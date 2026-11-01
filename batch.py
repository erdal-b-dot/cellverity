"""Klasör işleme: FITC/DAPI çiftlerini bulma ve toplu ölçüm (arayüzden bağımsız).

Ardışık dosya numarası her zaman aynı alan demek değildir (ZÜBEYDE/ICC: 292+293, 394+395 farklı
alanlar). Bu yüzden her FITC için aynı klasördeki yakın numaralı DAPI adayları arasından, çekirdek
maskesinin hücre maskesiyle en çok örtüştüğü seçilir.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from skimage import filters

import core

IMAGE_EXT = (".jpg", ".jpeg", ".tif", ".tiff", ".png")
MIN_OVERLAP = 0.5      # çekirdek alanının en az yarısı hücre maskesi içinde olmalı
NEIGHBOR = 3           # dosya numarasında ±3 içindeki DAPI'ler aday


def guess_kind(arr: np.ndarray) -> str | None:
    """'DAPI' / 'FITC' / None. Parlak %1 pikselde mavi/kırmızı oranı (DP74'te DAPI turkuaz görünür;
    ZÜBEYDE/ICC'deki 282 tek kanal görüntüde FITC ≤ 0.79, DAPI ≥ 1.47)."""
    if arr.ndim != 3:
        return None
    a = arr.reshape(-1, 3)[::7].astype(float)
    mx = a.max(axis=1)
    r, _, b = a[mx >= np.percentile(mx, 99)].mean(axis=0)
    ratio = b / (r + 1)
    if ratio > 1.2:
        return "DAPI"
    if ratio < 0.9:
        return "FITC"
    return None


def _number(p: Path) -> int | None:
    m = re.findall(r"\d+", p.stem)
    return int(m[-1]) if m else None


def _mask(arr: np.ndarray, channel: str, step: int = 4) -> np.ndarray:
    ch = core.get_channel(arr, channel)[::step, ::step].astype(float)
    ch = filters.gaussian(ch, 1, preserve_range=True)
    h, w = ch.shape
    ch[int(h * 0.85):, int(w * 0.75):] = 0  # ölçek çubuğu
    return ch > filters.threshold_li(ch) if ch.max() > 0 else np.zeros_like(ch, bool)


def overlap(fitc_arr: np.ndarray, dapi_arr: np.ndarray) -> float:
    """Çekirdek maskesinin FITC hücre maskesi içinde kalan oranı (hızlı, 4× küçültülmüş)."""
    nuc = _mask(dapi_arr, "B")
    if not nuc.any():
        return 0.0
    return float(_mask(fitc_arr, "G")[nuc].mean())


@dataclass
class Item:
    fitc: Path | None
    dapi: Path | None = None
    overlap: float | None = None
    group: str = ""
    status: str = ""      # "hazır" | "DAPI yok" | "atlandı: …"
    use: bool = True


def scan(folder: Path, recursive: bool = True, progress=None) -> list[Item]:
    """Klasördeki görüntüleri sınıflar ve FITC→DAPI eşleştirir. Grup = alt klasör adı."""
    files = sorted(p for p in (folder.rglob("*") if recursive else folder.iterdir())
                   if p.is_file() and p.suffix.lower() in IMAGE_EXT and not p.name.startswith("._"))
    info, items = {}, []
    for k, p in enumerate(files):
        if progress:
            progress(k, len(files), f"Okunuyor: {p.name}")
        try:
            arr, meta = core.load_image(str(p))
        except Exception as ex:
            items.append(Item(p, status=f"atlandı: açılamadı ({type(ex).__name__})", use=False))
            continue
        kind = guess_kind(arr)
        skip = ""
        if meta.get("software"):
            skip = f"işlenmiş görüntü ({meta['software']})"
        elif p.suffix.lower() in (".jpg", ".jpeg") and not meta.get("model"):
            skip = "kamera bilgisi yok (merge/yeniden kaydedilmiş)"
        elif kind is None:
            skip = "FITC mi DAPI mi anlaşılamadı"
        info[p] = (kind, arr, skip)
    dapis = [p for p, (k, _, s) in info.items() if k == "DAPI" and not s]
    used = set()
    fitcs = [p for p, (k, _, s) in info.items() if k == "FITC" or s]
    for i, p in enumerate(fitcs):
        kind, arr, skip = info[p]
        group = p.parent.name if p.parent != folder else folder.name
        if skip:
            items.append(Item(p, group=group, status=f"atlandı: {skip}", use=False))
            continue
        if progress:
            progress(i, len(fitcs), f"Eşleştiriliyor: {p.name}")
        n = _number(p)
        cands = [d for d in dapis if d.parent == p.parent and n is not None and _number(d) is not None
                 and 0 < abs(_number(d) - n) <= NEIGHBOR and info[d][1].shape[:2] == arr.shape[:2]]
        scored = sorted(((overlap(arr, info[d][1]), d) for d in cands), key=lambda t: -t[0])
        if scored and scored[0][0] >= MIN_OVERLAP:
            ov, d = scored[0]
            used.add(d)
            items.append(Item(p, d, ov, group, "hazır"))
        else:
            best = f" (en iyi aday %{100 * scored[0][0]:.0f})" if scored else ""
            items.append(Item(p, None, scored[0][0] if scored else None, group, "DAPI yok" + best))
    for d in dapis:
        if d not in used:
            items.append(Item(None, d, group=d.parent.name, status="atlandı: eşleşmeyen DAPI", use=False))
    return items


def measure(item: Item, s: core.Settings, exclude_edge: bool = True):
    """Bir çifti ölçer: tüm hücreler (isteğe bağlı kenara değenler hariç) + otomatik background.
    → (Analysis, cells_df, bg_df)."""
    fitc, meta = core.load_image(str(item.fitc))
    dapi = core.load_image(str(item.dapi))[0] if item.dapi else None
    a = core.analyze(fitc, meta, dapi, s)
    ids = a.cell_ids
    if exclude_edge:
        lab = a.labels
        # segmentasyondaki kapanış (closing) en dış 2 pikseli boşaltır → 3 piksellik şeride bak
        edge = set(np.unique(np.r_[lab[:3].ravel(), lab[-3:].ravel(), lab[:, :3].ravel(),
                                   lab[:, -3:].ravel()])) - {0}
        ids = [i for i in ids if i not in edge]
    cells, bg, _ = core.background_and_measure(a, ids, s)
    return a, cells, bg
