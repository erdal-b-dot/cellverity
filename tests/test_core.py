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


if __name__ == "__main__":
    if not FITC.exists():
        sys.exit(f"Örnek görüntü yok: {FITC}")
    test_image_392()
    print("✅ Doğrulama testi geçti: hesaplamalar Fiji ile doğrulanmış değerlerle aynı.")
