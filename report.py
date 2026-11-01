"""Biriken sonuçlar: grup özeti, Excel/CSV yazımı, grafik ve istatistik (arayüzden bağımsız).

v2 masaüstü arayüzü kullanır; v1 Streamlit sürümündeki aynı işlevlerle eşdeğerdir.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FRONT = ["Group", "Experiment", "Image", "Cell", "Area_unit", "Area", "Mean", "StdDev", "Min", "Max",
         "IntDen", "RawIntDen", "BG_Mean", "CTCF", "CTCF_per_Area"]
METRICS = {"CTCF": "CTCF (a.u.)", "CTCF_per_Area": "CTCF / Area (a.u./{unit})", "Mean": "Mean intensity",
           "IntDen": "Integrated density", "Area": "Area ({unit})"}
PLOT_KINDS = ("Bar (ortalama ± SEM) + noktalar", "Box + noktalar", "Violin + noktalar")


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
            f"ICC CTCF Ölçer {version}",
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


def write_excel(path: str | Path, results: pd.DataFrame, bg_results: pd.DataFrame, version: str):
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
        raise ValueError("Deney sütunu yok" if level == "experiment" else "Görüntü sütunu yok")
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
    return (f"⚠️ Farklı objektifler karışık ({', '.join(f'{v}×' for v in allv)}) — {detail}. "
            "Büyütme farkı floresan yoğunluğunu ve alanı etkiler; yalnızca aynı objektifle çekilmiş "
            "görüntüleri karşılaştırın.")


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
    unit = {"cell": "hücre", "image": "görüntü", "experiment": "deney"}[level]
    lines = ["n (" + unit + "): " + ", ".join(f"{g} = {len(d)}" for g, d in zip(groups, data))]
    pairs = []
    flat = [g for g, d in zip(groups, data) if len(d) > 1 and np.ptp(d) == 0]
    if flat:
        lines.append(f"⚠️ Grup içi değişkenlik sıfır ({', '.join(flat)}): aynı değerler tekrar ediyor (aynı "
                     "görüntü iki kez mi eklendi?). Test sonucu güvenilmez.")
    if len(groups) < 2:
        lines.append("İstatistik için en az iki grup gerekir.")
    elif any(len(d) < 2 for d in data) or (level == "cell" and any(len(d) < 3 for d in data)):
        lines.append(f"İstatistik için her grupta en az {3 if level == 'cell' else 2} {unit} gerekir.")
    elif len(groups) == 2:
        t = sps.ttest_ind(*data, equal_var=False)
        u = sps.mannwhitneyu(*data)
        lines += [f"Welch t-testi: {p_fmt(t.pvalue)} ({p_stars(t.pvalue)})",
                  f"Mann–Whitney U: {p_fmt(u.pvalue)} ({p_stars(u.pvalue)})"]
        pairs = [(0, 1, t.pvalue)]
    else:
        a, k = sps.f_oneway(*data), sps.kruskal(*data)
        lines += [f"Tek yönlü ANOVA: {p_fmt(a.pvalue)} ({p_stars(a.pvalue)})",
                  f"Kruskal–Wallis: {p_fmt(k.pvalue)} ({p_stars(k.pvalue)})", ""]
        if comparison == "dunnett":
            d = sps.dunnett(*data[1:], control=data[0], random_state=0)  # sabit tohum → tekrarlanabilir p
            lines.append(f"Dunnett (kontrol = {groups[0]}):")
            for j, pv in enumerate(d.pvalue, 1):
                lines.append(f"  {groups[j]} vs {groups[0]}: {p_fmt(pv)} ({p_stars(pv)})")
                pairs.append((0, j, pv))
        else:
            tk = sps.tukey_hsd(*data)
            lines.append("Tukey HSD (tüm çiftler):")
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    lines.append(f"  {groups[i]} vs {groups[j]}: {p_fmt(tk.pvalue[i, j])} "
                                 f"({p_stars(tk.pvalue[i, j])})")
                    pairs.append((i, j, tk.pvalue[i, j]))
    if level != "cell" and len(data) and min(len(d) for d in data) < 3:
        lines += ["", f"ℹ️ Grup başına {min(len(d) for d in data)} {unit}: test gücü düşük; en az 3 bağımsız "
                  "deney önerilir."]
    if level == "cell":
        lines += ["", "⚠️ Her hücre ayrı tekrar sayıldı (yalancı tekrar riski). Yayın için 'Deney ortalaması' "
                  "düzeyini kullanın."]
    warn = mixed_objectives(results)
    if warn:
        lines += ["", warn]
    return groups, data, "\n".join(lines), pairs


def plot(results: pd.DataFrame, metric: str = "CTCF", kind: str = PLOT_KINDS[0], normalize: bool = False,
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
        return fig, f"{ex}: bu düzey için tabloda 'Experiment' (deney) bilgisi gerekli."
    if normalize and len(data) and len(data[0]) and data[0].mean() != 0:
        ref = data[0].mean()
        data = [d / ref for d in data]
    fig.clear()
    if own:  # Qt tuvalinin boyutunu pencere belirler; değiştirmek eski çizimi ekranda bırakıyordu
        fig.set_size_inches(max(3.5, 1.3 * len(groups) + 1.5), 4)
    ax = fig.add_subplot(111)
    x = np.arange(len(groups))
    if kind == PLOT_KINDS[0]:
        ax.bar(x, [d.mean() if len(d) else 0 for d in data],
               yerr=[d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else 0 for d in data],
               capsize=4, color=["#bdbdbd"] + ["#7fbf7f"] * (len(groups) - 1), edgecolor="black", width=0.6)
    elif kind == PLOT_KINDS[1]:
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
