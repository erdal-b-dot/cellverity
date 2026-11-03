"""Yeni sürüm denetimi: GitHub'daki en son yayımlanmış sürümü (releases/latest) sorar ve kurulu sürümle karşılaştırır.

Yalnızca bir sürüm sorgusu gider (görüntü ya da veri gönderilmez); internet yoksa ya da 5 s içinde yanıt gelmezse
sessizce vazgeçilir. Arayüz bunu açılışta günde en çok bir kez (kapatılabilir) ya da Yardım menüsünden elle çağırır.
"""
from __future__ import annotations

import json
import re

REPO = "erdal-b-dot/cellverity"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"


def parse_version(v: str) -> tuple:
    """'v2.2.0' / '2.2.0-dev' / '2.10' → karşılaştırılabilir anahtar. Aynı numarada geliştirme sürümü (-dev, -rc…)
    yayımlanmış sürümden önce gelir: 2.2.0-dev < 2.2.0 < 2.2.1 < 2.10.0."""
    v = str(v).strip().lstrip("vV")
    base, _, suffix = v.partition("-")
    nums = [int(x) for x in re.findall(r"\d+", base)[:3]]
    nums += [0] * (3 - len(nums))
    return (*nums, 0 if suffix else 1)


def is_newer(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)


def fetch_latest(current: str, timeout: float = 5.0) -> dict:
    """→ {'version', 'url', 'notes', 'newer'}; ağ hatasında istisna fırlatır (çağıran yakalar)."""
    import ssl
    import urllib.request
    try:
        import certifi  # paketlenmiş programda sistem sertifikaları bulunamayabilir
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
    req = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": f"CellVerity/{current}"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        data = json.loads(r.read().decode("utf-8"))
    tag = data.get("tag_name", "")
    return {"version": tag.lstrip("vV"), "url": data.get("html_url") or RELEASES_PAGE,
            "notes": (data.get("body") or "").strip(), "newer": bool(tag) and is_newer(tag, current)}
