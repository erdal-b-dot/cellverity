# Example data / Örnek veri

Two raw FITC + DAPI image pairs for trying out ICC CTCF Ölçer and checking an installation.
*ICC CTCF Ölçer'i denemek ve kurulumu kontrol etmek için iki ham FITC + DAPI görüntü çifti.*

| Pair | FITC | DAPI | Field |
|---|---|---|---|
| Crowded field / kalabalık alan | `PARC_control/Image_11305.jpg` | `PARC_control/Image_11306.jpg` | many touching cells — DAPI-based separation |
| Sparse field / ayrık hücreler | `PARC_control/Image_11319.jpg` | `PARC_control/Image_11320.jpg` | mostly separate cells |

**Sample:** PARC immunocytochemistry (FITC-labelled secondary antibody), DAPI nuclear counterstain; untreated control group of a doxorubicin experiment (January 2021).
**Acquisition:** Olympus BX43 fluorescence microscope, Olympus DP74 colour camera, cellSens Entry; 40× objective; scale bar 20 µm = 137 px (0.146 µm/pixel). Files are unmodified camera output (JPEG, 1920 × 1200, original EXIF).

## Try it / Deneyin
- Drag a FITC + DAPI pair onto the program window, or use **Results ▸ Batch-measure folder…** on `PARC_control`.
- *Bir FITC + DAPI çiftini pencereye sürükleyin ya da `PARC_control` klasörünü **Sonuçlar ▸ Klasörü toplu ölç…** ile ölçün.*

## Expected results (v2.x, default settings) / Beklenen sonuçlar
See `PARC_control/expected_results_v2.csv`. With default settings you should get:

| FITC | Scale | Cells detected | Nuclei | Measured (border cells excluded) | Background | Median CTCF |
|---|---|---|---|---|---|---|
| Image_11305 | 137 px = 20 µm, 40× | 47 | 46 | 26 | 0.018 | 84 972 |
| Image_11319 | 137 px = 20 µm, 40× | 25 | 23 | 9 | 0.046 | 131 917 |

Small differences can occur between program versions if the segmentation method changes (see `Nucleus_method` and `App_version` in the Excel output).

## License / Lisans
Images © 2021 Erdal Balcan, Manisa Celal Bayar University. Licensed under **[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)** — see `LICENSE`.
You may share and adapt them for any purpose, provided you give appropriate credit:

> Balcan E. (2026). Example immunocytochemistry images (PARC, FITC/DAPI). In: *ICC CTCF Ölçer* [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.23860020

*Görüntüler CC BY 4.0 lisanslıdır: kaynak gösterilerek her amaçla paylaşılabilir ve uyarlanabilir.*
The program code is licensed separately under MIT (`../LICENSE`).
