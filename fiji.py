"""Fiji köprüsü: aynı ROI'leri Fiji'nin kendi ölçüm motoruyla (ij.plugin.filter.Analyzer = Measure
komutu) arka planda ölçtürür ya da Fiji'yi görüntü + ROI'lerle açar (arayüzden bağımsız).
"""
from __future__ import annotations

import io
import os
import platform
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

import core
from i18n import T

# Fiji'nin Measure komutuyla aynı ölçüm (RoiManager GUI gerektirdiği için Analyzer doğrudan çağrılır)
MEASURE_GROOVY = r'''#@ String tif
#@ String rois
#@ double umPerPx
#@ String out
#@ String nucLabels
#@ String cytoLabels
import ij.IJ
import ij.plugin.filter.ThresholdToSelection
import ij.process.ImageProcessor
import ij.io.RoiDecoder
import ij.measure.Measurements
import ij.measure.ResultsTable
import ij.plugin.filter.Analyzer
import java.util.zip.ZipFile

def imp = IJ.openImage(tif)
def cal = imp.getCalibration()
if (umPerPx > 0) { cal.pixelWidth = umPerPx; cal.pixelHeight = umPerPx; cal.setUnit("µm") }
int m = Measurements.AREA | Measurements.MEAN | Measurements.STD_DEV | Measurements.MIN_MAX | Measurements.INTEGRATED_DENSITY
def rt = new ResultsTable()
def zf = new ZipFile(rois)
zf.entries().each { e ->
    def roi = RoiDecoder.openFromByteArray(zf.getInputStream(e).bytes)
    imp.setRoi(roi)
    new Analyzer(imp, m, rt).measure()
    rt.setLabel(roi.getName() ?: e.getName(), rt.size() - 1)
}
// Çekirdek / sitoplazma: etiket görüntüsünden Fiji'nin kendi seçimi (Threshold → Create Selection), aynı Measure
[["Nuc", nucLabels], ["Cyto", cytoLabels]].each { pair ->
    if (!pair[1]) return
    def lab = IJ.openImage(pair[1])
    def lp = lab.getProcessor()
    def ids = new TreeSet()
    for (int i = 0; i < lp.getPixelCount(); i++) { int v = (int) lp.getf(i); if (v > 0) ids.add(v) }
    ids.each { id ->
        lp.setThreshold(id, id, ImageProcessor.NO_LUT_UPDATE)
        def roi = ThresholdToSelection.run(lab)
        if (roi == null) return
        imp.setRoi(roi)
        new Analyzer(imp, m, rt).measure()
        rt.setLabel(pair[0] + "_" + id, rt.size() - 1)
    }
}
rt.setPrecision(6)
rt.save(out)
println("FIJI_OK " + rt.size() + " " + IJ.getFullVersion())
'''

OPEN_MACRO = '''open("{tif}");
run("Set Scale...", "distance={px} known={um:g} unit=µm");
run("Set Measurements...", "area mean standard min integrated redirect=None decimal=3");
roiManager("reset");
roiManager("Open", "{rois}");
roiManager("Show All with labels");
roiManager("Deselect");
roiManager("Measure");
'''


def candidates() -> list[Path]:
    home = Path.home()
    sysname = platform.system()
    if sysname == "Darwin":
        roots = [home / "Downloads" / "Fiji", Path("/Applications/Fiji"), home / "Applications" / "Fiji",
                 home / "Fiji", Path("/Applications/Fiji.app"), home / "Applications" / "Fiji.app",
                 home / "Downloads" / "Fiji.app"]
        names = ["fiji", "Contents/MacOS/ImageJ-macosx", "Contents/MacOS/fiji-macos"]
    elif sysname == "Windows":
        roots = [home / "Fiji", home / "Fiji.app", home / "Downloads" / "Fiji", home / "Downloads" / "Fiji.app",
                 home / "Desktop" / "Fiji", home / "Desktop" / "Fiji.app", Path("C:/Fiji"), Path("C:/Fiji.app"),
                 Path("C:/Program Files/Fiji"), Path("C:/Program Files/Fiji.app")]
        names = ["fiji-windows-x64.exe", "ImageJ-win64.exe", "fiji.bat"]
    else:
        roots = [home / "Fiji", home / "Fiji.app", home / "Downloads" / "Fiji", home / "Downloads" / "Fiji.app",
                 home / "Applications" / "Fiji", home / "Applications" / "Fiji.app",
                 Path("/opt/Fiji"), Path("/opt/Fiji.app"), Path("/usr/local/Fiji"), Path("/usr/local/Fiji.app")]
        names = ["fiji", "fiji-linux-x64", "fiji-linux-arm64", "ImageJ-linux64"]
    return [r / n for r in roots for n in names]


def find_fiji(saved: str | None = None) -> Path | None:
    """Kayıtlı yol geçerliyse onu, değilse bilinen kurulum yerlerini dener."""
    for p in ([Path(saved)] if saved else []) + candidates():
        if p.is_file() and (os.access(p, os.X_OK) or p.suffix.lower() in (".exe", ".bat")):
            return p
    return None


def resolve(path: str | Path) -> Path | None:
    """Kullanıcının seçtiği klasör/uygulamadan çalıştırılabilir Fiji'yi bulur."""
    p = Path(path)
    if p.is_file():
        return p
    for n in ("fiji", "fiji-windows-x64.exe", "ImageJ-win64.exe", "fiji.bat", "Contents/MacOS/ImageJ-macosx",
              "Contents/MacOS/fiji-macos", "fiji-linux-x64", "fiji-linux-arm64", "ImageJ-linux64"):
        if (p / n).is_file():
            return p / n
    if p.name == "Fiji.app" and (p.parent / "fiji").is_file():  # yeni düzen: Fiji/Fiji.app + Fiji/fiji
        return p.parent / "fiji"
    return None


def write_package(folder: Path, a: core.Analysis, cell_ids, boxes, base: str,
                  margin_um: float = core.Settings.nc_margin_um) -> tuple[Path, Path]:
    """Ölçülen kanal (TIFF) + ROI'ler (RoiSet.zip) → klasöre; DAPI varsa çekirdek/sitoplazma etiket görüntüleri de
    (<base>_nucleus_labels.tif, <base>_cytoplasm_labels.tif). → (tif, roiset)."""
    folder.mkdir(parents=True, exist_ok=True)
    data = core.imagej_export_zip(a.fitc_ch, a.labels, cell_ids, boxes, base, (a.scale_bar.bar_px, a.bar_um))
    zipfile.ZipFile(io.BytesIO(data)).extractall(folder)
    tif = folder / f"{base}_measured_channel.tif"
    if a.nuclei is not None and a.nuclei.any():  # çekirdek/sitoplazma bölmeleri (N/C doğrulaması)
        import tifffile
        nuc, cyto = core.compartment_label_images(a.labels, a.nuclei, cell_ids, a.um_per_px, margin_um)
        tifffile.imwrite(compartment_paths(tif)[0], nuc, imagej=True)
        tifffile.imwrite(compartment_paths(tif)[1], cyto, imagej=True)
    return tif, folder / f"{base}_RoiSet.zip"


def compartment_paths(tif: Path) -> tuple[Path, Path]:
    stem = tif.name.removesuffix("_measured_channel.tif")
    return tif.with_name(f"{stem}_nucleus_labels.tif"), tif.with_name(f"{stem}_cytoplasm_labels.tif")


def _run(fiji: Path, args: list[str], timeout: int):
    kw = {"capture_output": True, "text": True, "timeout": timeout}
    if sys.platform == "win32":
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    return subprocess.run([str(fiji), *args], **kw)


def measure_in_fiji(fiji: Path, tif: Path, rois: Path, um_per_px: float | None, timeout: int = 180) -> tuple[pd.DataFrame, str]:
    """Fiji'yi arka planda (headless) çalıştırır; Results tablosu ve Fiji sürümü döner."""
    with tempfile.TemporaryDirectory() as d:
        script = Path(d) / "ctcf_measure.groovy"
        script.write_text(MEASURE_GROOVY, encoding="utf-8")
        out = Path(d) / "fiji_results.csv"
        nuc, cyto = (p.as_posix() if p.exists() else "" for p in compartment_paths(tif))
        arg = (f'tif="{tif.as_posix()}",rois="{rois.as_posix()}",umPerPx={um_per_px or 0},out="{out.as_posix()}",'
               f'nucLabels="{nuc}",cytoLabels="{cyto}"')
        r = _run(fiji, ["--headless", "--run", str(script), arg], timeout)
        ok = [ln for ln in r.stdout.splitlines() if ln.startswith("FIJI_OK")]
        if not out.exists() or not ok:
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-8:])
            raise RuntimeError(T("Fiji ölçümü başarısız (çıkış kodu {0}).\n{1}").format(r.returncode, tail))
        df = pd.read_csv(out)
    df = df.drop(columns=[c for c in df.columns if not c.strip() or c.startswith("Unnamed")], errors="ignore")
    return df, ok[0].split(" ", 2)[2]


def compare(app_cells: pd.DataFrame, app_bg: pd.DataFrame, fiji_df: pd.DataFrame) -> pd.DataFrame:
    """Program ve Fiji değerlerini yan yana koyar. Hücreler 'Cell_n', kutular 'BG_n', çekirdek/sitoplazma bölmeleri
    'Nuc_n' / 'Cyto_n' etiketiyle eşlenir. Bölmelerde Area, Mean, IntDen karşılaştırılır; ayrıca N/C oranı Fiji'nin
    kendi ölçtüğü değerlerden (Fiji'nin BG kutuları ortalamasıyla) yeniden hesaplanır."""
    cols = ["Area", "Mean", "StdDev", "Min", "Max", "IntDen", "RawIntDen"]
    parts = [app_cells.assign(Label="Cell_" + app_cells["Cell"].astype(int).astype(str)),
             app_bg.assign(Label="BG_" + app_bg["BG"].astype(int).astype(str))]
    if "Nuc_Mean" in app_cells:
        for k in ("Nuc", "Cyto"):
            c = app_cells.dropna(subset=[f"{k}_Mean"])
            parts.append(pd.DataFrame({"Label": f"{k}_" + c["Cell"].astype(int).astype(str), "Area": c[f"{k}_Area"],
                                       "Mean": c[f"{k}_Mean"], "IntDen": c[f"{k}_Area"] * c[f"{k}_Mean"]}))
    app = pd.concat(parts, ignore_index=True).reindex(columns=["Label"] + cols + ["NC_ratio"])
    m = app[["Label"] + cols].merge(fiji_df[["Label"] + cols], on="Label", suffixes=("_app", "_fiji"), how="outer")
    # N/C: Fiji'nin ölçtüğü çekirdek/sitoplazma ortalamaları ve Fiji'nin BG kutuları → oran
    fm = fiji_df.set_index("Label")["Mean"]
    bg_f = fm[fm.index.str.startswith("BG_")].mean()
    nc_app = dict(zip("Nuc_" + app_cells["Cell"].astype(int).astype(str), app_cells.get("NC_ratio", pd.Series(dtype=float))))
    rows = []
    for _, r in m.iterrows():
        row = {"ROI": r["Label"]}
        for c in cols:
            row[f"{c} (app)"] = r[f"{c}_app"]
            row[f"{c} (Fiji)"] = r[f"{c}_fiji"]
        pairs = [(r[f"{c}_app"], r[f"{c}_fiji"]) for c in cols]
        if str(r["Label"]).startswith("Nuc_") and pd.notna(nc_app.get(r["Label"])):
            cid = r["Label"][4:]
            nc_f = (fm.get(f"Nuc_{cid}", np.nan) - bg_f) / (fm.get(f"Cyto_{cid}", np.nan) - bg_f)
            row["NC_ratio (app)"], row["NC_ratio (Fiji)"] = nc_app[r["Label"]], nc_f
            pairs.append((nc_app[r["Label"]], nc_f))
        row["Max diff (%)"] = max((abs(x - y) / max(abs(y), 1e-9) * 100 for x, y in pairs
                                   if pd.notna(x) and pd.notna(y)), default=np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def unmatched(cmp: pd.DataFrame) -> int:
    """Programda olup Fiji'de olmayan (ya da tersi) ROI sayısı (Area her iki tarafta da olmalı)."""
    return int((cmp["Area (app)"].isna() | cmp["Area (Fiji)"].isna()).sum())


def open_in_fiji(fiji: Path, tif: Path, rois: Path, bar_px: int | None, bar_um: float) -> subprocess.Popen:
    """Fiji'yi arayüzüyle açar: görüntü + ölçek + ROI Manager'da ROI'ler + Measure (Results penceresi)."""
    macro = tif.parent / "ctcf_open_in_fiji.ijm"
    macro.write_text(OPEN_MACRO.format(tif=tif.as_posix(), rois=rois.as_posix(), px=bar_px or 1,
                                       um=bar_um if bar_px else 1), encoding="utf-8")
    kw = {}
    if sys.platform == "win32":
        kw["creationflags"] = 0x00000008  # DETACHED_PROCESS
    return subprocess.Popen([str(fiji), "-macro", str(macro)], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, **kw)
