"""CellVerity — koyu tema ve simgeler (Meriç Balcan, 2026-11-02; sistem görünümü 2026-11-03).

Program eskiden hiçbir tema kurmuyordu: görünüm işletim sisteminin eline kalıyor,
vurgu rengi Windows'un ayarından geliyordu (aynı program bir bilgisayarda pembe,
ötekinde mavi). Renkler artık tek yerde, burada.

Arayüz renkleri bilerek nötrdür: ölçülen floresan görüntüyle hiçbir şey
yarışmamalıdır. Görüntünün *üzerine* çizilen renkler (hücre sınırı, çekirdek,
background kutusu) veridir, temanın işi değildir — onlar core.py ve desktop.py'de
kalır.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from string import Template

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Paketlenmiş (.app/.exe) sürümde dosyalar PyInstaller'ın açtığı klasördedir;
# desktop.py'deki resource() ile aynı mantık.
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
ICONS = ROOT / "assets" / "icons"
QSS = ROOT / "theme.qss"

# İki görünüm: "dark" (varsayılan, bu dosyanın asıl teması) ve "system" (işletim sisteminin açık görünümü;
# yalnızca durum renkleri ve simgeler açık zemine göre koyulaşır). Seçim Görünüm ▸ Tema'dan, yeniden açılışta.
# Görüntünün çevresi (canvas) iki görünümde de koyu kalır: floresan koyu zeminde değerlendirilir.
MODE = "dark"

COLORS = {
    "canvas":    "#1b1b1b",   # görüntünün çevresi
    "canvas_text": "#9d9d9d", # görüntü alanındaki yönlendirme yazısı
    "header":    "#262626",   # panel başlıkları, durum çubuğu
    "panel":     "#2b2b2b",   # paneller ve dock'lar
    "chrome":    "#333333",   # araç çubukları, menüler
    "bar":       "#3a3a3a",   # pasif girdiler
    "field":     "#3c3c3c",   # girdi alanları
    "button":    "#4a4a4a",
    "active":    "#5a5a5a",   # seçili araç
    "line":      "#1f1f1f",   # sert ayraç
    "line_soft": "#3f3f3f",   # yumuşak ayraç
    "text":      "#d6d6d6",   # gövde yazısı     — #2b2b2b üzerinde 9.5:1
    "dim":       "#9d9d9d",   # etiket, ipucu    — #2b2b2b üzerinde 4.7:1
    "bright":    "#ffffff",
    "accent":    "#3b82d6",   # seçim ve odak — tek vurgu rengi
    "accent_hi": "#4d93e3",
    "icon":      "#c8c8c8",
    "icon_off":  "#6e6e6e",   # pasif
    # Zengin metin durumları. Hepsi #2b2b2b üzerinde en az 4.5:1 okunur;
    # eskiden bu renkler çevrilen cümlelerin içine gömülüydü (#a60, #b22, #555…)
    # ve açık zemin için seçilmişti, koyu zeminde okunmuyordu.
    "warn":      "#e0a33c",   # 6.2:1
    "bad":       "#e88a8a",   # 5.4:1
    "good":      "#7cc882",   # 6.8:1
    "info":      "#9d9d9d",   # 4.7:1
    # Durum şeritlerinin zemini; üstteki yazı renkleriyle en az 5.5:1 okunur.
    "bad_bg":    "#3a2626",
    "good_bg":   "#243026",
    "warn_bg":   "#3a3326",
}

DARK = dict(COLORS)

# Sistem (açık) görünümü: yalnızca zengin metin, durum şeritleri ve simgeler için; geri kalanı işletim sisteminde.
# Durum renkleri beyaz zeminde en az 4.5:1 okunur (eski sabit renklerle aynı aile).
LIGHT = dict(DARK, **{
    "text": "#1d1d1d", "dim": "#5f5f5f", "bright": "#000000",
    "accent": "#2a6fc2", "accent_hi": "#3a7fd2",
    "icon": "#3a3a3a", "icon_off": "#a6a6a6",
    "warn": "#9a5b00", "bad": "#b02020", "good": "#1e7a34", "info": "#5f5f5f",
    "bad_bg": "#fbe4e4", "good_bg": "#e3f4e6", "warn_bg": "#fdf3d8",
})

LIGHT_QSS = """
QLabel#hint, QLabel#toolhint { color: $dim; }
QLabel#toolhint { padding-left: 8px; }
QLabel#note { color: $warn; }
QLabel#banner { padding: 6px; border-radius: 4px; }
QLabel#banner[state="bad"]  { background: $bad_bg;  color: $bad; }
QLabel#banner[state="good"] { background: $good_bg; color: $good; }
QLabel#banner[state="warn"] { background: $warn_bg; color: $warn; }
QLabel#banner[state="none"] { background: transparent; padding: 0; }
QPushButton#primary { font-weight: bold; padding: 6px 14px; }
"""


def set_mode(mode: str) -> None:
    """'dark' | 'system'. Simgeler ve renkler ilk kullanımda önbelleğe alınır: pencereler kurulmadan önce çağrılmalı."""
    global MODE
    MODE = mode if mode in ("dark", "system") else "dark"
    COLORS.clear()
    COLORS.update(DARK if MODE == "dark" else LIGHT)
    _source.cache_clear()
    icon.cache_clear()


# Onay kutusundaki işaret yalnızca vurgu renginin üzerinde görünür: beyaz sabit.
_CHECK = ICONS / "check.svg"


# ------------------------------------------------------------------ simgeler
@lru_cache(maxsize=None)
def _source(name: str) -> str | None:
    try:
        return (ICONS / f"{name}.svg").read_text(encoding="utf-8")
    except OSError:
        return None


def _render(src: str, color: str, size: int) -> QPixmap:
    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    painter = QPainter(img)
    QSvgRenderer(QByteArray(src.replace("currentColor", color).encode())).render(
        painter, QRectF(0, 0, size, size))
    painter.end()
    return QPixmap.fromImage(img)


@lru_cache(maxsize=None)
def icon(name: str) -> QIcon:
    """assets/icons/<name>.svg — tema rengine boyanmış QIcon.

    Qt'nin SVG motoru `currentColor` bilmez, bu yüzden renk çizimden önce
    kaynağa yazılır. Aynı yol pasif ve üzerine gelinmiş durumlar için de ayrı
    piksel haritası verir; Qt'nin kendi soluklaştırması koyu zeminde kötü durur.
    """
    src = _source(name)
    if src is None:
        return QIcon()
    result = QIcon()
    for size in (16, 24, 32, 48):
        result.addPixmap(_render(src, COLORS["icon"], size), QIcon.Mode.Normal)
        result.addPixmap(_render(src, COLORS["icon_off"], size), QIcon.Mode.Disabled)
        result.addPixmap(_render(src, COLORS["bright"], size), QIcon.Mode.Active)
        result.addPixmap(_render(src, COLORS["bright"], size), QIcon.Mode.Selected)
    return result


# -------------------------------------------------------------- zengin metin
def span(kind: str, text: str) -> str:
    """Durum rengiyle sarılmış metin: span('warn', '…').

    QLabel'in zengin metni stylesheet sınıflarını görmez, bu yüzden renk satır
    içinde verilmek zorunda; önemli olan, rengin çevrilen cümlenin içinde değil
    burada durmasıdır.
    """
    return f"<span style='color:{COLORS[kind]}'>{text}</span>"


def restyle(widget) -> None:
    """Dinamik bir özellik (örn. durum şeridinin 'state') değişince yeniden boyar.

    Qt stylesheet'i özellik seçicilerini kendiliğinden yenilemez.
    """
    widget.style().unpolish(widget)
    widget.style().polish(widget)


# -------------------------------------------------------------------- tema
def _palette() -> QPalette:
    """QSS'in ulaşmadığı yerler (öğe görünümleri, ipuçları, devre dışı metin)."""
    c = {k: QColor(v) for k, v in COLORS.items()}
    p = QPalette()
    roles = {
        QPalette.ColorRole.Window: c["panel"],
        QPalette.ColorRole.WindowText: c["text"],
        QPalette.ColorRole.Base: c["canvas"],
        QPalette.ColorRole.AlternateBase: c["chrome"],
        QPalette.ColorRole.Text: c["text"],
        QPalette.ColorRole.Button: c["button"],
        QPalette.ColorRole.ButtonText: c["text"],
        QPalette.ColorRole.BrightText: c["bright"],
        QPalette.ColorRole.ToolTipBase: c["header"],
        QPalette.ColorRole.ToolTipText: c["text"],
        QPalette.ColorRole.PlaceholderText: c["dim"],
        QPalette.ColorRole.Highlight: c["accent"],
        QPalette.ColorRole.HighlightedText: c["bright"],
        QPalette.ColorRole.Link: c["accent"],
        QPalette.ColorRole.LinkVisited: c["accent"],
    }
    for role, color in roles.items():
        p.setColor(role, color)
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text,
                 QPalette.ColorRole.ButtonText):
        p.setColor(QPalette.ColorGroup.Disabled, role, c["icon_off"])
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, c["active"])
    return p


def stylesheet() -> str:
    """theme.qss'i renklerle doldurur. Dosya yoksa boş döner (program yine açılır)."""
    try:
        template = QSS.read_text(encoding="utf-8")
    except OSError:
        return ""
    values = dict(COLORS)
    values["check"] = _CHECK.as_posix()   # QSS url() ters eğik çizgiyi sevmez
    values["arrow_down"] = (ICONS / "arrow-down.svg").as_posix()
    values["arrow_up"] = (ICONS / "arrow-up.svg").as_posix()
    return Template(template).substitute(values)


def apply(app) -> None:
    """Tüm uygulamaya temayı kurar. desktop.py'de QApplication'dan hemen sonra çağrılır."""
    if MODE == "system":  # işletim sisteminin görünümü; yalnızca adlandırılmış etiketler/düğmeler biçimlenir
        app.setStyleSheet(Template(LIGHT_QSS).substitute(COLORS))
        return
    app.setStyle("Fusion")   # yoksa Windows yerel stili QSS'i ve vurgu rengini ezer
    app.setPalette(_palette())
    app.setStyleSheet(stylesheet())
