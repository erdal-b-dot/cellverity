# ICC CTCF Ölçer 2 — User Guide

*Version 2.0.0 · Erdal Balcan, Manisa Celal Bayar University · MIT license · DOI: [10.5281/zenodo.23860021](https://doi.org/10.5281/zenodo.23860021)*

Source code and downloads: https://github.com/erdal-b-dot/icc-ctcf-olcer · Türkçe kılavuz: `KULLANIM_KILAVUZU.md`

---

## Contents
1. [What does the program do?](#1-what-does-the-program-do)
2. [Installation](#2-installation)
3. [Image requirements](#3-image-requirements)
4. [Quick start (5 minutes)](#4-quick-start-5-minutes)
5. [The main window](#5-the-main-window)
6. [Measuring a single image — step by step](#6-measuring-a-single-image-step-by-step)
7. [Editing cell boundaries](#7-editing-cell-boundaries)
8. [Batch-measuring a folder](#8-batch-measuring-a-folder)
9. [Results, Excel and autosave](#9-results-excel-and-autosave)
10. [Plots and statistics (comparing groups)](#10-plots-and-statistics-comparing-groups)
11. [Fiji bridge and method validation](#11-fiji-bridge-and-method-validation)
12. [Warnings: what they mean and what to do](#12-warnings-what-they-mean-and-what-to-do)
13. [For your paper: methods text and citation](#13-for-your-paper-methods-text-and-citation)
14. [Troubleshooting](#14-troubleshooting)
15. [Technical details](#15-technical-details)

---

## 1. What does the program do?

It measures **per-cell CTCF** (corrected total cell fluorescence) in immunocytochemistry (ICC) fluorescence images:

> **CTCF = Integrated density − (Cell area × Mean background)**
> (McCloy et al., 2014, *Cell Cycle* 13:1400–1412)

It automates the manual ImageJ workflow:

| Manually in ImageJ | In this program |
|---|---|
| Calibrate with Set Scale | The scale bar **and the value printed under it** (20 µm, 50 µm) are read automatically |
| Trace every cell with the polygon tool | Cells are segmented from FITC; touching cells are separated using DAPI nuclei |
| Draw and measure 3 background regions | 3 boxes are placed automatically away from cells (movable, or add your own) |
| Measure → copy to Excel → formula | Table, Excel, group summary, plots and statistics in one click |

**Measurements are identical to ImageJ/Fiji.** For the same cell boundaries, Area, Mean, StdDev, Min, Max, IntDen and RawIntDen are the same as Fiji's (largest difference < 0.00001 %). You can check this yourself from within the program: **Fiji ▸ Verify with Fiji** ([Section 11](#11-fiji-bridge-and-method-validation)).

Your images are **never sent anywhere**; the program works offline.

**Language:** the interface follows your computer's language (Turkish or English). Change it under **View ▸ Language / Dil** (takes effect after restart). Excel output is always in English.

---

## 2. Installation

### 2.1 Ready-to-run app (recommended — no Python needed)
Download from **https://github.com/erdal-b-dot/icc-ctcf-olcer/releases** (newest version at the top).

| Computer | File | Minimum system |
|---|---|---|
| Apple Silicon Mac (M1/M2/M3/M4) | `ICC_CTCF_Olcer_<version>_mac_AppleSilicon.dmg` | macOS 12.3 |
| Intel Mac | `ICC_CTCF_Olcer_<version>_mac_Intel.dmg` | macOS 12.0 (Monterey) |
| Windows 10/11 (64-bit) | `ICC_CTCF_Olcer_<version>_Windows.zip` | Windows 10 |

> To find your Mac's processor: Apple menu ▸ **About This Mac**. "Chip: Apple M…" means Apple Silicon; "Processor: Intel…" means Intel.

**macOS:**
1. Double-click the `.dmg` → drag **ICC CTCF Ölçer** onto the **Applications** folder shown next to it. Then eject the disk (⏏) in the Finder sidebar.
2. **On first launch** do not double-click: **right-click the app ▸ Open ▸ Open**. (The app is not notarized by Apple, so macOS shows an "unidentified developer" warning; this is needed only once.)
3. If you see *"is damaged and can't be opened"* (happens with downloaded files), run once in Terminal:
   `xattr -cr "/Applications/ICC CTCF Ölçer.app"`

**Windows:**
1. Right-click the zip ▸ **Extract All**. Put the folder e.g. in `Documents` (do not run it from inside the zip).
2. Double-click `ICC CTCF Olcer.exe`. If *"Windows protected your PC"* appears: **More info ▸ Run anyway**.
3. Desktop shortcut: right-click the exe ▸ Send to ▸ Desktop (create shortcut).

### 2.2 Running from source
With a Python environment (to receive updates via `git pull`):
- macOS: `./install_mac.sh`, then `./run_desktop.command`
- Windows: `install_windows.bat`, then `start_desktop.bat`

Building the stand-alone packages yourself: `./build_mac.sh` (macOS) / `build_windows.bat` (Windows).

### 2.3 Fiji (optional but recommended)
The Fiji bridge ([Section 11](#11-fiji-bridge-and-method-validation)) requires Fiji: https://imagej.net/software/fiji/downloads
The program looks for Fiji in `Downloads/Fiji`, `Applications/Fiji`, your home folder (`~/Fiji`, `C:\Fiji`). Elsewhere: **Fiji ▸ Choose Fiji location…** (asked once, remembered).

### 2.4 Earlier browser version (v1)
v1 (the browser-based Streamlit version, Turkish only) is still available under the `v1.0.0` tag. v1 and v2 give the same numbers for the same cell boundaries, but the **nucleus detection method differs**, so boundaries between touching cells are drawn slightly differently ([Section 15](#15-technical-details)). Measure all images of a study with **the same version**.

---

## 3. Image requirements

However good the program is, the validity of the measurement depends on the image.

**Required:**
- **Raw, single-channel images.** The FITC image saved directly by the microscope software (cellSens etc.). Images that went through Photoshop, had brightness/contrast adjusted, or were **merged** **cannot be used** for CTCF — the program detects these and warns you.
- **All compared images acquired with identical settings:** same objective, exposure time, gain, lamp power, white balance.
- **Same objective.** Do not compare 20× with 40× images — the program warns if objectives are mixed.
- **No saturated pixels.** The number of saturated pixels is reported for every cell ("Saturated px" column).

**Recommended:**
- **The DAPI image of the same field.** Essential for separating touching cells correctly ([Warnings](#12-warnings-what-they-mean-and-what-to-do)).
- **Keep the scale bar in the image.** Calibration is read from it (cellSens style: white box in the lower right corner).
- **TIFF** is better than JPEG (JPEG is lossy). Use the same format for all images of a study.

**Tested camera:** Olympus DP74 colour camera with cellSens. On this camera FITC appears yellow-green and DAPI **cyan**. FITC is measured on the **green (G) channel**; FITC and DAPI are told apart by the blue/red ratio of the brightest pixels. Other cameras/software should work for measurement; if the scale-bar label cannot be read, the program warns you and asks for the value ([Section 6.2](#62-checking-the-calibration)).

---

## 4. Quick start (5 minutes)

1. Open the program.
2. In Finder/Explorer, **select the FITC and DAPI files together** and drag them onto the window. The program tells which one is DAPI by its colour.
3. Check the right panel: **Calibration** (e.g. 0.1449 µm/pixel, 20 µm, *read from label*), **Objective**, **Cell count**, the green **"Cell separation: DAPI nuclei"** box.
4. **Select all cells** (or click the cells to measure — they turn yellow). The **Cells** tab below shows CTCF.
5. In the right panel enter **Group / condition** (e.g. *Control*) and **Experiment / replicate** (e.g. *1*) → **➕ Add to results table** (⌘↩ / Ctrl+Enter).
6. Next image: close with **⌘W**, drag the next pair, change the group, add.
7. When done: **Save to Excel** (⌘E) and **Plot…** (⌘G).

With many images, use **Batch-measure folder** (⌘B) instead of steps 4–6 ([Section 8](#8-batch-measuring-a-folder)).

---

## 5. The main window

| Part | Contents |
|---|---|
| **Menus** | File · Results · Fiji · Edit · View · Help |
| **Toolbar 1** | Open FITC · Open DAPI · Close images · Fit/Zoom in/Zoom out · **Display:** FITC / DAPI / Merged · Nucleus outlines |
| **Toolbar 2** | **Boundary editing:** Select · Split · Merge · Delete · Draw · Undo · Redo — **Results:** add to table · batch · Excel · Plot · Verify with Fiji |
| **Image area** | Mouse wheel: zoom · Drag: pan · Click: select cell |
| **Right panel** | Files, scale bar, calibration, objective, counts, cell-separation indicator, cell selection, background settings, results (group, experiment), legend, display brightness |
| **Bottom tabs** | Cells · Background boxes · Collected results · Group summary |

**Outlines on the image:**

| Outline | Meaning |
|---|---|
| Grey, numbered | Cell boundary found by the program |
| **Yellow** | Selected (measured) cell |
| **Magenta** | Nucleus boundary found in DAPI |
| **Red square** (BG1, BG2…) | Background box |

The **Display brightness** slider and **Display: FITC/DAPI/Merged** change **only the screen**; measurement always uses the raw FITC (green channel) data.

---

## 6. Measuring a single image — step by step

### 6.1 Opening images
- **Drag and drop** (easiest): drag FITC + DAPI together.
- **Open FITC… (⌘O)** and **Open DAPI… (⌘D)**.
- If you use the wrong button (e.g. a blue file with "Open FITC"), the program asks: *"… looks like a DAPI image, open it as DAPI?"*
- **Opening a new FITC removes the previous field's DAPI** (another field's nuclei would separate cells wrongly). Open the new field's DAPI too.
- **Close images (⌘W):** clears the window; collected results are kept.

### 6.2 Checking the calibration
The **Calibration** line in the right panel also tells the source:
- *read from label* — the value under the scale bar (20 µm, 50 µm) was read. ✅
- *entered manually* — the value you typed into the **Scale bar** box.
- *label NOT READ, assumed* — a red warning appears; type the value shown in the image into the **Scale bar** box.

> ⚠️ A wrong scale value makes **area and IntDen wrong several-fold** (e.g. 20 µm instead of 50 µm: 6.25×). Glance at the calibration line for every new image.

Known values for DP74 + cellSens: **20 µm = 138 px → 0.1449 µm/px (40×)**; **50 µm = 172 px → 0.2907 µm/px (20×)**.

### 6.3 Cell-separation indicator
| Indicator | Meaning | What to do |
|---|---|---|
| 🟢 **DAPI nuclei** | Touching cells were separated using nuclei | — |
| 🟡 **Shape only (no touching cells)** | No DAPI, but none needed | — |
| 🔴 **Shape only — N touching cell pairs** | Touching cells separated by shape only (~5% error) | Open the DAPI of the same field |
| 🔴 **DAPI does not seem to belong to the same field** | Most nuclei lie outside the cells | Open the correct DAPI (consecutive numbers can still be different fields) |

### 6.4 Selecting cells
- **Click** a cell → it turns yellow and is measured; click again → deselected.
- **Select all cells** / **Clear selection**.
- Do not measure cells **cut off** at the image border (their area is incomplete).

### 6.5 Background
- **Automatic** (default): **3 boxes** (50×50 pixels) ≥ 40 pixels away from cells, free of signal/debris, as close to the cells as possible. Size and number are set in the right panel.
- **Moving boxes:** hover over a box (hand cursor), press and drag. It is re-measured when released. Moving an automatic box switches to **Manual**; the other boxes stay in place.
- **Manual:** click an empty area → a box is added; click a box → it is removed. **Clear manual boxes**.
- A box overlapping a cell is not accepted (it moves back).
- Per-box values: **Background boxes** tab below.

> ℹ️ **If the background is 0**, the camera/cellSens clipped the dark background to zero; CTCF = IntDen. Comparisons are valid if all images were acquired with the same settings.

### 6.6 Adding to the results table
- **Group / condition:** e.g. *Control*, *Drug 10 µM 24 h*. Plots and statistics group by this label.
- **Experiment / replicate:** independent experiment (biological replicate): *1*, *2*, *3*… Needed for statistics on experiment means ([Section 10](#10-plots-and-statistics-comparing-groups)).
- **➕ Add to results table (⌘↩).** Re-adding the same image replaces the earlier entry (it is not counted twice).

---

## 7. Editing cell boundaries

Automatic boundaries are good in most images; dense clusters, debris or dim cells may need corrections. **Toolbar 2 ▸ Boundary editing**:

| Tool | How | When |
|---|---|---|
| **Select** | Normal mode | Select cells, move boxes, pan |
| **Split** | Draw a line across touching cells **from one edge to the other** | Two (or more) cells were counted as one |
| **Merge** | Click one cell, then its neighbour | One cell was split in two |
| **Delete** | Click the region | Debris or a non-cell region |
| **Draw** | Draw the cell boundary with the mouse; it closes when released | A missed cell or a poorly outlined boundary (the drawing overrides cells beneath) |
| **Undo / Redo** | ⌘Z / ⇧⌘Z (Windows: Ctrl+Z / Ctrl+Y), 30 steps | Every edit can be undone |

- In Split and Draw modes, pan by holding **⌥ Option (Windows: Alt)** while dragging.
- Splitting and merging **preserve the total area**.
- Edits are written to the **Manual_edits** column in Excel (e.g. *merge 1+2; split 1*).
- Changing the scale value re-analyses the image and **resets the edits** (a warning appears below). Calibrate first, then edit.

---

## 8. Batch-measuring a folder

**Results ▸ Batch-measure folder… (⌘B)**

### 8.1 Recommended folder layout
```
Experiments/
  Exp_1/
    Control/      ← FITC + DAPI images
    Treatment1/
    Treatment2/
  Exp_2/
    Control/
    ...
```
- **Group** = name of the folder containing the image; **Experiment** = the folder above it.
- If you select a single experiment folder (e.g. `Exp_1`), its name becomes the experiment name.
- Both can be edited in the table before measuring.

### 8.2 FITC–DAPI pairing
Each FITC is paired with the DAPI, among those **within ±3 file numbers in the same folder**, whose **nuclei actually overlap the cells**. Overlap is a **chance-corrected** score (1 = all nuclei inside cells, 0 = no better than random placement); ≥ 0.5 is required. A raw fraction would mislead: in a crowded field where cells cover half the image, a DAPI from another field still overlaps ~50%. Consecutive numbers do not always mean the same field — the program checks the images themselves.

| Status | Meaning |
|---|---|
| 🟢 **ready** | Pair found (percentage in the Overlap column) |
| 🟠 **no DAPI** | No matching DAPI; cells will be separated by shape only |
| ⚪ **skipped: no camera information** | Merged or re-saved image |
| ⚪ **skipped: processed image** | Saved by Photoshop etc. |
| ⚪ **skipped: could not tell FITC from DAPI** | Ambiguous colour (e.g. merged) |
| ⚪ **skipped: unpaired DAPI** | A DAPI that belongs to no FITC |

### 8.3 Measurement
- Ticked rows are measured; untick those you do not want.
- In each image: **all cells** + **automatic background** (box size/number from the right panel).
- **Cells touching the image border** are excluded by default.
- The **Selection** column in Excel records *manual click* or *batch: all cells, edge excluded*.
- After batch measurement, opening suspicious images one by one is recommended (especially dense clusters).

---

## 9. Results, Excel and autosave

### 9.1 Excel sheets
| Sheet | Contents |
|---|---|
| **Cells** | All per-cell measurements with context |
| **Group_summary** | n, mean, SD, SEM, median, min, max per group (CTCF) |
| **Image_means** | Image (field) means — ready to paste into GraphPad |
| **Experiment_means** | Experiment means — the recommended statistical unit |
| **Background** | Per-box background measurements |
| **Methods** | Formulas, methods, citation |
| **Validation**, **Validation_summary** | Manual (Fiji) vs automatic comparison and Bland–Altman summary (if present) |

### 9.2 Key columns in the Cells sheet
| Column | Meaning |
|---|---|
| Area, Mean, StdDev, Min, Max, IntDen, RawIntDen | Same definitions as ImageJ |
| BG_Mean, CTCF, CTCF_per_Area | Background mean, CTCF, CTCF/area (= Mean − BG_Mean) |
| Saturated_px | Saturated pixel count (should be 0) |
| um_per_px, Scale_bar_um, Scale_source, Objective | Calibration and its source (label / user / default) |
| BG_mode, BG_box_px, BG_n | Background method |
| Segmentation, Nucleus_method, DAPI_overlap, Touching_pairs | Cell separation details |
| Selection, Manual_edits | How cells were selected; manual boundary edits |
| Fiji_check | Result of the Fiji verification, if done |
| App_version, Timestamp | Program version, date |

### 9.3 Other outputs
- **CSV** (opens correctly in Excel, including non-ASCII characters).
- **ROI image (PNG):** with outlines and boxes.
- **ImageJ/Fiji comparison package (ZIP):** measured channel (TIFF) + ROIs (RoiSet.zip) + instructions (`HOW_TO_USE.txt`).

### 9.4 Not losing your work
- **Autosave:** after every addition, `Documents/ICC CTCF Olcer/otomatik_kayit.xlsx`. Even after a crash or power cut nothing is lost; on restart the program asks *"Continue where you left off?"*
- **Open previous results (Excel)…:** load a saved Excel file and continue measuring (the same image is not counted twice).
- Quitting with unsaved results asks whether to save.

---

## 10. Plots and statistics (comparing groups)

**Results ▸ Plot and statistics… (⌘G)**

| Setting | Options |
|---|---|
| **Control group** | Reference for Dunnett's test and normalisation (a group named *Control/Kontrol/untreated/vehicle…* is chosen automatically) |
| **Variable** | CTCF · CTCF_per_Area · Mean · IntDen · Area |
| **Statistical unit** | Cell · Image mean · **Experiment mean (recommended)** |
| **Multiple comparisons** | **Dunnett** (each group vs control) · Tukey HSD (all pairs) |
| **Plot type** | Bar (mean ± SEM) · Box · Violin — all with individual points |
| **Group order** | Drag to reorder (control always first, grey) |
| Normalise | Control mean = 1 |
| Asterisks | GraphPad notation: ns, \* p<0.05, \*\* p<0.01, \*\*\* p<0.001, \*\*\*\* p<0.0001 |

**Tests:** 2 groups → Welch's t-test + Mann–Whitney U. 3+ groups → one-way ANOVA + Kruskal–Wallis + Dunnett (or Tukey).

### 10.1 Important: the statistical unit (pseudoreplication)
Cells from the same experiment are not independent. Counting every cell as a replicate makes **p values look smaller than they are** (one of the most common issues flagged by reviewers). Example (simulated data, 3 experiments × 3 images × 6 cells):

| Unit | n | Dunnett p (treatment vs control) |
|---|---|---|
| Cell | 54 | 0.069 |
| Experiment mean | 3 | **0.62** |

**Recommendation:** in publications, run statistics on **means of independent experiments** (at least 3); individual cells can still be shown as points in the plot. The program warns when you test at the cell level.

Dunnett p values are computed by numerical integration; the program uses a fixed seed, so **the same data always give the same p**.

Save: plot as PNG (600 dpi), PDF, SVG; statistics as .txt.

---

## 11. Fiji bridge and method validation

**Fiji menu:**

### 11.1 Verify with Fiji (⌘⇧F)
Has **Fiji's own Measure engine** measure the selected cells and background boxes **in the background** (no Fiji window, ~5 seconds) and shows the results side by side with the program's. When the image is added to the results table, the outcome is written to the **Fiji_check** column (e.g. *OK (1.54p99, max diff 3.3e-07 %)*). Changing the selection, boxes or boundaries invalidates the earlier check.

### 11.2 Open in Fiji
Opens Fiji with its interface: image, scale, all ROIs in the ROI Manager, Measure results. Files: `Documents/ICC CTCF Olcer/Fiji/<image name>/`.

### 11.3 Compare with manually traced ROIs (method validation)
To quantify how close the automatic boundaries are to manual tracing (recommended for papers):

1. In Fiji, open the FITC image. Trace a cell with the **Polygon** or **Freehand** tool → **T** (add to ROI Manager). Repeat for all cells.
2. ROI Manager ▸ **More » ▸ Save…** → `manual_RoiSet_<image>.zip`
3. In the program, open the same image (and its DAPI) → **Fiji ▸ Compare with ROIs traced manually…** → choose the zip.
4. Each manual ROI is matched to the automatic cell it overlaps most: area difference, CTCF difference, **Dice** and IoU (boundary overlap; 1 = perfect).
5. **➕ Add to validation table.** Repeat for 3–5 images (separate + touching cells, different conditions).
6. **Fiji ▸ Method validation table and Bland–Altman…:** scatter plot + Bland–Altman (percentage difference), mean difference (bias), 95% limits of agreement, Pearson r, Lin's CCC, Dice.

**Recommendation:** ≥ 30 cells, ≥ 3 images. Optionally re-trace the same cells a few hours later (intra-observer variability): if the automatic–manual difference is not larger than the manual–manual difference, the method is at least as reliable as manual measurement.

---

## 12. Warnings: what they mean and what to do

### 12.1 Opening images
| Warning | Meaning | What to do |
|---|---|---|
| *The image appears to have been processed with software (Adobe Photoshop…)* | The file was re-saved by an image editor | Use the raw microscope output |
| *No camera information (EXIF)* | Merged or re-saved image | Use the raw single-channel FITC |
| *… looks like a DAPI image, open it as DAPI?* | File colour does not match the button | Usually **Yes** |
| *The FITC and DAPI images differ in size; DAPI was not used* | The two files are not the same acquisition | Open the correct DAPI |
| *New FITC opened; open the DAPI of the same field* | The previous field's DAPI was removed | Open the new field's DAPI |

### 12.2 Calibration and cell separation
| Warning | Meaning | What to do |
|---|---|---|
| 🔴 *The scale bar value could not be read; 20 µm was assumed* | Label not read | Type the value from the image into the **Scale bar** box |
| *No scale bar found — pixel units* | No scale bar | Area in pixel²; comparisons valid only at identical magnification |
| 🔴 *Cell separation: shape only — N touching cell pairs* | No DAPI, touching cells present | Open the DAPI of the same field |
| 🔴 *This DAPI image does not seem to belong to the same field* | Most nuclei lie outside the cells | Open the correct DAPI |
| *Re-analysed: previous manual edits were reset* | Scale etc. changed | Redo the edits |

### 12.3 Background
| Warning | Meaning | What to do |
|---|---|---|
| ℹ️ *All pixels in the boxes are 0* | Camera black level clipped; CTCF = IntDen | Fine if all images used the same settings |
| ⚠️ *Some boxes may contain signal/debris* | Bright pixels in a box | Drag the box to a clean area |
| 🔴 *No background box — CTCF cannot be computed* | No room for boxes / no box in Manual mode | Reduce the box size or add boxes manually |
| ⚠️ *The box overlaps a cell* | Boxes cannot be placed on cells | Place it a little further away |

### 12.4 Measurement table
| Situation | Meaning | What to do |
|---|---|---|
| **Saturated px > 0** | Pixels at the camera's maximum → CTCF is **underestimated** | Re-acquire with lower exposure, or exclude that cell |

### 12.5 Statistics
| Warning | Meaning | What to do |
|---|---|---|
| ⚠️ *Each cell was counted as a replicate (risk of pseudoreplication)* | n = number of cells | Use the **Experiment mean** unit for publication |
| ⚠️ *Different objectives are mixed (20×, 40×)* | Groups acquired at different magnifications | Compare only images from the same objective |
| ⚠️ *Zero within-group variability* | Identical values repeat (same image added twice?) | Check the table; the test is not reliable |
| ℹ️ *2 experiments per group: low statistical power* | n < 3 | At least 3 independent experiments |
| *Statistics require at least … per group* | Not enough data | Add more images/experiments |
| ⚠️ *Few cells: r and CCC are meaningless* (validation) | Too few cells for Bland–Altman | ≥ 30 cells, ≥ 3 images |

### 12.6 Batch measurement and Fiji
| Warning | Meaning | What to do |
|---|---|---|
| 🟠 *no DAPI (best candidate …%)* | No overlapping DAPI found | Put the correct DAPI in the folder, or accept shape-only separation |
| ⚪ *skipped: …* | See [8.2](#82-fitcdapi-pairing) | — |
| *Fiji was not found* | Fiji not installed / elsewhere | Fiji ▸ Choose Fiji location… |
| ⚠️ *Difference found* (Fiji verification) | Program and Fiji differ (not expected) | Check calibration; please report the issue |

---

## 13. For your paper: methods text and citation

**Example methods text (adapt to your settings):**

> Corrected total cell fluorescence (CTCF) was quantified as CTCF = integrated density − (cell area × mean background fluorescence) (McCloy et al., 2014) using ICC CTCF Ölçer v2.0.0 (Balcan, 2026; https://doi.org/10.5281/zenodo.23860021), an open-source tool whose measurements are identical to ImageJ/Fiji for the same regions of interest (verified with Fiji 1.54p). FITC fluorescence was measured on the green channel of unprocessed Olympus DP74 images (40× objective, 0.145 µm/pixel; calibration read from the embedded scale bar). Cells were segmented from the FITC channel (Li threshold) and touching cells were separated by watershed seeded with DAPI-stained nuclei. Background was the mean of three 50 × 50 pixel cell-free regions per field. Cells touching the image border were excluded. Automatic boundaries were compared with manual Fiji tracing in n = … cells from … images (Bland–Altman bias …%, 95% limits of agreement … to …%; mean Dice …). Statistics were performed on the means of N = … independent experiments using one-way ANOVA followed by Dunnett's test versus control.

The **Methods** sheet in Excel and the *App_version, Nucleus_method, Scale_source, BG_box_px, BG_n, Selection, Manual_edits, Fiji_check* columns in the **Cells** sheet contain everything needed to fill in this text.

**Citation (reference list):**

> Balcan E. (2026). *ICC CTCF Ölçer: per-cell corrected total cell fluorescence (CTCF) quantification for immunocytochemistry images* (Version 2.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.23860021

| DOI | When to use |
|---|---|
| **10.5281/zenodo.23860021** | **This version** (2.0.0) as used in your paper — recommended for reproducibility |
| 10.5281/zenodo.23860020 | **All versions** of the program (concept DOI; always resolves to the newest version) |

The version used is recorded in the **App_version** column in Excel; if you measured with a newer version, take that version's DOI from the Zenodo page (https://doi.org/10.5281/zenodo.23860020 → "Versions").

For the CTCF method: McCloy RA, Rogers S, Caldon CE, Lorca T, Castro A, Burgess A. (2014). Partial inhibition of Cdk1 in G2 phase overrides the SAC and decouples mitotic events. *Cell Cycle* 13(9):1400–1412. https://doi.org/10.4161/cc.28401

---

## 14. Troubleshooting

| Problem | Solution |
|---|---|
| Mac: *"unidentified developer"* | Right-click the app ▸ Open ▸ Open (once) |
| Mac: *"is damaged and can't be opened"* | Terminal: `xattr -cr "/Applications/ICC CTCF Ölçer.app"` |
| Mac (Apple Silicon, Monterey): does not open | Update macOS to 12.3 or later |
| Windows: *"Windows protected your PC"* | More info ▸ Run anyway |
| Slow first start | A font cache is built on first launch (once, ~10–30 s) |
| Wrong cell count | Did you use the right button (FITC/DAPI)? Is the DAPI from the same field? Correct boundaries as in [Section 7](#7-editing-cell-boundaries) |
| A dense cluster counted as one "cell" | **Split** tool |
| Nuclei (magenta outlines) look wrong | Switch to **Display: DAPI** and check; is the DAPI from the same field? |
| Values differ slightly from v1 | v2 uses different nucleus detection (Nucleus_method). Use one version throughout a study |
| Excel cannot be saved | If the file is open in Excel, close it and retry |
| The program closed / crashed | Reopen → *"Continue where you left off?"* → Yes (autosave) |
| Fiji bridge does not work | Fiji ▸ Choose Fiji location… ; open and close Fiji once yourself (first-run updates) |
| Interface in the wrong language | View ▸ Language / Dil, then restart |

Questions and bug reports: https://github.com/erdal-b-dot/icc-ctcf-olcer/issues

---

## 15. Technical details

**Measurement definitions (same as ImageJ):**
- Area = number of pixels × (µm/pixel)²
- IntDen = Area × Mean (calibrated units); RawIntDen = sum of pixel values
- StdDev = sample standard deviation (n − 1)
- ROI rule: a pixel belongs to the ROI if its centre lies inside the polygon
- CTCF = IntDen − Area × BG_Mean; CTCF_per_Area = Mean − BG_Mean

**Calibration:** the length of the cellSens scale bar (white box, lower right) is measured in pixels; the number below it is read with digit templates (all 301 images of the development data set, Olympus DP74/cellSens, read correctly: 157 × 50 µm, 144 × 20 µm). Objective = camera pixel size (DP74: 5.86 µm) ÷ µm/pixel.

**Cell segmentation:** FITC (G channel) Gaussian smoothing → Li threshold → closing, hole filling, small-object removal (< 50 µm²) → watershed seeded with DAPI nuclei (distance transform if no DAPI).

**Nucleus detection (Nucleus_method):**
| Method | Version | Description |
|---|---|---|
| `otsu` | v1.0.0 | Otsu threshold (also includes the dim DAPI halo) |
| `bright_core` | early v2 | Upper threshold of 3-class Otsu (misses dim nuclei) |
| **`local`** | **v2.0.0 default** | Otsu mask → watershed from smoothed DAPI maxima → each nucleus trimmed at half of its own peak intensity |

**Validation results:**
- Identical to Fiji 1.54p for the same ROIs: Area/Mean/StdDev/Min/Max/IntDen/RawIntDen (5 ROIs in a 40× image; 54 ROIs in a 20× image with non-zero background; largest difference < 0.00001 %).
- Manual tracing (1 image, 2 touching cells — preliminary): Dice 0.943 / 0.938; CTCF difference +2.3 % / +3.7 %.
- Dense clusters at 20×: 47 nuclei, 51 cells detected.

**Program files:** `core.py` (measurement), `batch.py` (batch), `report.py` (Excel, plots, statistics), `fiji.py` (Fiji bridge), `desktop.py` (interface), `i18n.py` + `locales/` (languages), `tests/test_core.py` (validation tests).
