"""Biriken sonuçlar: grup özeti, Excel/CSV yazımı, grafik ve istatistik (arayüzden bağımsız).

v2 masaüstü arayüzü kullanır; v1 Streamlit sürümündeki aynı işlevlerle eşdeğerdir.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FRONT = ["Group", "Image", "Cell", "Area_unit", "Area", "Mean", "StdDev", "Min", "Max",
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
            "Bright nuclear body (upper threshold of 3-class Otsu) split by smoothed DAPI intensity maxima (v2)",
            "Scale bar length detected automatically; its µm value read from the label (Scale_source column)",
            "McCloy et al., 2014, Cell Cycle 13(9):1400–1412, doi:10.4161/cc.28401"]})


def write_excel(path: str | Path, results: pd.DataFrame, bg_results: pd.DataFrame, version: str):
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        ordered(results).to_excel(xw, sheet_name="Cells", index=False)
        group_summary(results).to_excel(xw, sheet_name="Group_summary", index=False)
        bg_results.to_excel(xw, sheet_name="Background", index=False)
        methods_table(version).to_excel(xw, sheet_name="Methods", index=False)


def write_csv(path: str | Path, results: pd.DataFrame):
    ordered(results).to_csv(path, index=False, encoding="utf-8-sig")  # Excel Türkçe karakterleri doğru açsın


def plot(results: pd.DataFrame, metric: str = "CTCF", kind: str = PLOT_KINDS[0], normalize: bool = False,
         fig=None):
    """Grup grafiği + istatistik metni. fig verilirse onun üzerine çizer (Qt tuvali için)."""
    from scipy import stats as sps
    import matplotlib
    if fig is None:
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig = plt.figure(dpi=150)
    groups = list(dict.fromkeys(results["Group"]))
    data = [results.loc[results["Group"] == g, metric].dropna().to_numpy(float) for g in groups]
    if normalize and len(data[0]) and data[0].mean() != 0:
        ref = data[0].mean()
        data = [d / ref for d in data]
    fig.clear()
    fig.set_size_inches(max(3.5, 1.3 * len(groups) + 1.5), 4)
    ax = fig.add_subplot(111)
    x = np.arange(len(groups))
    if kind == PLOT_KINDS[0]:
        ax.bar(x, [d.mean() if len(d) else 0 for d in data],
               yerr=[d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else 0 for d in data],
               capsize=4, color="#7fbf7f", edgecolor="black", width=0.6)
    elif kind == PLOT_KINDS[1]:
        ax.boxplot(data, positions=x, widths=0.5, showfliers=False)
    else:
        ok = [i for i, d in enumerate(data) if len(d) > 1]
        if ok:
            ax.violinplot([data[i] for i in ok], positions=x[ok], showmedians=True)
    rng = np.random.default_rng(0)
    for i, d in enumerate(data):
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(d)), d, s=12, color="black", alpha=0.7, zorder=3)
    rot = len(groups) > 3
    ax.set_xticks(x, groups, rotation=30 if rot else 0, ha="right" if rot else "center")
    unit = results["Area_unit"].iloc[0] if "Area_unit" in results else ""
    ax.set_ylabel(("Relative " if normalize else "") + METRICS[metric].format(unit=unit))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()

    txt = ""
    if len(groups) == 2 and all(len(d) >= 3 for d in data):
        t = sps.ttest_ind(*data, equal_var=False)
        u = sps.mannwhitneyu(*data)
        txt = f"Welch t-test p = {t.pvalue:.4g}\nMann–Whitney U p = {u.pvalue:.4g}"
    elif len(groups) > 2 and all(len(d) >= 3 for d in data):
        txt = (f"One-way ANOVA p = {sps.f_oneway(*data).pvalue:.4g}\n"
               f"Kruskal–Wallis p = {sps.kruskal(*data).pvalue:.4g}\n\nTukey HSD:")
        tk = sps.tukey_hsd(*data)
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                txt += f"\n  {groups[i]} vs {groups[j]}: p = {tk.pvalue[i, j]:.4g}"
    elif len(groups) < 2:
        txt = "İstatistik için en az iki grup gerekir."
    else:
        txt = "İstatistik için her grupta en az 3 hücre gerekir."
    return fig, txt
