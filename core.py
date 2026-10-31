"""ICC CTCF – görüntü işleme ve ölçüm çekirdeği (arayüzden bağımsız, test edilebilir).

CTCF = Integrated Density − (Area of selected cell × Mean fluorescence of background)
(McCloy et al. 2014, Cell Cycle; theolb.readthedocs.io ImageJ protokolü)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation, feature

# Olympus DP74 fiziksel piksel boyutu (µm). 1920×1200 çıktıda efektif piksel ≈ 5.86 µm.
CAMERA_PIXEL_UM = {"Olympus DP74": 5.86}
STANDARD_OBJECTIVES = [4, 10, 20, 40, 60, 63, 100]


# --------------------------------------------------------------------------- I/O
def load_image(file) -> tuple[np.ndarray, dict]:
    """Görüntüyü bit derinliğini koruyarak yükler. (H,W) veya (H,W,3) döner."""
    name = getattr(file, "name", str(file)).lower()
    meta = {}
    if name.endswith((".tif", ".tiff")):
        import tifffile
        arr = tifffile.imread(file)
        if arr.ndim == 3 and arr.shape[0] in (3, 4) and arr.shape[-1] not in (3, 4):
            arr = np.moveaxis(arr, 0, -1)
    else:
        im = Image.open(file)
        exif = im.getexif()
        meta["make"] = exif.get(271, "")
        meta["model"] = exif.get(272, "")
        meta["software"] = exif.get(305, "")
        arr = np.asarray(im.convert("RGB") if im.mode not in ("L", "I;16", "I") else im)
    if arr.ndim == 3:
        arr = arr[..., :3]
    meta["dtype"] = str(arr.dtype)
    meta["max_value"] = 255 if arr.dtype == np.uint8 else int(np.iinfo(arr.dtype).max) if arr.dtype.kind == "u" else float(arr.max())
    return arr, meta


CHANNEL_MODES = {
    "Yeşil kanal (G) – FITC için önerilen": "G",
    "Kırmızı kanal (R)": "R",
    "Mavi kanal (B)": "B",
    "ImageJ RGB→8-bit (R+G+B)/3": "MEAN",
    "Ağırlıklı luminans (0.299R+0.587G+0.114B)": "LUMA",
}


def get_channel(arr: np.ndarray, mode: str) -> np.ndarray:
    """Ölçülecek tek kanal yoğunluk görüntüsünü float64 olarak döndürür."""
    if arr.ndim == 2:
        return arr.astype(np.float64)
    a = arr.astype(np.float64)
    if mode == "R":
        return a[..., 0]
    if mode == "G":
        return a[..., 1]
    if mode == "B":
        return a[..., 2]
    if mode == "MEAN":
        return a.mean(axis=-1)
    if mode == "LUMA":
        return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    raise ValueError(mode)


# ------------------------------------------------------------------ Kalibrasyon
@dataclass
class ScaleBar:
    found: bool
    bbox: tuple[int, int, int, int] | None = None  # y0, y1, x0, x1 (dışlanacak bölge)
    bar_px: int | None = None


def detect_scale_bar(arr: np.ndarray) -> ScaleBar:
    """Sağ alt köşedeki beyaz kutu içinde koyu ölçek çizgisini bulur (Olympus cellSens stili)."""
    if arr.ndim != 3:
        return ScaleBar(False)
    h, w = arr.shape[:2]
    y0, x0 = int(h * 0.80), int(w * 0.70)
    sub = arr[y0:, x0:].astype(int)
    white = (sub.min(axis=-1) > 200)
    if white.sum() < 500:
        return ScaleBar(False)
    lab = measure.label(white)
    reg = max(measure.regionprops(lab), key=lambda r: r.area)
    by0, bx0, by1, bx1 = reg.bbox
    box = sub[by0:by1, bx0:bx1].sum(axis=-1)
    best = 0
    for row in box:
        dark = row < 200
        # en uzun kesintisiz koyu dizi
        runs = np.diff(np.concatenate([[0], dark.view(np.int8), [0]]))
        starts, ends = np.where(runs == 1)[0], np.where(runs == -1)[0]
        if len(starts):
            best = max(best, int((ends - starts).max()))
    pad = 4
    bbox = (max(y0 + by0 - pad, 0), min(y0 + by1 + pad, h), max(x0 + bx0 - pad, 0), min(x0 + bx1 + pad, w))
    return ScaleBar(best > 20, bbox, best if best > 20 else None)


def estimate_objective(um_per_px: float, camera_pixel_um: float = 5.86) -> tuple[int, float]:
    """µm/piksel'den objektif büyütmesini tahmin eder (adaptör 1× varsayımıyla)."""
    raw = camera_pixel_um / um_per_px
    nearest = min(STANDARD_OBJECTIVES, key=lambda o: abs(o - raw))
    return nearest, raw


# ---------------------------------------------------------------- Segmentasyon
THRESH = {"Otsu": filters.threshold_otsu, "Li": filters.threshold_li,
          "Triangle": filters.threshold_triangle, "Mean": filters.threshold_mean}


def segment_nuclei(dapi: np.ndarray, um_per_px: float, exclude: np.ndarray,
                   min_area_um2: float = 15.0, nucleus_diam_um: float = 10.0,
                   method: str = "Otsu", split: bool = True, bright_core: bool = False) -> np.ndarray:
    """Çekirdek etiketleri.

    bright_core=False (v1.0.0): Otsu eşiği; DAPI çevresindeki loş mavi haleyi de çekirdeğe katar.
    bright_core=True  (v2): yalnızca parlak çekirdek gövdesi (3 sınıflı Otsu'nun üst eşiği) ve
    yumuşatılmış DAPI yoğunluk tepelerinden ayırma — değen çekirdekleri daha doğru böler.
    """
    sm = filters.gaussian(dapi, sigma=max(1.0, 0.5 / um_per_px), preserve_range=True)
    sm[exclude] = 0
    if bright_core:
        th = filters.threshold_multiotsu(sm[~exclude], classes=3)[-1]
        mask = sm > th
        mask = morphology.remove_small_objects(mask, max_size=max(1, int(min_area_um2 / um_per_px ** 2)))
        mask = ndi.binary_fill_holes(mask)
        if not split:
            return measure.label(mask)
        smooth = filters.gaussian(dapi, sigma=0.3 * nucleus_diam_um / um_per_px, preserve_range=True)
        peaks = feature.peak_local_max(smooth, min_distance=max(3, int(0.4 * nucleus_diam_um / um_per_px)),
                                       labels=measure.label(mask), exclude_border=False)
        markers = np.zeros(mask.shape, int)
        markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
        return segmentation.watershed(-smooth, markers, mask=mask)
    th = THRESH[method](sm[~exclude])
    mask = sm > th
    mask = morphology.remove_small_objects(mask, max_size=max(1, int(min_area_um2 / um_per_px ** 2)))
    mask = ndi.binary_fill_holes(mask)
    if not split:
        return measure.label(mask)
    dist = ndi.distance_transform_edt(mask)
    min_d = max(3, int(0.6 * nucleus_diam_um / 2 / um_per_px))
    peaks = feature.peak_local_max(dist, min_distance=min_d, labels=measure.label(mask), exclude_border=False)
    markers = np.zeros(mask.shape, int)
    markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
    return segmentation.watershed(-dist, markers, mask=mask)


def segment_cells(fitc: np.ndarray, um_per_px: float, exclude: np.ndarray,
                  nuclei: np.ndarray | None = None, method: str = "Li",
                  thresh_factor: float = 1.0, min_area_um2: float = 50.0,
                  cell_diam_um: float = 20.0) -> tuple[np.ndarray, float]:
    """FITC kanalından hücre maskesi; çekirdekler varsa watershed tohumu olarak kullanılır."""
    sm = filters.gaussian(fitc, sigma=max(1.0, 0.4 / um_per_px), preserve_range=True)
    sm[exclude] = 0
    th = THRESH[method](sm[~exclude]) * thresh_factor
    mask = sm > th
    mask = ndi.binary_closing(mask, morphology.disk(2))
    mask = ndi.binary_fill_holes(mask)
    mask = morphology.remove_small_objects(mask, max_size=max(1, int(min_area_um2 / um_per_px ** 2)))
    mask &= ~exclude

    if nuclei is not None and nuclei.max() > 0:
        markers = nuclei * mask  # yalnızca hücre maskesi içindeki çekirdekler
        markers = morphology.remove_small_objects(markers, max_size=5)
        # çekirdeği olmayan floresan bölgelere de birer tohum ver
        comp = measure.label(mask)
        nxt = markers.max() + 1
        for r in measure.regionprops(comp):
            if markers[comp == r.label].max() == 0:
                markers[tuple(r.coords[len(r.coords) // 2])] = nxt
                nxt += 1
        labels = segmentation.watershed(-sm, markers, mask=mask)
    else:
        dist = ndi.distance_transform_edt(mask)
        min_d = max(5, int(0.5 * cell_diam_um / 2 / um_per_px))
        peaks = feature.peak_local_max(dist, min_distance=min_d, labels=measure.label(mask), exclude_border=False)
        markers = np.zeros(mask.shape, int)
        markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
        labels = segmentation.watershed(-dist, markers, mask=mask)
    labels, _, _ = segmentation.relabel_sequential(labels)
    return labels, float(th)


# --------------------------------------------------------------- Background
def auto_background_boxes(fitc: np.ndarray, cell_mask: np.ndarray, exclude: np.ndarray,
                          size: int = 50, n: int = 3, margin_px: int = 40,
                          signal_thresh: float | None = None) -> list[tuple[int, int, int, int]]:
    """Hücre dışı, hücrelere yakın ve birbirinden ayrık n adet size×size kutu seçer.

    signal_thresh verilirse bu değerin üstündeki her piksel (debris, zayıf hücre kenarı)
    çevresiyle birlikte yasaklanır. Döndürülen kutu formatı: (y0, x0, y1, x1)."""
    h, w = fitc.shape
    # dilatasyon yerine mesafe dönüşümü (büyük yarıçaplarda çok daha hızlı)
    forbidden = (ndi.distance_transform_edt(~cell_mask) <= margin_px) | exclude
    if signal_thresh is not None:
        sm = filters.gaussian(fitc, sigma=1, preserve_range=True)
        forbidden |= ndi.distance_transform_edt(~(sm > signal_thresh)) <= 5
    # kutu tamamen izinli alanda mı? → integral image ile hızlı kontrol
    ii = np.pad(forbidden.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    ys = np.arange(0, h - size, max(4, size // 4))
    xs = np.arange(0, w - size, max(4, size // 4))
    Y, X = np.meshgrid(ys, xs, indexing="ij")
    bad = ii[Y + size, X + size] - ii[Y, X + size] - ii[Y + size, X] + ii[Y, X]
    cand = np.stack([Y[bad == 0], X[bad == 0]], axis=1)
    if len(cand) == 0:
        return []
    # hücrelere yakınlık: lokal background tercih edilir
    if cell_mask.any():
        dist = ndi.distance_transform_edt(~cell_mask)
        d = dist[cand[:, 0] + size // 2, cand[:, 1] + size // 2]
    else:
        d = np.zeros(len(cand))
    order = np.argsort(d)
    chosen: list[tuple[int, int, int, int]] = []
    for i in order:
        y, x = cand[i]
        # kutular hem çakışmasın hem de etrafa dağılsın (≥ 2×size mesafe)
        if all(abs(y - c[0]) >= 2 * size or abs(x - c[1]) >= 2 * size for c in chosen):
            chosen.append((int(y), int(x), int(y + size), int(x + size)))
        if len(chosen) == n:
            break
    return chosen


def box_at(cy: int, cx: int, size: int, shape) -> tuple[int, int, int, int]:
    h, w = shape
    y0 = int(np.clip(cy - size // 2, 0, h - size))
    x0 = int(np.clip(cx - size // 2, 0, w - size))
    return (y0, x0, y0 + size, x0 + size)


# ------------------------------------------------------------------- Ölçüm
def _stats(px: np.ndarray, px_area: float, sat_value) -> dict:
    n = px.size
    mean = float(px.mean())
    return {
        "Area_px": int(n),
        "Area": n * px_area,
        "Mean": mean,
        "StdDev": float(px.std(ddof=1)) if n > 1 else 0.0,  # ImageJ örneklem SD kullanır
        "Min": float(px.min()),
        "Max": float(px.max()),
        "IntDen": n * px_area * mean,  # ImageJ: Area × Mean (kalibre birimde)
        "RawIntDen": float(px.sum()),  # ImageJ: piksel değerleri toplamı
        "Saturated_px": int((px >= sat_value).sum()),
    }


def measure_backgrounds(img: np.ndarray, boxes, px_area: float, sat_value) -> pd.DataFrame:
    rows = []
    for i, (y0, x0, y1, x1) in enumerate(boxes, 1):
        s = _stats(img[y0:y1, x0:x1].ravel(), px_area, sat_value)
        rows.append({"BG": i, "y0": y0, "x0": x0, "y1": y1, "x1": x1, **s})
    return pd.DataFrame(rows)


def measure_cells(img: np.ndarray, labels: np.ndarray, cell_ids, bg_mean: float,
                  um_per_px: float | None, sat_value, nuclei: np.ndarray | None = None) -> pd.DataFrame:
    px_area = um_per_px ** 2 if um_per_px else 1.0
    rows = []
    for cid in cell_ids:
        m = labels == cid
        if not m.any():
            continue
        s = _stats(img[m], px_area, sat_value)
        ctcf = s["IntDen"] - s["Area"] * bg_mean
        props = measure.regionprops(m.astype(np.uint8))[0]
        row = {"Cell": int(cid), **s,
               "BG_Mean": bg_mean,
               "CTCF": ctcf,
               "CTCF_per_Area": ctcf / s["Area"],  # = Mean − BG_Mean
               "Centroid_x": round(props.centroid[1], 1), "Centroid_y": round(props.centroid[0], 1)}
        if nuclei is not None:
            row["Nuclei_in_cell"] = int(len(np.setdiff1d(np.unique(nuclei[m]), [0])))
        rows.append(row)
    df = pd.DataFrame(rows)
    if len(df):
        df.insert(1, "Area_unit", "µm²" if um_per_px else "px²")
    return df


# ------------------------------------------------------- Tek adımda tüm akış
@dataclass
class Settings:
    """Varsayılanlar v1.0.0 Streamlit arayüzüyle aynıdır (Fiji doğrulaması bu ayarlarla yapıldı)."""
    channel: str = "G"
    bar_um: float = 20.0
    bar_px: int | None = None          # None → ölçek çubuğundan otomatik
    camera_pixel_um: float = 5.86
    thresh_method: str = "Li"
    thresh_factor: float = 1.0
    min_cell_um2: float = 50.0
    nuc_split: bool = True
    nuc_bright_core: bool = True       # v2 varsayılanı; False = v1.0.0 çekirdek algılaması
    nuc_diam_um: float = 10.0
    min_nuc_um2: float = 15.0
    bg_size: int = 50
    bg_n: int = 3


@dataclass
class Analysis:
    fitc_arr: np.ndarray
    meta: dict
    scale_bar: ScaleBar
    um_per_px: float | None
    exclude: np.ndarray
    fitc_ch: np.ndarray
    dapi_ch: np.ndarray | None
    nuclei: np.ndarray | None
    labels: np.ndarray
    threshold: float
    cell_ids: list[int]
    touching: list[tuple[int, int]] = field(default_factory=list)
    camera_pixel_um: float = 5.86

    @property
    def segmentation_mode(self) -> str:
        return "DAPI nuclei" if self.nuclei is not None else "Shape only"

    @property
    def objective(self) -> tuple[int, float] | None:
        return estimate_objective(self.um_per_px, self.camera_pixel_um) if self.um_per_px else None


def analyze(fitc_arr: np.ndarray, meta: dict, dapi_arr: np.ndarray | None = None,
            s: Settings | None = None) -> Analysis:
    """Kalibrasyon → çekirdek → hücre segmentasyonu. Arayüzler (Streamlit / masaüstü) bunu çağırır."""
    s = s or Settings()
    sb = detect_scale_bar(fitc_arr)
    bar_px = s.bar_px if s.bar_px is not None else sb.bar_px
    upp = s.bar_um / bar_px if bar_px else None
    exclude = np.zeros(fitc_arr.shape[:2], bool)
    if sb.found:
        y0, y1, x0, x1 = sb.bbox
        exclude[y0:y1, x0:x1] = True
    fitc_ch = get_channel(fitc_arr, s.channel)
    dapi_ch = get_channel(dapi_arr, "B" if dapi_arr.ndim == 3 else "G") if dapi_arr is not None else None
    nuclei = None
    if dapi_ch is not None:
        nuclei = segment_nuclei(dapi_ch, upp or 1.0, exclude, s.min_nuc_um2, s.nuc_diam_um, split=s.nuc_split,
                                bright_core=s.nuc_bright_core)
    labels, th = segment_cells(fitc_ch, upp or 1.0, exclude, nuclei, s.thresh_method, s.thresh_factor,
                               s.min_cell_um2)
    ids = [int(i) for i in np.setdiff1d(np.unique(labels), [0])]
    a = Analysis(fitc_arr, meta, sb, upp, exclude, fitc_ch, dapi_ch, nuclei, labels, th, ids,
                 touching_pairs(labels), s.camera_pixel_um)
    return a


def background_and_measure(a: Analysis, cell_ids, s: Settings | None = None, boxes=None):
    """Background kutuları (verilmezse otomatik) + hücre ölçümü → (cells_df, bg_df, boxes)."""
    s = s or Settings()
    if boxes is None:
        boxes = auto_background_boxes(a.fitc_ch, a.labels > 0, a.exclude, s.bg_size, s.bg_n,
                                      signal_thresh=a.threshold * 0.3)
    sat = a.meta["max_value"]
    bg = measure_backgrounds(a.fitc_ch, boxes, (a.um_per_px or 1) ** 2, sat)
    bg_mean = float(bg["Mean"].mean()) if len(bg) else 0.0
    cells = measure_cells(a.fitc_ch, a.labels, cell_ids, bg_mean, a.um_per_px, sat, a.nuclei)
    return cells, bg, boxes


# -------------------------------------------------------------- Görselleştirme
def to_display(arr: np.ndarray, gain: float = 1.0) -> np.ndarray:
    a = arr.astype(np.float64)
    a = a / (65535.0 if arr.dtype == np.uint16 else 255.0) * 255.0 * gain
    a = np.clip(a, 0, 255).astype(np.uint8)
    return np.stack([a] * 3, -1) if a.ndim == 2 else a


def overlay(display_rgb: np.ndarray, labels: np.ndarray, selected: set[int],
            bg_boxes, nuclei: np.ndarray | None = None, font_scale: int = 2,
            nucleus_color=(0, 160, 255), nucleus_width: int = 0) -> Image.Image:
    from PIL import ImageDraw, ImageFont
    out = display_rgb.copy()
    if nuclei is not None and nuclei.max() > 0:
        nb = segmentation.find_boundaries(nuclei, mode="inner")
        if nucleus_width:
            nb = ndi.binary_dilation(nb, morphology.disk(nucleus_width))
        out[nb] = nucleus_color
    for cid in np.setdiff1d(np.unique(labels), [0]):
        b = segmentation.find_boundaries(labels == cid, mode="inner")
        b = ndi.binary_dilation(b, morphology.disk(1))
        out[b] = (255, 220, 0) if cid in selected else (150, 150, 150)
    im = Image.fromarray(out)
    dr = ImageDraw.Draw(im)
    font = None
    for path in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS
                 "C:/Windows/Fonts/arialbd.ttf",                        # Windows
                 "DejaVuSans-Bold.ttf"):                                # Linux
        try:
            font = ImageFont.truetype(path, 14 * font_scale)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default(size=14 * font_scale)  # Pillow ≥10.1
    for r in measure.regionprops(labels):
        y, x = r.centroid
        col = (255, 220, 0) if r.label in selected else (200, 200, 200)
        dr.text((x, y), str(r.label), fill=col, font=font, anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))
    for i, (y0, x0, y1, x1) in enumerate(bg_boxes, 1):
        dr.rectangle([x0, y0, x1, y1], outline=(255, 60, 60), width=3)
        dr.text((x0, y0 - 4), f"BG{i}", fill=(255, 60, 60), font=font, anchor="lb")
    return im


# ------------------------------------------------------------ ImageJ aktarımı
def imagej_export_zip(channel: np.ndarray, labels: np.ndarray, cell_ids, bg_boxes, base: str) -> bytes:
    """ImageJ/Fiji karşılaştırması için zip: ölçülen kanal (TIFF) + RoiSet.zip (hücre poligonları + BG kutuları).

    Fiji'de: TIFF'i aç → ROI Manager → Open RoiSet.zip → Measure. Değerler bu uygulamayla aynı olmalı."""
    import io
    import zipfile
    import roifile
    import tifffile

    rois = []
    for cid in cell_ids:
        m = labels == cid
        # pikselleri dışarıdan saran kontur: bulunan poligonun içi = maskenin pikselleri
        cont = measure.find_contours(np.pad(m, 1).astype(float), 0.5)
        cont = max(cont, key=len) - 1 + 0.5  # pad düzeltmesi, piksel merkezi → köşe koordinatı
        xy = np.fliplr(cont).astype(np.float32)
        r = roifile.ImagejRoi.frompoints(xy)
        r.roitype = roifile.ROI_TYPE.POLYGON
        r.name = f"Cell_{cid}"
        rois.append(r)
    for i, (y0, x0, y1, x1) in enumerate(bg_boxes, 1):
        r = roifile.ImagejRoi(roitype=roifile.ROI_TYPE.RECT, top=y0, left=x0, bottom=y1, right=x1, name=f"BG_{i}")
        rois.append(r)

    roi_buf = io.BytesIO()
    with zipfile.ZipFile(roi_buf, "w") as zf:
        for r in rois:
            zf.writestr(f"{r.name}.roi", r.tobytes())
    tif_buf = io.BytesIO()
    ch = channel
    ch = ch.astype(np.uint8) if np.allclose(ch, np.round(ch)) and ch.max() <= 255 else ch.astype(np.float32)
    tifffile.imwrite(tif_buf, ch, imagej=True)

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zf:
        zf.writestr(f"{base}_measured_channel.tif", tif_buf.getvalue())
        zf.writestr(f"{base}_RoiSet.zip", roi_buf.getvalue())
        zf.writestr("NASIL_KULLANILIR.txt",
                    "1. Fiji'de *_measured_channel.tif dosyasini acin (uygulamanin olctugu kanal).\n"
                    "2. Analyze > Set Measurements: Area, Mean, Std.Dev, Min&Max, Integrated Density isaretli.\n"
                    "3. Analyze > Set Scale: Distance in pixels=<cubuk px>, Known distance=20, Unit=um\n"
                    "4. Analyze > Tools > ROI Manager > More > Open... > *_RoiSet.zip\n"
                    "5. ROI Manager'da tumunu secin (Cmd+A) > Measure.\n"
                    "6. CTCF = IntDen - Area x ortalama(BG Mean).\n")
    return out.getvalue()


# --------------------------------------------------- Ayırma modu / temas kontrolü
def touching_pairs(labels: np.ndarray) -> list[tuple[int, int]]:
    """Sınırı paylaşan (birbirine değen) hücre çiftleri."""
    pairs = set()
    for a, b in ((labels[:, :-1], labels[:, 1:]), (labels[:-1, :], labels[1:, :])):
        m = (a != b) & (a > 0) & (b > 0)
        for p, q in zip(a[m], b[m]):
            pairs.add((int(min(p, q)), int(max(p, q))))
    return sorted(pairs)


# ---------------------------------------------- Elle çizilmiş ROI karşılaştırması
def read_imagej_rois(data: bytes, shape) -> list[tuple[str, np.ndarray]]:
    """ImageJ RoiSet.zip (veya tek .roi) → [(ad, maske)]. ImageJ kuralı: piksel merkezi poligon içindeyse dahil."""
    import io
    import zipfile
    import roifile
    from skimage.draw import polygon2mask

    blobs = []
    if data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            blobs = [(n.rsplit(".", 1)[0], zf.read(n)) for n in zf.namelist() if n.endswith(".roi")]
    else:
        blobs = [("ROI_1", data)]
    out = []
    for name, b in blobs:
        r = roifile.ImagejRoi.frombytes(b)
        name = r.name or name
        if r.roitype == roifile.ROI_TYPE.RECT:
            m = np.zeros(shape, bool)
            m[r.top:r.bottom, r.left:r.right] = True
        elif r.roitype == roifile.ROI_TYPE.OVAL:
            from skimage.draw import ellipse
            m = np.zeros(shape, bool)
            cy, cx = (r.top + r.bottom) / 2 - 0.5, (r.left + r.right) / 2 - 0.5
            rr, cc = ellipse(cy, cx, (r.bottom - r.top) / 2, (r.right - r.left) / 2, shape=shape)
            m[rr, cc] = True
        else:
            xy = r.coordinates()
            m = polygon2mask(shape, np.fliplr(xy) - 0.5)
        out.append((name, m))
    return out


def compare_manual(img: np.ndarray, labels: np.ndarray, manual: list[tuple[str, np.ndarray]],
                   bg_mean: float, um_per_px: float | None) -> pd.DataFrame:
    """Her elle çizilmiş ROI'yi en çok örtüşen otomatik hücreyle eşleştirir; alan, CTCF ve Dice karşılaştırır."""
    px_area = um_per_px ** 2 if um_per_px else 1.0
    rows = []
    for name, m in manual:
        if not m.any():
            continue
        ids, counts = np.unique(labels[m], return_counts=True)
        keep = ids > 0
        ids, counts = ids[keep], counts[keep]
        man_area = m.sum() * px_area
        man_ctcf = man_area * img[m].mean() - man_area * bg_mean
        row = {"Manual_ROI": name, "Manual_Area": man_area, "Manual_Mean": img[m].mean(), "Manual_CTCF": man_ctcf}
        if len(ids):
            cid = int(ids[np.argmax(counts)])
            a = labels == cid
            auto_area = a.sum() * px_area
            auto_ctcf = auto_area * img[a].mean() - auto_area * bg_mean
            inter = (a & m).sum()
            row.update({"Auto_Cell": cid, "Auto_Area": auto_area, "Auto_Mean": img[a].mean(), "Auto_CTCF": auto_ctcf,
                        "Area_diff_%": 100 * (auto_area - man_area) / man_area,
                        "CTCF_diff_%": 100 * (auto_ctcf - man_ctcf) / man_ctcf if man_ctcf else np.nan,
                        "Dice": 2 * inter / (a.sum() + m.sum()),
                        "IoU": inter / (a | m).sum()})
        rows.append(row)
    return pd.DataFrame(rows)
