"""Klasör işleme: FITC/DAPI çiftlerini bulma ve toplu ölçüm (arayüzden bağımsız).

Ardışık dosya numarası her zaman aynı alan demek değildir (geliştirme veri setinde 292+293, 394+395 farklı
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
    geliştirme veri setindeki 282 tek kanal görüntüde FITC ≤ 0.79, DAPI ≥ 1.47)."""
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
    """Şansa göre düzeltilmiş çekirdek–hücre örtüşmesi (hızlı, 4× küçültülmüş): 1 = bütün çekirdekler hücre
    içinde, 0 = rastgele yerleşimden farksız. Ham oran yanıltıcıdır: hücrelerin alanın yarısını kapladığı kalabalık
    görüntüde başka alana ait bir DAPI bile ~%50 örtüşür (2026-11-01, samples/Image_11323 + 11322: ham 0.55)."""
    nuc = _mask(dapi_arr, "B")
    if not nuc.any():
        return 0.0
    return core.chance_corrected_overlap(_mask(fitc_arr, "G"), nuc)


@dataclass
class Item:
    fitc: Path | None
    dapi: Path | None = None
    overlap: float | None = None
    group: str = ""
    experiment: str = ""  # bağımsız deney / biyolojik tekrar
    status: str = ""      # dilden bağımsız kod: "ready" | "no_dapi" | "skipped"
    reason: str = ""      # skipped: "unreadable" | "processed" | "no_exif" | "unknown_kind" | "unpaired_dapi"
    detail: str = ""      # ek bilgi (yazılım adı, hata türü)
    use: bool = True


def group_experiment(p: Path, folder: Path) -> tuple[str, str]:
    """Klasör düzeninden grup ve deney adı:
    Seçilen/Deney_1/Kontrol/img → deney 'Deney_1', grup 'Kontrol'
    Seçilen(=Deney_1)/Kontrol/img → deney 'Deney_1' (seçilen klasör), grup 'Kontrol'
    Seçilen/img → grup ve deney = seçilen klasör adı."""
    parts = p.relative_to(folder).parts
    if len(parts) >= 3:
        return parts[-2], parts[-3]
    if len(parts) == 2:
        return parts[0], folder.name
    return folder.name, folder.name


def scan(folder: Path, recursive: bool = True, progress=None) -> list[Item]:
    """Klasördeki görüntüleri sınıflar ve FITC→DAPI eşleştirir. Grup/deney klasör düzeninden gelir."""
    files = sorted(p for p in (folder.rglob("*") if recursive else folder.iterdir())
                   if p.is_file() and p.suffix.lower() in IMAGE_EXT and not p.name.startswith("._"))
    info, items = {}, []
    for k, p in enumerate(files):
        if progress:
            progress(k, len(files), "read", p.name)
        try:
            arr, meta = core.load_image(str(p))
        except Exception as ex:
            items.append(Item(p, status="skipped", reason="unreadable", detail=type(ex).__name__, use=False))
            continue
        kind = guess_kind(arr)
        skip = ""
        if meta.get("software"):
            skip = "processed:" + str(meta["software"])
        elif p.suffix.lower() in (".jpg", ".jpeg") and not meta.get("model"):
            skip = "no_exif"
        elif kind is None:
            skip = "unknown_kind"
        info[p] = (kind, arr, skip)
    dapis = [p for p, (k, _, s) in info.items() if k == "DAPI" and not s]
    used = set()
    fitcs = [p for p, (k, _, s) in info.items() if k == "FITC" or s]
    for i, p in enumerate(fitcs):
        kind, arr, skip = info[p]
        group, exp = group_experiment(p, folder)
        if skip:
            reason, _, detail = skip.partition(":")
            items.append(Item(p, group=group, experiment=exp, status="skipped", reason=reason, detail=detail,
                              use=False))
            continue
        if progress:
            progress(i, len(fitcs), "pair", p.name)
        n = _number(p)
        cands = [d for d in dapis if d.parent == p.parent and n is not None and _number(d) is not None
                 and 0 < abs(_number(d) - n) <= NEIGHBOR and info[d][1].shape[:2] == arr.shape[:2]]
        scored = sorted(((overlap(arr, info[d][1]), d) for d in cands), key=lambda t: -t[0])
        if scored and scored[0][0] >= MIN_OVERLAP:
            ov, d = scored[0]
            used.add(d)
            items.append(Item(p, d, ov, group, exp, "ready"))
        else:
            items.append(Item(p, None, scored[0][0] if scored else None, group, exp, "no_dapi"))
    for d in dapis:
        if d not in used:
            g, e = group_experiment(d, folder)
            items.append(Item(None, d, group=g, experiment=e, status="skipped", reason="unpaired_dapi", use=False))
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
