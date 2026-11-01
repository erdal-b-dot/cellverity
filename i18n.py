"""Arayüz dili (Türkçe / English).

Kaynak metinler Türkçedir; İngilizce karşılıkları locales/en.json'dadır. T("…") seçili dile göre döner.
Biçimli metinler: T("{0} hücre bulundu.").format(n) — çeviride de aynı {0}, {1:.3f} yer tutucuları bulunur.
Ölçüm, Excel sütun adları ve sayısal sonuçlar dilden bağımsızdır.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LANGS = {"tr": "Türkçe", "en": "English"}
_lang = "tr"
_table: dict[str, str] = {}


def _locale_dir() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "locales"


def set_language(lang: str) -> str:
    global _lang, _table
    _lang = lang if lang in LANGS else "en"
    _table = {}
    if _lang != "tr":
        p = _locale_dir() / f"{_lang}.json"
        if p.exists():
            _table = json.loads(p.read_text(encoding="utf-8"))
    return _lang


def language() -> str:
    return _lang


def T(text: str) -> str:
    """Seçili dildeki karşılık; yoksa kaynak (Türkçe) metin."""
    return _table.get(text, text) if _table else text


def system_language() -> str:
    """İşletim sistemi Türkçe ise 'tr', değilse 'en'."""
    try:
        from PySide6.QtCore import QLocale
        return "tr" if QLocale.system().name().lower().startswith("tr") else "en"
    except Exception:
        import locale
        return "tr" if (locale.getlocale()[0] or "").lower().startswith("tr") else "en"
