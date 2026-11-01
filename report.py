"""Biriken sonuçlar: grup özeti, Excel/CSV yazımı, grafik ve istatistik (arayüzden bağımsız).

v2 masaüstü arayüzü kullanır; v1 Streamlit sürümündeki aynı işlevlerle eşdeğerdir.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from i18n import T

FRONT = ["Group", "Experiment", "Image", "Cell", "Area_unit", "Area", "Mean", "StdDev", "Min", "Max",
         "IntDen", "RawIntDen", "BG_Mean", "CTCF", "CTCF_per_Area"]
METRICS = {"CTCF": "CTCF (a.u.)", "CTCF_per_Area": "CTCF / Area (a.u./{unit})", "Mean": "Mean intensity",
           "IntDen": "Integrated density", "Area": "Area ({unit})"}
PLOT_KINDS = {"bar": "Bar (ortalama ± SEM) + noktalar", "box": "Box + noktalar", "violin": "Violin + noktalar"}


def ordered(results: pd.DataFrame) -> pd.DataFrame:
    front = [c for c in FRONT if c in results.columns]
    return results[front + [c for c in results.columns if c not in front]]


def add_image(results: pd.DataFrame, cells: pd.DataFrame, meta: dict) -> pd.DataFrame:
    """Bir görüntünün hücrelerini ekler; aynı görüntü önceden eklendiyse üzerine yazar."""
    add = cells.assign(**meta)
    if len(results) and "Image_path" in results:
        results = results[results["Image_path"] != meta["Image_path"]]
    return ordered(pd.concat([results, add], ignore_index=True)) if len(results) else ordered(add)


def add_background(bg_results: pd.DataFrame, bg: pd.DataFrame, image: str, image_path: str,
                   group: str) -> pd.DataFrame:
    add = bg.assign(Image=image, Image_path=image_path, Group=group)
    if len(bg_results):
        bg_results = bg_results[bg_results["Image_path"] != image_path]
        return pd.concat([bg_results, add], ignore_index=True)
    return add


def group_summary(results: pd.DataFrame, metric: str = "CTCF") -> pd.DataFrame:
    if not len(results):
        return pd.DataFrame()
    return (results.groupby("Group", sort=False)[metric]
            .agg(n="count", Mean="mean", SD="std", Median="median", Min="min", Max="max")
            .assign(SEM=lambda d: d["SD"] / np.sqrt(d["n"]))
            .reset_index())


def methods_table(version: str) -> pd.DataFrame:
    return pd.DataFrame({"Item": [
        "Software", "CTCF", "IntDen", "StdDev", "ROI rule", "Background", "Cell segmentation",
        "Nucleus segmentation", "Calibration", "Reference"],
        "Description": [
            f"ICC CTCF Ölçer {version} (Balcan, 2026; https://doi.org/10.5281/zenodo.23860020)",
            "CTCF = IntDen − (Area × Mean_background)",
            "IntDen = Area × Mean (calibrated units); RawIntDen = sum of pixel values (ImageJ definitions)",
            "Sample SD (n − 1), as in ImageJ",
            "A pixel belongs to an ROI if its centre lies inside it (ImageJ polygon rule)",
            "Mean of square cell-free boxes (size/number per image in Cells sheet: BG_box_px, BG_n, BG_mode)",
            "Li threshold on the measured channel; touching cells split by watershed seeded with DAPI nuclei",
            "DAPI Otsu mask split by watershed from smoothed-intensity maxima; each nucleus trimmed at half of "
            "its own peak intensity above background (v2 'local'; Nucleus_method column)",
            "Scale bar length detected automatically; its µm value read from the label (Scale_source column)",
            "McCloy et al., 2014, Cell Cycle 13(9):1400–1412, doi:10.4161/cc.28401"]})


def write_excel(path: str | Path, results: pd.DataFrame, bg_results: pd.DataFrame, version: str,
                validation: pd.DataFrame | None = None, excluded: pd.DataFrame | None = None):
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        ordered(results).to_excel(xw, sheet_name="Cells", index=False)
        group_summary(results).to_excel(xw, sheet_name="Group_summary", index=False)
        # GraphPad vb. için hazır: alan (görüntü) ve deney ortalamaları
        cols = [c for c in ("Group", "Experiment", "Image", "Image_path") if c in results]
        vals = [c for c in ("CTCF", "CTCF_per_Area", "Area", "Mean") if c in results]
        if "Image_path" in results and vals:
            (results.groupby(cols, sort=False, dropna=False)[vals]
             .mean().assign(n_cells=results.groupby(cols, sort=False, dropna=False).size())
             .reset_index().to_excel(xw, sheet_name="Image_means", index=False))
        if "Experiment" in results and results["Experiment"].notna().any():
            (results.groupby(["Group", "Experiment"], sort=False)[vals]
             .mean().assign(n_cells=results.groupby(["Group", "Experiment"], sort=False).size())
             .reset_index().to_excel(xw, sheet_name="Experiment_means", index=False))
        bg_results.to_excel(xw, sheet_name="Background", index=False)
        methods_table(version).to_excel(xw, sheet_name="Methods", index=False)
        if excluded is not None and len(excluded):  # dışlanan her hücre gerekçesiyle (QC otomatik / elle)
            front = [c for c in ("Group", "Experiment", "Image", "Cell", "Exclusion", "Reason") if c in excluded]
            excluded[front + [c for c in excluded.columns if c not in front]].to_excel(
                xw, sheet_name="Excluded_cells", index=False)
            (excluded.groupby(["Group", "Reason"]).size().rename("n").reset_index()
             .to_excel(xw, sheet_name="Exclusion_summary", index=False))
        if validation is not None and len(validation):  # elle (Fiji) vs otomatik — yöntem doğrulaması
            validation.to_excel(xw, sheet_name="Validation", index=False)
            pd.DataFrame([agreement(validation)]).to_excel(xw, sheet_name="Validation_summary", index=False)


def write_csv(path: str | Path, results: pd.DataFrame):
    ordered(results).to_csv(path, index=False, encoding="utf-8-sig")  # Excel Türkçe karakterleri doğru açsın


LEVELS = {"cell": "Hücre (her hücre bir değer)", "image": "Görüntü ortalaması (her alan bir değer)",
          "experiment": "Deney ortalaması (her bağımsız deney bir değer) — önerilen"}
COMPARISONS = {"dunnett": "Her grup kontrole karşı (Dunnett)", "tukey": "Tüm gruplar birbirine karşı (Tukey HSD)"}


def aggregate(results: pd.DataFrame, metric: str, level: str = "cell") -> pd.DataFrame:
    """İstatistik birimi: hücre / görüntü ortalaması / deney ortalaması → (Group, value, n_cells) tablosu."""
    if level == "cell":
        return results[["Group", metric]].rename(columns={metric: "value"}).assign(n_cells=1).dropna()
    key = {"image": "Image_path", "experiment": "Experiment"}[level]
    if key not in results or results[key].isna().all():
        raise ValueError(T("Deney sütunu yok") if level == "experiment" else T("Görüntü sütunu yok"))
    return (results.groupby(["Group", key], sort=False)[metric]
            .agg(value="mean", n_cells="count").reset_index())


def p_fmt(p: float) -> str:
    """p değeri metni; çok küçükse GraphPad gibi 'p < 0.0001' (Dunnett sayısal olarak 0 verebilir)."""
    return "p < 0.0001" if p < 1e-4 else f"p = {p:.4g}"


def p_stars(p: float) -> str:
    """GraphPad Prism gösterimi."""
    return "****" if p < 1e-4 else "***" if p < 1e-3 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"


def mixed_objectives(results: pd.DataFrame) -> str:
    """Farklı objektiflerle çekilmiş görüntüler karşılaştırılıyorsa uyarı metni (yoksa boş)."""
    if "Objective" not in results:
        return ""
    obj = results.dropna(subset=["Objective"]).groupby("Group")["Objective"].unique()
    allv = sorted({int(v) for vs in obj for v in vs})
    if len(allv) <= 1:
        return ""
    detail = "; ".join(f"{g}: {', '.join(f'{int(v)}×' for v in sorted(vs))}" for g, vs in obj.items())
    return (T("⚠️ Farklı objektifler karışık ({0}) — {1}. Büyütme farkı floresan yoğunluğunu ve alanı etkiler; yalnızca aynı objektifle çekilmiş görüntüleri karşılaştırın.").format(', '.join(f'{v}×' for v in allv), detail))


def mixed_exposures(results: pd.DataFrame) -> str:
    """Farklı pozlama süreleriyle çekilmiş görüntüler bir arada ise uyarı metni (yoksa boş). Floresan sinyali
    pozlamayla orantılı arttığı için bu görüntülerin CTCF değerleri karşılaştırılamaz (2026-11-01: samples
    klasöründe 0.33–1.0 s arası beş farklı pozlama)."""
    if "Exposure_s" not in results:
        return ""
    e = results.drop_duplicates("Image_path" if "Image_path" in results else "Image")["Exposure_s"].dropna()
    vals = sorted({round(float(v), 4) for v in e})
    if len(vals) <= 1:
        return ""
    return T("⚠️ Görüntüler farklı pozlama süreleriyle çekilmiş ({0}). Floresan sinyali pozlamayla orantılı arttığı "
             "için bu görüntülerin CTCF değerleri birbiriyle karşılaştırılamaz; aynı pozlama, kazanç ve lamba "
             "ayarıyla çekilmiş görüntüleri karşılaştırın.").format(", ".join(f"{v:g} s" for v in vals))


def compare(results: pd.DataFrame, metric: str = "CTCF", level: str = "cell", control: str | None = None,
            order: list[str] | None = None, comparison: str = "dunnett"):
    """Gruplar arası test. → (groups, data, txt, pairs) ; pairs = [(i, j, p)] grafikte yıldız için."""
    import warnings
    from scipy import stats as sps
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="scipy")  # sıfır varyans → yukarıda uyarı
    agg = aggregate(results, metric, level)
    groups = [g for g in (order or list(dict.fromkeys(agg["Group"]))) if g in set(agg["Group"])]
    if control in groups:
        groups.remove(control)
        groups.insert(0, control)
    data = [agg.loc[agg["Group"] == g, "value"].to_numpy(float) for g in groups]
    unit = {"cell": T("hücre"), "image": T("görüntü"), "experiment": T("deney")}[level]
    lines = ["n (" + unit + "): " + ", ".join(f"{g} = {len(d)}" for g, d in zip(groups, data))]
    pairs = []
    flat = [g for g, d in zip(groups, data) if len(d) > 1 and np.ptp(d) == 0]
    if flat:
        lines.append(T("⚠️ Grup içi değişkenlik sıfır ({0}): aynı değerler tekrar ediyor (aynı görüntü iki kez mi eklendi?). Test sonucu güvenilmez.").format(', '.join(flat)))
    if len(groups) < 2:
        lines.append(T("İstatistik için en az iki grup gerekir."))
    elif any(len(d) < 2 for d in data) or (level == "cell" and any(len(d) < 3 for d in data)):
        lines.append(T("İstatistik için her grupta en az {0} {1} gerekir.").format(3 if level == 'cell' else 2, unit))
    elif len(groups) == 2:
        t = sps.ttest_ind(*data, equal_var=False)
        u = sps.mannwhitneyu(*data)
        lines += [T("Welch t-testi: {0} ({1})").format(p_fmt(t.pvalue), p_stars(t.pvalue)),
                  T("Mann–Whitney U: {0} ({1})").format(p_fmt(u.pvalue), p_stars(u.pvalue))]
        pairs = [(0, 1, t.pvalue)]
    else:
        a, k = sps.f_oneway(*data), sps.kruskal(*data)
        lines += [T("Tek yönlü ANOVA: {0} ({1})").format(p_fmt(a.pvalue), p_stars(a.pvalue)),
                  T("Kruskal–Wallis: {0} ({1})").format(p_fmt(k.pvalue), p_stars(k.pvalue)), ""]
        if comparison == "dunnett":
            d = sps.dunnett(*data[1:], control=data[0], random_state=0)  # sabit tohum → tekrarlanabilir p
            lines.append(T("Dunnett (kontrol = {0}):").format(groups[0]))
            for j, pv in enumerate(d.pvalue, 1):
                lines.append(f"  {groups[j]} vs {groups[0]}: {p_fmt(pv)} ({p_stars(pv)})")
                pairs.append((0, j, pv))
        else:
            tk = sps.tukey_hsd(*data)
            lines.append(T("Tukey HSD (tüm çiftler):"))
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    lines.append(f"  {groups[i]} vs {groups[j]}: {p_fmt(tk.pvalue[i, j])} "
                                 f"({p_stars(tk.pvalue[i, j])})")
                    pairs.append((i, j, tk.pvalue[i, j]))
    if level != "cell" and len(data) and min(len(d) for d in data) < 3:
        lines += ["", T("ℹ️ Grup başına {0} {1}: test gücü düşük; en az 3 bağımsız deney önerilir.").format(min(len(d) for d in data), unit)]
    if level == "cell":
        lines += ["", T("⚠️ Her hücre ayrı tekrar sayıldı (yalancı tekrar riski). Yayın için 'Deney ortalaması' düzeyini kullanın.")]
    for warn in (mixed_objectives(results), mixed_exposures(results)):
        if warn:
            lines += ["", warn]
    return groups, data, "\n".join(lines), pairs


def plot(results: pd.DataFrame, metric: str = "CTCF", kind: str = "bar", normalize: bool = False,
         fig=None, level: str = "cell", control: str | None = None, order: list[str] | None = None,
         comparison: str = "dunnett", stars: bool = True):
    """Grup grafiği + istatistik metni. fig verilirse onun üzerine çizer (Qt tuvali için).
    Normalize: kontrol grubu ortalaması = 1."""
    import matplotlib
    own = fig is None
    if own:
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig = plt.figure(dpi=150)
    try:
        groups, data, txt, pairs = compare(results, metric, level, control, order, comparison)
    except ValueError as ex:
        fig.clear()
        return fig, T("{0}: bu düzey için tabloda 'Experiment' (deney) bilgisi gerekli.").format(ex)
    if normalize and len(data) and len(data[0]) and data[0].mean() != 0:
        ref = data[0].mean()
        data = [d / ref for d in data]
    fig.clear()
    if own:  # Qt tuvalinin boyutunu pencere belirler; değiştirmek eski çizimi ekranda bırakıyordu
        fig.set_size_inches(max(3.5, 1.3 * len(groups) + 1.5), 4)
    ax = fig.add_subplot(111)
    x = np.arange(len(groups))
    if kind == "bar":
        ax.bar(x, [d.mean() if len(d) else 0 for d in data],
               yerr=[d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else 0 for d in data],
               capsize=4, color=["#bdbdbd"] + ["#7fbf7f"] * (len(groups) - 1), edgecolor="black", width=0.6)
    elif kind == "box":
        ax.boxplot(data, positions=x, widths=0.5, showfliers=False)
    else:
        ok = [i for i, d in enumerate(data) if len(d) > 1]
        if ok:
            ax.violinplot([data[i] for i in ok], positions=x[ok], showmedians=True)
    rng = np.random.default_rng(0)
    for i, d in enumerate(data):
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(d)), d, s=14 if level == "cell" else 30,
                   color="black", alpha=0.7, zorder=3)
    if stars and pairs:
        top = max((d.max() for d in data if len(d)), default=1)
        step = 0.08 * (top if top else 1)
        y = top + step
        for i, j, pv in pairs:
            if len(pairs) > 1 and pairs[0][0] == 0 and all(pp[0] == 0 for pp in pairs):
                ax.text(j, max(data[j].max(), 0) + step * 0.6, p_stars(pv), ha="center", va="bottom", fontsize=11)
            else:
                ax.plot([i, i, j, j], [y, y + step * 0.3, y + step * 0.3, y], color="black", lw=1)
                ax.text((i + j) / 2, y + step * 0.35, p_stars(pv), ha="center", va="bottom", fontsize=11)
                y += step * 1.2
        ax.set_ylim(top=y + step)
    rot = len(groups) > 3
    ax.set_xticks(x, groups, rotation=30 if rot else 0, ha="right" if rot else "center")
    unit = results["Area_unit"].iloc[0] if "Area_unit" in results else ""
    ax.set_ylabel(("Relative " if normalize else "") + METRICS[metric].format(unit=unit))
    ax.spines[["top", "right"]].set_visible(False)
    if fig.get_layout_engine() is None:
        fig.tight_layout()
    return fig, txt


# ------------------------------------------------- Yöntem doğrulaması (elle vs otomatik)
def agreement(val: pd.DataFrame, metric: str = "CTCF") -> dict:
    """Elle (Fiji'de çizilmiş) ve otomatik ölçüm uyumu: Bland–Altman yanlılığı ve %95 uyum sınırları
    (yüzde fark olarak; CTCF değerleri hücreden hücreye çok değiştiği için), Pearson r, Lin CCC, Dice."""
    d = val.dropna(subset=[f"Manual_{metric}", f"Auto_{metric}"])
    m, a = d[f"Manual_{metric}"].to_numpy(float), d[f"Auto_{metric}"].to_numpy(float)
    if len(d) < 2:
        return {"n": len(d)}
    mean = (m + a) / 2
    pdiff = 100 * (a - m) / mean
    bias, sd = pdiff.mean(), pdiff.std(ddof=1)
    r = np.corrcoef(m, a)[0, 1]
    ccc = 2 * np.cov(m, a, ddof=1)[0, 1] / (m.var(ddof=1) + a.var(ddof=1) + (m.mean() - a.mean()) ** 2)
    return {"n": len(d), "n_images": d["Image"].nunique() if "Image" in d else np.nan,
            "bias_%": bias, "sd_%": sd, "loa_low_%": bias - 1.96 * sd, "loa_high_%": bias + 1.96 * sd,
            "pearson_r": r, "lin_ccc": ccc,
            "dice_mean": d["Dice"].mean() if "Dice" in d else np.nan,
            "dice_min": d["Dice"].min() if "Dice" in d else np.nan}


def agreement_text(st: dict, metric: str = "CTCF") -> str:
    if st.get("n", 0) < 2:
        return T("Bland–Altman için en az 2 eşleşmiş hücre gerekir (yayın için ≥ 30 hücre, ≥ 3 görüntü önerilir).")
    return (T("n = {0} hücre, {1} görüntü\n{2}: ortalama fark (otomatik − elle) = {3:+.1f} %\n%95 uyum sınırları: {4:+.1f} % … {5:+.1f} %\nPearson r = {6:.3f} · Lin CCC = {7:.3f}\nDice (sınır örtüşmesi): ortalama {8:.3f}, en düşük {9:.3f}").format(st['n'], st['n_images'], metric, st['bias_%'], st['loa_low_%'], st['loa_high_%'], st['pearson_r'], st['lin_ccc'], st['dice_mean'], st['dice_min'])
            + (T("\n\n⚠️ Az hücre: r ve CCC bu kadar küçük örneklemde anlamsızdır. Yayın için ≥ 30 hücre, ≥ 3 görüntü (ayrık ve değen hücreler) önerilir.") if st["n"] < 30 else ""))


def bland_altman_plot(val: pd.DataFrame, metric: str = "CTCF", fig=None):
    import matplotlib
    own = fig is None
    if own:
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(9, 4), dpi=150)
    fig.clear()
    d = val.dropna(subset=[f"Manual_{metric}", f"Auto_{metric}"])
    st = agreement(val, metric)
    ax1, ax2 = fig.subplots(1, 2)
    if len(d) >= 2:
        m, a = d[f"Manual_{metric}"].to_numpy(float), d[f"Auto_{metric}"].to_numpy(float)
        lim = [0, max(m.max(), a.max()) * 1.05]
        ax1.scatter(m, a, s=18, color="black", alpha=0.7)
        ax1.plot(lim, lim, "--", color="grey", lw=1)
        ax1.set_xlim(lim); ax1.set_ylim(lim)
        ax1.set_xlabel(f"Manual {metric} (Fiji)"); ax1.set_ylabel(f"Automatic {metric}")
        ax1.set_title(f"r = {st['pearson_r']:.3f}, CCC = {st['lin_ccc']:.3f}", fontsize=9)
        mean = (m + a) / 2
        pd_ = 100 * (a - m) / mean
        ax2.scatter(mean, pd_, s=18, color="black", alpha=0.7)
        for y, ls in ((st["bias_%"], "-"), (st["loa_low_%"], "--"), (st["loa_high_%"], "--")):
            ax2.axhline(y, color="#c33" if ls == "-" else "grey", ls=ls, lw=1)
        ax2.axhline(0, color="black", lw=0.5)
        ax2.set_xlabel(f"Mean of methods ({metric})"); ax2.set_ylabel("Difference, auto − manual (%)")
        ax2.set_title(f"bias {st['bias_%']:+.1f} %, LoA {st['loa_low_%']:+.1f} … {st['loa_high_%']:+.1f} %",
                      fontsize=9)
    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
    if fig.get_layout_engine() is None:
        fig.tight_layout()
    return fig, agreement_text(st, metric)
