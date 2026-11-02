# CellVerity

*Formerly ICC CTCF Ölçer*

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23860020.svg)](https://doi.org/10.5281/zenodo.23860020)

**Per-cell corrected total cell fluorescence (CTCF) for immunocytochemistry images** — a desktop application (macOS, Windows) that automates the ImageJ CTCF workflow, with measurements identical to ImageJ/Fiji.

```
CTCF = Integrated density − (Cell area × Mean background)        (McCloy et al., 2014, Cell Cycle 13:1400–1412)
```

*Türkçe açıklama aşağıda — [Türkçe](#türkçe).*

## Features
- **Automatic calibration** from the cellSens scale bar, including the printed value (20 µm, 50 µm) → µm/pixel and objective
- **Cell segmentation** from the FITC channel; **touching cells separated with DAPI-stained nuclei**; automatic check that the DAPI image belongs to the same field
- **Background** boxes placed automatically away from cells — movable by drag-and-drop, or placed manually
- **Manual boundary editing:** split, merge, delete, draw — with undo/redo
- **Batch processing** of folders: FITC–DAPI pairing by image overlap (not just file numbers), group and experiment from the folder layout, border cells excluded
- **Statistics:** Welch's t / Mann–Whitney; one-way ANOVA, Kruskal–Wallis, **Dunnett vs a chosen control**, Tukey; on cell, image or **independent-experiment means** (guards against pseudoreplication); GraphPad-style plots (PNG 600 dpi / PDF / SVG)
- **Excel export with full provenance:** calibration source, segmentation and nucleus method, manual edits, Fiji check, program version; image- and experiment-mean sheets
- **Fiji bridge:** re-measure the same ROIs with Fiji's own *Measure* engine in the background and compare; open results in Fiji; compare manually traced RoiSets with automatic boundaries (**Bland–Altman**, Dice) for method validation
- **Turkish and English** interface; autosave; images never leave your computer

## Download
Stand-alone apps (no Python needed): **[Releases](https://github.com/erdal-b-dot/cellverity/releases)**

| Computer | File | Requires |
|---|---|---|
| Apple Silicon Mac (M1–M4) | `CellVerity_…_mac_AppleSilicon.dmg` | macOS 12.3+ |
| Intel Mac | `CellVerity_…_mac_Intel.dmg` | macOS 12.0+ |
| Windows 10/11 | `CellVerity_…_Windows.zip` | Windows 10+ |

macOS: open the DMG, drag the app to Applications; on first launch **right-click ▸ Open** (the app is not notarized).
Windows: extract the zip, run `CellVerity.exe`; if SmartScreen appears: **More info ▸ Run anyway**.

**User guide:** [English](docs/USER_GUIDE.md) ([PDF](docs/USER_GUIDE.pdf)) · [Türkçe](docs/KULLANIM_KILAVUZU.md) ([PDF](docs/KULLANIM_KILAVUZU.pdf)) — also in the app: Help ▸ User guide (F1).

## Example data
[`examples/`](examples/) contains two raw FITC + DAPI pairs (crowded and sparse fields; Olympus BX43 / DP74 / cellSens Entry, 40×) with expected results, so you can try the program and check your installation. Images are licensed **CC BY 4.0** (code: MIT).

## Validation
- **Identical to Fiji 1.54p** for the same ROIs (Area, Mean, StdDev, Min, Max, IntDen, RawIntDen; largest difference < 0.00001 %), checked automatically by the test suite when Fiji is installed.
- Scale bar and its label read correctly in **all 3,534 fluorescence images** tested: the author's own 2018–2021 archive (3,233 images; MDM2/P53/PARC ICC, doxorubicin and tunicamycin dose series) and the development data set (301 images); two cellSens box styles (20/50 µm). FITC–DAPI pairing by chance-corrected overlap: 1,807 pairs matched automatically in the archive; non-fluorescence images (e.g. Giemsa) are recognised and skipped.
- Agreement with manual tracing (preliminary, 1 image, 2 touching cells): Dice 0.943 / 0.938, CTCF difference +2.3 % / +3.7 %. A larger validation study is in progress; the app contains the tools to run your own (Fiji ▸ Compare with manually traced ROIs).

**Scope:** developed and validated with images acquired by the author on an **Olympus BX43** fluorescence microscope with an **Olympus DP74** colour camera and **cellSens Entry** software (FITC + DAPI). Measurements work on other images; if the scale-bar label cannot be read, the program warns you and asks for the value.

## Citation
Balcan E. (2026). *CellVerity: verifiable per-cell fluorescence (CTCF) quantification for immunocytochemistry images* (Version 2.1.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.23860020

- v2.0.0 (as ICC CTCF Ölçer): [10.5281/zenodo.23860021](https://doi.org/10.5281/zenodo.23860021)
- All versions (resolves to the latest): [10.5281/zenodo.23860020](https://doi.org/10.5281/zenodo.23860020)

Please also cite the CTCF method: McCloy RA et al. (2014) *Cell Cycle* 13(9):1400–1412, https://doi.org/10.4161/cc.28401. See `CITATION.cff`.

## Running from source
```
./install_mac.sh            # macOS (uv + Python 3.12; macOS 12+)
./run_desktop.command
install_windows.bat         # Windows
start_desktop.bat
.venv/bin/python tests/test_core.py   # validation tests
```
Build stand-alone packages: `./build_mac.sh` (Apple Silicon + Intel DMGs) · `build_windows.bat`.

| File | Purpose |
|---|---|
| `core.py` | Image processing and measurement (UI-independent, tested) |
| `batch.py` | Folder processing, FITC–DAPI pairing |
| `report.py` | Results, Excel, plots, statistics, Bland–Altman |
| `fiji.py` | Fiji bridge (headless measurement, open in Fiji) |
| `desktop.py` | Desktop interface (PySide6/Qt) |
| `i18n.py`, `locales/` | Turkish / English interface |
| `app.py` | v1 browser interface (Streamlit, Turkish) — kept for reference |
| `tests/test_core.py` | Validation tests (Fiji-verified values, statistics, translations) |

Issues and suggestions: [GitHub Issues](https://github.com/erdal-b-dot/cellverity/issues). License: MIT.

---

## Türkçe

**CellVerity** (eski adı ICC CTCF Ölçer), immunositokimya floresan görüntülerinde hücre başına **CTCF** ölçen bir masaüstü programıdır. ImageJ'deki elle yapılan iş akışını otomatikleştirir; ölçümleri ImageJ/Fiji ile birebir aynıdır.

- **İndirme:** [Releases](https://github.com/erdal-b-dot/cellverity/releases) — Mac (Apple Silicon / Intel) `.dmg`, Windows `.zip`. Python gerekmez.
- **Örnek veri:** [`examples/`](examples/) — iki ham FITC + DAPI çifti ve beklenen sonuçlar (CC BY 4.0).
- **Kullanım kılavuzu:** [KULLANIM_KILAVUZU.md](docs/KULLANIM_KILAVUZU.md) ([PDF](docs/KULLANIM_KILAVUZU.pdf)); programda Yardım ▸ Kullanım kılavuzu (F1).
- **Dil:** Arayüz bilgisayarın diline göre Türkçe ya da İngilizce açılır; Görünüm ▸ Dil / Language ile değiştirilir.
- **Özellikler:** ölçek çubuğundan otomatik kalibrasyon; FITC'den hücre, DAPI'den çekirdek bulma; değen hücreleri çekirdeklere göre ayırma; otomatik/taşınabilir/elle background; sınır düzeltme (böl, birleştir, sil, çiz); klasörü toplu ölçme; Dunnett dahil grup istatistiği (hücre/görüntü/deney ortalaması); ayrıntılı Excel; Fiji köprüsü ve Bland–Altman doğrulaması.
- **Atıf:** yukarıdaki *Citation* bölümü; DOI (tüm sürümler) 10.5281/zenodo.23860020.
- Eski tarayıcı sürümü (v1, Streamlit): `v1.0.0` etiketi.
