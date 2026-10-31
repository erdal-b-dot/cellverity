"""Doğrulama testi: Image_392 (FITC) + Image_393 (DAPI) için Fiji ile doğrulanmış değerler.

Arayüz değişse de hesaplamaların aynı kaldığını kontrol eder.
Çalıştırma:  .venv/bin/python tests/test_core.py
Örnek görüntüler repoda yok (yayımlanmamış veri); ornek/ klasörüne kopyalanmalıdır.
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import core  # noqa: E402

FITC = ROOT / "ornek" / "Image_392.jpg"
DAPI = ROOT / "ornek" / "Image_393.jpg"

# (Area µm², Mean, IntDen) — 2026-10-31, DAPI modu, varsayılan ayarlar
EXPECTED = [(498.26, 146.71, 73097.7), (475.80, 139.17, 66216.8)]


def run_default_pipeline():
    fitc_arr, meta = core.load_image(open(FITC, "rb"))
    dapi_arr = core.load_image(open(DAPI, "rb"))[0]
    sb = core.detect_scale_bar(fitc_arr)
    upp = 20.0 / sb.bar_px
    exclude = np.zeros(fitc_arr.shape[:2], bool)
    if sb.found:
        y0, y1, x0, x1 = sb.bbox
        exclude[y0:y1, x0:x1] = True
    fitc_ch = core.get_channel(fitc_arr, "G")
    dapi_ch = core.get_channel(dapi_arr, "B")
    nuclei = core.segment_nuclei(dapi_ch, upp, exclude, 15.0, 10.0, split=True)
    labels, th = core.segment_cells(fitc_ch, upp, exclude, nuclei, "Li", 1.0, 50.0)
    boxes = core.auto_background_boxes(fitc_ch, labels > 0, exclude, 50, 3, signal_thresh=th * 0.3)
    bg = core.measure_backgrounds(fitc_ch, boxes, upp ** 2, meta["max_value"])
    ids = [int(i) for i in np.setdiff1d(np.unique(labels), [0])]
    cells = core.measure_cells(fitc_ch, labels, ids, float(bg["Mean"].mean()), upp,
                               meta["max_value"], nuclei)
    return sb, upp, cells, bg


def test_analyze_matches_manual_pipeline():
    """core.analyze() (masaüstü sürümün kullandığı akış) adım adım akışla birebir aynı olmalı."""
    sb, upp, cells_ref, bg_ref = run_default_pipeline()
    fitc_arr, meta = core.load_image(open(FITC, "rb"))
    a = core.analyze(fitc_arr, meta, core.load_image(open(DAPI, "rb"))[0], core.Settings(nuc_bright_core=False))
    assert a.um_per_px == upp and a.segmentation_mode == "DAPI nuclei"
    assert a.objective[0] == 40
    cells, bg, _ = core.background_and_measure(a, a.cell_ids)
    assert np.array_equal(cells[["Area", "Mean", "IntDen", "CTCF"]].to_numpy(),
                          cells_ref[["Area", "Mean", "IntDen", "CTCF"]].to_numpy())
    assert np.array_equal(bg["Mean"].to_numpy(), bg_ref["Mean"].to_numpy())


def test_image_392():
    sb, upp, cells, bg = run_default_pipeline()
    assert sb.bar_px == 138, sb.bar_px
    assert abs(upp - 0.1449) < 1e-4
    assert len(cells) == 2, len(cells)
    got = sorted(zip(cells["Area"], cells["Mean"], cells["IntDen"]), reverse=True)
    for (a, m, i), (ea, em, ei) in zip(got, EXPECTED):
        assert abs(a - ea) < 0.01, (a, ea)
        assert abs(m - em) < 0.01, (m, em)
        assert abs(i - ei) < 0.1, (i, ei)
    assert np.allclose(cells["CTCF"], cells["IntDen"] - cells["Area"] * bg["Mean"].mean())


def test_v2_bright_core_nuclei():
    """v2 çekirdek algılaması (parlak çekirdek gövdesi). Değerler 2026-10-31 tarihli; elle çizimle
    karşılaştırma: Dice 0.938 / 0.932, CTCF farkı +1.3 % / +4.7 % (v1: 0.935 / 0.918, −1.9 % / +8.0 %)."""
    fitc_arr, meta = core.load_image(open(FITC, "rb"))
    a = core.analyze(fitc_arr, meta, core.load_image(open(DAPI, "rb"))[0])
    assert int(a.nuclei.max()) == 2 and len(a.cell_ids) == 2
    nuc = sorted(np.bincount(a.nuclei.ravel())[1:] * a.um_per_px ** 2)
    assert abs(nuc[0] - 354.3) < 1 and abs(nuc[1] - 383.1) < 1, nuc
    cells, _, _ = core.background_and_measure(a, a.cell_ids)
    for got, exp in zip(cells[["Area", "CTCF"]].to_numpy(), [(483.78, 70910.71), (490.28, 68403.86)]):
        assert abs(got[0] - exp[0]) < 0.01 and abs(got[1] - exp[1]) < 0.1, (got, exp)


if __name__ == "__main__":
    if not FITC.exists():
        sys.exit(f"Örnek görüntü yok: {FITC}")
    test_image_392()
    test_analyze_matches_manual_pipeline()
    test_v2_bright_core_nuclei()
    print("✅ Doğrulama testi geçti: hesaplamalar Fiji ile doğrulanmış değerlerle aynı.")
