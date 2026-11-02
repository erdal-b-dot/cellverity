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
    a = core.analyze(fitc_arr, meta, core.load_image(open(DAPI, "rb"))[0], core.Settings(nuc_method="otsu"))
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
    a = core.analyze(fitc_arr, meta, core.load_image(open(DAPI, "rb"))[0], core.Settings(nuc_method="bright_core"))
    assert int(a.nuclei.max()) == 2 and len(a.cell_ids) == 2
    nuc = sorted(np.bincount(a.nuclei.ravel())[1:] * a.um_per_px ** 2)
    assert abs(nuc[0] - 354.3) < 1 and abs(nuc[1] - 383.1) < 1, nuc
    cells, _, _ = core.background_and_measure(a, a.cell_ids)
    for got, exp in zip(cells[["Area", "CTCF"]].to_numpy(), [(483.78, 70910.71), (490.28, 68403.86)]):
        assert abs(got[0] - exp[0]) < 0.01 and abs(got[1] - exp[1]) < 0.1, (got, exp)


def test_v2_local_nuclei():
    """v2 varsayılan çekirdek algılaması ('local', 2026-11-01). Image_392 elle çizime göre Dice 0.943/0.938;
    20× kümelerde (Image_287) bright_core 4 çekirdek bulurken local ≥ 40 bulmalı."""
    fitc_arr, meta = core.load_image(open(FITC, "rb"))
    a = core.analyze(fitc_arr, meta, core.load_image(open(DAPI, "rb"))[0])
    assert a.nuc_method == "local" and int(a.nuclei.max()) == 2 and len(a.cell_ids) == 2
    cells, _, _ = core.background_and_measure(a, a.cell_ids)
    for got, exp in zip(cells[["Area", "CTCF"]].to_numpy(), [(478.58, 70203.38), (495.48, 69111.2)]):
        assert abs(got[0] - exp[0]) < 0.01 and abs(got[1] - exp[1]) < 0.1, (got, exp)
    p286, p287 = ROOT / "ornek" / "Image_286.jpg", ROOT / "ornek" / "Image_287.jpg"
    if p286.exists():
        f, m = core.load_image(str(p286))
        a = core.analyze(f, m, core.load_image(str(p287))[0])
        assert int(a.nuclei.max()) >= 40, a.nuclei.max()


def test_scale_label_reading():
    """Ölçek etiketi okunmalı: 20 µm (40×) ve 50 µm (20×). 2026-10-31 öncesi hep 20 varsayılıyordu →
    50 µm'lik görüntülerde alan 6.25 kat küçük çıkıyordu."""
    a, _ = core.load_image(str(FITC))
    assert core.read_scale_label(a, core.detect_scale_bar(a)) == 20.0
    p50 = ROOT / "ornek" / "Image_286.jpg"
    if p50.exists():
        a, m = core.load_image(str(p50))
        an = core.analyze(a, m)
        assert an.bar_um == 50.0 and an.bar_um_source == "label"
        assert abs(an.um_per_px - 50 / 172) < 1e-9 and an.objective[0] == 20


def test_report_exports(tmp=None):
    """Biriken tablo: aynı görüntü yeniden eklenince üzerine yazılır; Excel 4 sayfa; istatistik doğru."""
    import tempfile
    import pandas as pd
    from scipy import stats as sps
    import report
    rng = np.random.default_rng(1)
    res = pd.DataFrame()
    for g, mu in (("Kontrol", 100.0), ("İlaç", 140.0)):
        for k in range(2):
            cells = pd.DataFrame({"Cell": range(1, 6), "Area_unit": "µm²", "Area": 400.0,
                                  "CTCF": rng.normal(mu, 10, 5)})
            res = report.add_image(res, cells, {"Group": g, "Image": f"{g}{k}.jpg", "Image_path": f"/x/{g}{k}.jpg"})
    assert len(res) == 20
    again = pd.DataFrame({"Cell": [1], "Area_unit": "µm²", "Area": 1.0, "CTCF": 1.0})
    res2 = report.add_image(res, again, {"Group": "Kontrol", "Image": "Kontrol0.jpg", "Image_path": "/x/Kontrol0.jpg"})
    assert len(res2) == 16
    _, txt = report.plot(res, "CTCF")
    p = sps.ttest_ind(res.CTCF[res.Group == "Kontrol"], res.CTCF[res.Group == "İlaç"], equal_var=False).pvalue
    assert report.p_fmt(p) in txt
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "t.xlsx"
        report.write_excel(path, res, pd.DataFrame({"BG": [1]}), "test")
        with pd.ExcelFile(path) as x:   # Windows: kapatılmazsa geçici klasör silinemez (WinError 32)
            assert x.sheet_names == ["Cells", "Group_summary", "Image_means", "Background", "Methods"]
            assert len(pd.read_excel(x, "Cells")) == 20
            assert pd.read_excel(x, "Group_summary")["n"].tolist() == [10, 10]


def test_batch_pairing():
    """Klasör eşleştirme: doğru çift eşleşir; başka alanın DAPI'si (numara ardışık olsa da) eşleşmez;
    EXIF'siz (merge/yeniden kaydedilmiş) JPEG atlanır."""
    import shutil
    import tempfile
    from PIL import Image
    import batch
    p286, p287 = ROOT / "ornek" / "Image_286.jpg", ROOT / "ornek" / "Image_287.jpg"
    if not p286.exists():
        return
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "A").mkdir(); (d / "B").mkdir()
        shutil.copy(FITC, d / "A" / "Image_392.jpg"); shutil.copy(DAPI, d / "A" / "Image_393.jpg")
        shutil.copy(FITC, d / "B" / "Image_10.jpg"); shutil.copy(p287, d / "B" / "Image_11.jpg")  # farklı alan
        Image.open(p286).save(d / "B" / "Image_20-21.jpg")                                       # EXIF'siz
        items = {(it.group, it.fitc.name if it.fitc else None): it for it in batch.scan(d)}
        a = items[("A", "Image_392.jpg")]
        assert a.dapi.name == "Image_393.jpg" and a.status == "ready"
        b = items[("B", "Image_10.jpg")]
        assert b.dapi is None and b.status == "no_dapi", b
        assert items[("B", "Image_20-21.jpg")].status == "skipped" and not items[("B", "Image_20-21.jpg")].use
        an, cells, _ = batch.measure(a, core.Settings())
        assert len(cells) == 2


def test_group_statistics():
    """Kontrol seçimi, Dunnett (elle hesapla aynı), deney düzeyi, karışık objektif uyarısı."""
    import pandas as pd
    from scipy import stats as sps
    import report
    rng = np.random.default_rng(3)
    rows = []
    for g, mu, obj in (("Uygulama1", 105, 40), ("Kontrol", 100, 40), ("Uygulama2", 150, 40)):
        for e in (1, 2, 3):
            for c in range(6):
                rows.append(dict(Group=g, Experiment=e, Image_path=f"{g}/{e}", CTCF=rng.normal(mu + 8 * e, 15),
                                 Area_unit="µm²", Objective=obj))
    r = pd.DataFrame(rows)
    groups, data, txt, pairs = report.compare(r, "CTCF", "experiment", control="Kontrol")
    assert groups[0] == "Kontrol" and [len(d) for d in data] == [3, 3, 3]
    agg = r.groupby(["Group", "Experiment"]).CTCF.mean()
    ref = sps.dunnett(agg["Uygulama1"].values, agg["Uygulama2"].values, control=agg["Kontrol"].values,
                      random_state=0).pvalue
    assert np.allclose([p for _, _, p in pairs], ref)
    assert "Dunnett" in txt and "objektif" not in txt
    r.loc[r.Group == "Uygulama2", "Objective"] = 20
    assert "Farklı objektifler" in report.compare(r, "CTCF", "image", control="Kontrol")[2]
    assert "yalancı tekrar" in report.compare(r, "CTCF", "cell", control="Kontrol")[2]


def test_manual_edits():
    """Elle düzeltme: birleştir/böl alanı korur, sil kaldırır, çiz ImageJ çokgen kuralıyla piksel ekler."""
    from skimage import measure
    fitc_arr, meta = core.load_image(open(FITC, "rb"))
    a = core.analyze(fitc_arr, meta, core.load_image(open(DAPI, "rb"))[0])
    L = a.labels
    M = core.merge_cells(L, 1, 2)
    assert set(np.unique(M)) == {0, 1} and (M > 0).sum() == (L > 0).sum()
    r = {p.label: p for p in measure.regionprops(L)}
    y0, _, y1, _ = r[1].bbox
    cx = int(r[1].centroid[1])
    S, split = core.split_cells(L, [(cx, y0 - 5), (cx, y1 + 5)])
    assert split == [1] and len(np.unique(S)) == 4 and (S > 0).sum() == (L > 0).sum()
    assert set(np.unique(core.delete_cell(L, 2))) == {0, 1}
    A, cid = core.add_cell(L, [(100, 100), (200, 100), (200, 200), (100, 200)])
    assert cid == 3 and (A == cid).sum() == 100 * 100
    a2 = core.relabeled(a, S)
    assert a2.cell_ids == [1, 2, 3] and a2.labels is S


def test_fiji_bridge():
    """Fiji kuruluysa: aynı ROI'leri Fiji'nin kendi Measure motoru (Analyzer) ölçer → birebir aynı olmalı."""
    import tempfile
    import fiji
    exe = fiji.find_fiji()
    if exe is None:
        print("  (Fiji bulunamadı — Fiji köprüsü testi atlandı)")
        return
    fitc_arr, meta = core.load_image(open(FITC, "rb"))
    a = core.analyze(fitc_arr, meta, core.load_image(open(DAPI, "rb"))[0])
    cells, bg, boxes = core.background_and_measure(a, a.cell_ids)
    with tempfile.TemporaryDirectory() as d:
        tif, rois = fiji.write_package(Path(d), a, a.cell_ids, boxes, "t")
        df, ver = fiji.measure_in_fiji(exe, tif, rois, a.um_per_px)
    cmp = fiji.compare(cells, bg, df)
    assert len(cmp) == 5 and not cmp.isna().any().any() and cmp["Max diff (%)"].max() < 1e-3, cmp


def test_translations():
    """İngilizce arayüz: koddaki her T("…") metninin çevirisi var, yer tutucular iki dilde aynı, ve T() dışında
    Türkçe arayüz metni kalmamış (ürün adı ve kontrol grubu anahtar kelimesi hariç)."""
    import ast
    import json
    import re
    import i18n
    en = json.loads((ROOT / "locales" / "en.json").read_text(encoding="utf-8"))
    ph = re.compile(r"\{[^{}]*\}")
    trc = re.compile(r"[çğıöşüÇĞİÖŞÜ]")
    allowed = {"ilaçsız"}
    missing, leftover = [], []
    for f in ("desktop.py", "report.py", "fiji.py"):
        tree = ast.parse((ROOT / f).read_text(encoding="utf-8"))
        inside, docs = set(), set()
        for n in ast.walk(tree):
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and \
                    isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
                docs.add(id(n.body[0].value))
            if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "T":
                for m in ast.walk(n):
                    inside.add(id(m))
                if n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value not in en:
                    missing.append(n.args[0].value[:60])
            if isinstance(n, ast.Assign) and any(getattr(t, "id", "") in ("LEVELS", "COMPARISONS", "PLOT_KINDS")
                                                  for t in n.targets):
                for v in getattr(n.value, "values", []):  # yalnızca etiketler; anahtarlar iç kod
                    if isinstance(v, ast.Constant) and v.value not in en:
                        missing.append(v.value[:60])
                for m in ast.walk(n.value):
                    inside.add(id(m))
            if isinstance(n, ast.Assign) and any(getattr(t, "id", "") in ("MEASURE_GROOVY", "OPEN_MACRO")
                                                  for t in n.targets):
                for m in ast.walk(n.value):
                    inside.add(id(m))
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in inside | docs \
                    and trc.search(n.value) and n.value not in allowed \
                    and "ICC CTCF Ölçer" not in n.value:  # eski ad (özel isim) çevrilmez
                leftover.append(f"{f}:{n.lineno} {n.value[:50]}")
    bad_ph = [k[:50] for k, v in en.items() if sorted(ph.findall(k)) != sorted(ph.findall(v))]
    assert not missing, f"çevirisi yok: {missing}"
    assert not leftover, f"T() dışında Türkçe metin: {leftover}"
    assert not bad_ph, f"yer tutucu uyuşmazlığı: {bad_ph}"
    i18n.set_language("en")
    assert i18n.T("Hücre sayısı") == "Cell count"
    i18n.set_language("tr")
    assert i18n.T("Hücre sayısı") == "Hücre sayısı"


def test_chance_corrected_pairing():
    """Kalabalık alanda (hücreler görüntünün ~%50'si) başka alana ait DAPI ham oranla ~%55 örtüşür ve eşleşiyordu.
    Şansa göre düzeltilmiş skorla reddedilmeli; doğru çift ≈ 1 almalı (samples/Image_11305/06, 11323/22)."""
    import shutil
    import tempfile
    import batch
    names = ["Image_11305.jpg", "Image_11306.jpg", "Image_11322.jpg", "Image_11323.jpg"]
    if not all((ROOT / "ornek" / n).exists() for n in names):
        return
    with tempfile.TemporaryDirectory() as d:
        for n in names:
            shutil.copy(ROOT / "ornek" / n, Path(d) / n)
        items = {it.fitc.name if it.fitc else it.dapi.name: it for it in batch.scan(Path(d), recursive=False)}
    assert items["Image_11305.jpg"].status == "ready" and items["Image_11305.jpg"].overlap > 0.9
    assert items["Image_11323.jpg"].status == "no_dapi" and items["Image_11323.jpg"].overlap < 0.3
    assert items["Image_11322.jpg"].reason == "unpaired_dapi"


def test_scale_bar_hard_cases():
    """Köşede kutudan büyük doymuş beyaz hücre (Image_10841; eski yöntem 65 px buldu) ve kutuya değen parlak hücre
    (Image_14164; etiket okunamıyordu): ikisinde de 20 µm / 137 px okunmalı. Bu arşivde kutu daha büyük
    (çubuk ~9 px, kutu 68 px) — Image_392'deki küçük kutu (3 px / 31 px) da aynı kodla okunur."""
    for name in ("Image_10841.jpg", "Image_14164.jpg"):
        p = ROOT / "ornek" / name
        if not p.exists():
            continue
        a, _ = core.load_image(str(p))
        sb = core.detect_scale_bar(a)
        assert sb.bar_px == 137 and core.read_scale_label(a, sb) == 20.0, (name, sb)


def test_examples_expected_results():
    """Repodaki örnek veri (examples/, CC BY 4.0) beklenen sonuçları vermeli — herkesin bilgisayarında çalışan test."""
    import pandas as pd
    import batch
    folder = ROOT / "examples" / "PARC_control"
    exp = pd.read_csv(folder / "expected_results_v2.csv").set_index("FITC")
    for it in batch.scan(folder, recursive=False):
        if it.status != "ready":
            continue
        a, cells, bg = batch.measure(it, core.Settings())
        e = exp.loc[it.fitc.name]
        assert it.dapi.name == e.DAPI and len(a.cell_ids) == e.cells_detected, (it.fitc.name, len(a.cell_ids))
        assert int(a.nuclei.max()) == e.nuclei and len(cells) == e.cells_measured_edge_excluded
        assert abs(cells.CTCF.median() - e.CTCF_median) < 1, (cells.CTCF.median(), e.CTCF_median)


def test_exposure_metadata_and_warning():
    """Pozlama süresi EXIF'ten okunur; farklı pozlamalar bir aradaysa uyarı verilir (samples: 0.5 s ve 0.649 s)."""
    import pandas as pd
    import report
    folder = ROOT / "examples" / "PARC_control"
    e1 = core.load_image(str(folder / "Image_11305.jpg"))[1].get("exposure_s")
    e2 = core.load_image(str(folder / "Image_11319.jpg"))[1].get("exposure_s")
    assert e1 == 0.5 and abs(e2 - 0.649) < 1e-6, (e1, e2)
    same = pd.DataFrame({"Group": ["A", "B"], "Image_path": ["x", "y"], "Exposure_s": [0.5, 0.5]})
    mixed = pd.DataFrame({"Group": ["A", "B"], "Image_path": ["x", "y"], "Exposure_s": [0.5, 0.649]})
    assert report.mixed_exposures(same) == "" and "0.649" in report.mixed_exposures(mixed)


def test_quality_control_and_exclusions():
    """QC bayrakları ve toplu ölçümde gerekçeli dışlama (örnek veri: 11305'te kenara değmeyen 26 hücreden 3'ü doymuş)."""
    import batch
    ref = (1000.0, 100.0)
    assert core.qc_flags({"Saturated_px": 2, "Nuclei_in_cell": 1, "Nucleus_area_px": 900, "Nucleus_DAPI_mean": 100}, ref) == ["saturated"]
    assert core.qc_flags({"Saturated_px": 0, "Nuclei_in_cell": 2}, ref) == ["multinucleate"]
    assert core.qc_flags({"Saturated_px": 0, "Nuclei_in_cell": 1, "Nucleus_area_px": 200, "Nucleus_DAPI_mean": 100}, ref) == ["partial_nucleus"]
    assert core.qc_flags({"Saturated_px": 0, "Nuclei_in_cell": 1, "Nucleus_area_px": 400, "Nucleus_DAPI_mean": 180}, ref) == ["pyknotic"]
    assert core.qc_flags({"Saturated_px": 0, "Nuclei_in_cell": 1, "Nucleus_area_px": 900, "Nucleus_DAPI_mean": 110}, ref) == []
    folder = ROOT / "examples" / "PARC_control"
    it = next(i for i in batch.scan(folder, recursive=False) if i.fitc and i.fitc.name == "Image_11305.jpg")
    a, cells, bg, excl = batch.measure_qc(it, core.Settings())
    a2, all_cells, _ = batch.measure(it, core.Settings())
    assert len(cells) + (excl["Reason"] == "saturated").sum() == len(all_cells) == 26
    assert set(excl["Reason"].str.split(";").explode()) <= {"border", "saturated", "no_nucleus", "partial_nucleus",
                                                            "multinucleate", "pyknotic"}
    assert (excl["Exclusion"] == "auto").all() and cells["QC_pass"].all()


# ornek/ klasöründeki yayımlanmamış görüntüler olmadan çalışamayanlar. Geri kalanlar depodaki
# examples/ veriyle ya da üretilmiş veriyle her bilgisayarda çalışır; bazıları eksik dosyayı
# kendi içinde atlar.
NEEDS_SAMPLE = {"test_image_392", "test_analyze_matches_manual_pipeline", "test_v2_bright_core_nuclei",
                "test_v2_local_nuclei", "test_scale_label_reading", "test_manual_edits"}

if __name__ == "__main__":
    # Çıktı dosyaya ya da boruya yönlendirilince Windows yerel kod sayfasına (cp1254) düşer ve
    # ✅ gibi karakterler UnicodeEncodeError verir.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    # Testler adlarından bulunur: yeni bir test eklenince listeye yazmayı unutmak diye bir şey olmasın.
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f) and getattr(f, "__module__", "") == "__main__"]
    have_sample = FITC.exists()
    ran = [n for n, f in tests if not (n in NEEDS_SAMPLE and not have_sample)]
    for name, fn in tests:
        if name in ran:
            fn()
    print(f"✅ {len(ran)} test geçti.")
    if have_sample:
        print("✅ Hesaplamalar Fiji ile doğrulanmış değerlerle aynı.")
    else:
        print(f"ℹ️  {len(tests) - len(ran)} test atlandı: {FITC.parent} klasöründe örnek görüntü yok "
              "(yayımlanmamış veri). Fiji ile doğrulanmış değerleri denetleyen testler bunlardır; "
              "geri kalanlar depodaki examples/ verisiyle çalıştı.")
