"""Belgeler için arayüz ekran görüntüsü: örnek veri (examples/, CC BY 4.0) açılır, hücreler seçilir ve sonuç
tablosuna eklenir, tüm pencere PNG olarak kaydedilir. GitHub Actions'ta (Screenshots iş akışı) gerçek Windows/macOS
yazı tipleriyle çalışır.

    python tools/screenshot.py çıktı.png [--width 1600] [--height 1560] [--lang en] [--theme dark] [--scale 2]
                                         [--no-menubar]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=1560)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--theme", default="dark")
    ap.add_argument("--scale", default="2")
    ap.add_argument("--no-menubar", action="store_true", help="macOS görünümü: menü pencerede değil ekranın üstünde")
    a = ap.parse_args()
    os.environ.setdefault("QT_SCALE_FACTOR", a.scale)
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    import core
    import desktop
    import i18n
    import theme
    app = QApplication(sys.argv[:1])
    app.setApplicationName(desktop.APP_NAME)
    theme.set_mode(a.theme)
    theme.apply(app)
    i18n.set_language(a.lang)
    w = desktop.MainWindow()
    w.resize(a.width, a.height)
    w.show()
    if a.no_menubar:
        w.menuBar().hide()
    folder = ROOT / "examples" / "PARC_control"
    for name in ("Image_11305.jpg", "Image_11306.jpg"):
        p = folder / name
        arr, meta = core.load_image(str(p))
        w._set(p, arr, meta, "DAPI" if desktop.is_dapi_like(arr) else "FITC", run=False)
    w.panel.group.setText("Control")
    w.panel.experiment.setText("1")
    w.panel.protein.setText("p53")
    w.run_analysis()

    def analysed():
        if w._thread is not None:
            QTimer.singleShot(300, analysed)
            return
        w.select_all()
        w.add_to_results()
        w.tabs.setCurrentIndex(0)
        QTimer.singleShot(1500, save)

    def save():
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        w.grab().save(a.out)
        print("kaydedildi:", a.out, w.grab().size().toTuple(), "platform:", app.platformName(),
              "yazı tipi:", app.font().family())
        w._dirty = False  # kapanışta 'kaydedilmemiş sonuçlar' sorusu sorulmasın (ekransız ortam)
        app.quit()

    QTimer.singleShot(500, analysed)
    app.exec()


if __name__ == "__main__":
    main()
