"""ICC CTCF Ölçer 2.0 — bağımsız masaüstü arayüzü (PySide6/Qt).

Hesaplamalar core.py'dedir (v1.0.0 Streamlit sürümüyle aynı, Fiji ile doğrulandı).
Çalıştırma:  .venv/bin/python desktop.py   (Windows: .venv\\Scripts\\python desktop.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QRectF, Qt, QThread, Signal
from PySide6.QtGui import QAction, QImage, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QDockWidget, QFileDialog, QFormLayout, QFrame,
                               QComboBox, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QLabel,
                               QMainWindow, QMessageBox, QSlider, QVBoxLayout, QWidget)

import core

APP_NAME = "ICC CTCF Ölçer"
VERSION = "2.0.0-dev"
IMAGE_FILTER = "Görüntüler (*.jpg *.jpeg *.tif *.tiff *.png)"


def is_dapi_like(arr: np.ndarray) -> bool:
    """Mavi kanalın baskın olduğu (DAPI) görüntüyü tanır; sürükle-bırakta FITC/DAPI ayrımı için."""
    if arr.ndim != 3:
        return False
    m = arr.reshape(-1, 3).mean(axis=0)
    return m[2] > 1.5 * max(m[1], 1e-6)


VIEW_MODES = ("FITC", "DAPI", "Birleşik (FITC + DAPI)")


def merge_display(fitc: np.ndarray, dapi: np.ndarray, gain: float) -> np.ndarray:
    """FITC yeşil + DAPI mavi kanallarını tek renkli görüntüde birleştirir (yalnız ekran için)."""
    f = core.to_display(fitc, gain)
    d = core.to_display(dapi, gain)
    return np.maximum(f, d)


def to_pixmap(im) -> QPixmap:
    a = np.ascontiguousarray(np.asarray(im.convert("RGB")))
    h, w = a.shape[:2]
    return QPixmap.fromImage(QImage(a.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy())


# ------------------------------------------------------------------ Görüntü alanı
class ImageView(QGraphicsView):
    """Fare tekerleği ile yakınlaştırma, sürükleyerek kaydırma."""

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.item = QGraphicsPixmapItem()
        self.item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.scene().addItem(self.item)
        self.setRenderHints(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(Qt.GlobalColor.black)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.placeholder = QLabel("FITC ve DAPI görüntülerini buraya sürükleyin\nveya  Dosya ▸ FITC aç  (⌘O / Ctrl+O)",
                                  self)
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color:#9aa; font-size:16px;")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.placeholder.resize(self.viewport().size())

    def set_pixmap(self, pm: QPixmap, fit: bool):
        self.placeholder.hide()
        self.item.setPixmap(pm)
        self.scene().setSceneRect(QRectF(pm.rect()))
        if fit:
            self.fit()

    def fit(self):
        if not self.item.pixmap().isNull():
            self.fitInView(self.item, Qt.AspectRatioMode.KeepAspectRatio)

    def zoom(self, f: float):
        self.scale(f, f)

    def wheelEvent(self, e):
        self.zoom(1.25 if e.angleDelta().y() > 0 else 0.8)


# ------------------------------------------------------------- Arka plan işi
class AnalysisWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fitc, meta, dapi):
        super().__init__()
        self.args = fitc, meta, dapi

    def run(self):
        try:
            self.finished.emit(core.analyze(*self.args))
        except Exception as ex:  # arayüzde göster, programı çökertme
            self.failed.emit(f"{type(ex).__name__}: {ex}")


# --------------------------------------------------------------- Bilgi paneli
class InfoPanel(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.fields = {}
        for key in ("FITC", "DAPI", "Kalibrasyon", "Objektif", "Hücre sayısı", "Çekirdek sayısı"):
            lbl = QLabel("—")
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl.setWordWrap(True)
            self.fields[key] = lbl
            form.addRow(f"<b>{key}</b>", lbl)
        lay.addLayout(form)
        self.mode = QLabel()
        self.mode.setWordWrap(True)
        lay.addWidget(self.mode)
        legend = QLabel("<b>Çizgiler</b><br>"
                        "<span style='color:#b8b8b8'>━</span> hücre sınırı (numaralı)<br>"
                        "<span style='color:#d4b000'>━</span> seçili hücre<br>"
                        "<span style='color:#00a0ff'>━</span> çekirdek sınırı (DAPI'den)<br>"
                        "<span style='color:#ff3c3c'>□</span> background kutusu")
        lay.addSpacing(8)
        lay.addWidget(legend)
        lay.addSpacing(12)
        lay.addWidget(QLabel("<b>Görüntü parlaklığı</b> (yalnız ekran; ölçümü etkilemez)"))
        self.gain = QSlider(Qt.Orientation.Horizontal)
        self.gain.setRange(10, 60)
        self.gain.setValue(10)
        lay.addWidget(self.gain)
        lay.addStretch()
        note = QLabel("⚠️ Birbirine değen hücreler varsa aynı alanın DAPI görüntüsünü mutlaka yükleyin.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#a60;")
        lay.addWidget(note)

    def set(self, key, text):
        self.fields[key].setText(text)

    def set_mode(self, a: core.Analysis | None):
        if a is None:
            self.mode.setText("")
            self.mode.setStyleSheet("")
        elif a.nuclei is not None:
            self.mode.setText("🧬 <b>Hücre ayırma: DAPI çekirdekleri</b>")
            self.mode.setStyleSheet("background:#e3f4e6; color:#174; padding:6px; border-radius:4px;")
        elif a.touching:
            self.mode.setText(f"⚠️ <b>Hücre ayırma: yalnızca şekil</b> — {len(a.touching)} değen hücre çifti var; "
                              "DAPI yükleyin.")
            self.mode.setStyleSheet("background:#fbe4e4; color:#922; padding:6px; border-radius:4px;")
        else:
            self.mode.setText("ℹ️ <b>Hücre ayırma: yalnızca şekil</b> (değen hücre yok)")
            self.mode.setStyleSheet("background:#fdf3d8; color:#850; padding:6px; border-radius:4px;")


# ---------------------------------------------------------------- Ana pencere
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {VERSION}")
        self.resize(1400, 900)
        self.setAcceptDrops(True)
        self.fitc = self.dapi = None  # (Path, arr, meta)
        self.analysis: core.Analysis | None = None
        self._thread = None
        self._pending = False  # analiz sürerken yeni görüntü gelirse bitince yeniden çalıştır

        self.view = ImageView()
        self.setCentralWidget(self.view)
        self.panel = InfoPanel()
        self.panel.gain.valueChanged.connect(lambda _: self.redraw(fit=False))
        dock = QDockWidget("Görüntü bilgisi", self)
        dock.setWidget(self.panel)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        dock.setMinimumWidth(300)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self._build_actions()
        self.statusBar().showMessage("Hazır — görüntü açın veya sürükleyin.")

    def _build_actions(self):
        def act(text, slot, shortcut=None, checkable=False):
            a = QAction(text, self)
            a.triggered.connect(slot)
            if shortcut:
                a.setShortcut(QKeySequence(shortcut))
            a.setCheckable(checkable)
            return a

        self.a_fitc = act("FITC aç…", lambda: self.open_dialog("FITC"), QKeySequence.StandardKey.Open)
        self.a_fitc.setToolTip("Ölçülecek yeşil (FITC) görüntüyü açar. Yeni FITC açılınca eski DAPI kaldırılır.")
        self.a_dapi = act("DAPI aç…", lambda: self.open_dialog("DAPI"), "Ctrl+D")
        self.a_dapi.setToolTip("Aynı alanın mavi (DAPI) görüntüsünü açar; değen hücreleri çekirdeklere göre ayırmak için.")
        self.a_fit = act("Pencereye sığdır", self.view.fit, "Ctrl+0")
        self.a_in = act("Yakınlaştır", lambda: self.view.zoom(1.25), QKeySequence.StandardKey.ZoomIn)
        self.a_out = act("Uzaklaştır", lambda: self.view.zoom(0.8), QKeySequence.StandardKey.ZoomOut)
        self.a_nuc = act("Çekirdek sınırları", lambda: self.redraw(fit=False), "Ctrl+N", checkable=True)
        self.a_nuc.setChecked(True)
        self.a_nuc.setToolTip("DAPI'den bulunan çekirdeklerin sınırlarını mavi çizgiyle gösterir/gizler.\n"
                              "Program değen hücreleri bu çekirdeklere göre ayırır. Ölçümü etkilemez.")
        self.view_mode = QComboBox()
        self.view_mode.addItems(VIEW_MODES)
        self.view_mode.setToolTip("Ekranda hangi görüntünün gösterileceği. Ölçüm her zaman FITC'den yapılır.")
        self.view_mode.currentIndexChanged.connect(lambda _: self.redraw(fit=False))

        m = self.menuBar().addMenu("Dosya")
        m.addActions([self.a_fitc, self.a_dapi])
        m.addSeparator()
        m.addAction(act("Çıkış", self.close, QKeySequence.StandardKey.Quit))
        m = self.menuBar().addMenu("Görünüm")
        m.addActions([self.a_fit, self.a_in, self.a_out])
        m.addSeparator()
        m.addAction(self.a_nuc)
        m = self.menuBar().addMenu("Yardım")
        m.addAction(act("Hakkında", self.about))

        tb = self.addToolBar("Araçlar")
        tb.setMovable(False)
        tb.addActions([self.a_fitc, self.a_dapi])
        tb.addSeparator()
        tb.addActions([self.a_fit, self.a_in, self.a_out])
        tb.addSeparator()
        tb.addWidget(QLabel(" Görüntü: "))
        tb.addWidget(self.view_mode)
        tb.addAction(self.a_nuc)

    # ---------------------------------------------------------- dosya açma
    def open_dialog(self, kind):
        path, _ = QFileDialog.getOpenFileName(self, f"{kind} görüntüsü aç", "", IMAGE_FILTER)
        if path:
            self.load(Path(path), kind)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        paths = [Path(u.toLocalFile()) for u in e.mimeData().urls()][:2]
        loaded = []
        for p in paths:
            try:
                loaded.append((p, *core.load_image(str(p))))
            except Exception as ex:
                QMessageBox.warning(self, APP_NAME, f"{p.name} açılamadı:\n{ex}")
        loaded.sort(key=lambda t: is_dapi_like(t[1]))  # önce FITC, sonra DAPI
        for p, arr, meta in loaded:
            self._set(p, arr, meta, "DAPI" if is_dapi_like(arr) else "FITC", run=False)
        if loaded:
            self.run_analysis()

    def load(self, path: Path, kind: str):
        try:
            arr, meta = core.load_image(str(path))
        except Exception as ex:
            QMessageBox.warning(self, APP_NAME, f"{path.name} açılamadı:\n{ex}")
            return
        looks = "DAPI" if is_dapi_like(arr) else "FITC"
        if looks != kind:
            ans = QMessageBox.question(
                self, APP_NAME,
                f"{path.name} bir {looks} görüntüsüne benziyor ({'mavi' if looks == 'DAPI' else 'mavi değil'}), "
                f"ama {kind} olarak açılıyor.\n\n{looks} olarak açılsın mı?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
            if ans == QMessageBox.StandardButton.Yes:
                kind = looks
        self._set(path, arr, meta, kind)

    def _set(self, path, arr, meta, kind, run=True):
        if kind == "FITC":
            if self.fitc is None or self.fitc[0] != path:
                self.analysis = None
                if self.fitc is not None and self.dapi is not None:  # önceki alanın DAPI'si yanlış ayırır
                    self.dapi = None
                    self.panel.set("DAPI", "— (yeni FITC açıldı; aynı alanın DAPI'sini açın)")
            self.fitc = (path, arr, meta)
            self.panel.set("FITC", path.name)
            if meta.get("software"):
                QMessageBox.warning(self, APP_NAME, f"Görüntü yazılımla işlenmiş görünüyor: {meta['software']}.\n"
                                    "Parlaklık/kontrast ayarı yapılmış görüntülerde CTCF güvenilir değildir.")
        else:
            self.dapi = (path, arr, meta)
            self.panel.set("DAPI", path.name)
            self.view_mode.setCurrentIndex(2)  # DAPI'nin yüklendiği görülsün
        if run:
            self.run_analysis()

    # ------------------------------------------------------------- analiz
    def run_analysis(self):
        if self.fitc is None:
            self.statusBar().showMessage("DAPI yüklendi — şimdi FITC görüntüsünü açın.")
            return
        if self._thread is not None:
            self._pending = True
            return
        _, arr, meta = self.fitc
        dapi = self.dapi[1] if self.dapi else None
        if dapi is not None and dapi.shape[:2] != arr.shape[:2]:
            QMessageBox.warning(self, APP_NAME, "FITC ve DAPI görüntülerinin boyutları farklı; DAPI kullanılmadı.")
            dapi = None
        self.statusBar().showMessage("Hücreler algılanıyor…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self._thread = QThread(self)
        self._worker = AnalysisWorker(arr, meta, dapi)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self.on_done)
        self._worker.failed.connect(self.on_fail)
        self._thread.start()

    def _stop_thread(self):
        QApplication.restoreOverrideCursor()
        self._thread.quit()
        self._thread.wait()
        self._thread = None

    def on_fail(self, msg):
        self._stop_thread()
        self.statusBar().showMessage("Analiz başarısız.")
        QMessageBox.critical(self, APP_NAME, f"Analiz sırasında hata:\n{msg}")

    def on_done(self, a: core.Analysis):
        first = self.analysis is None
        self._stop_thread()
        self.analysis = a
        p = self.panel
        if a.um_per_px:
            p.set("Kalibrasyon", f"{a.um_per_px:.4f} µm/piksel  (çubuk {a.scale_bar.bar_px} px = 20 µm)")
            obj, raw = a.objective
            p.set("Objektif", f"{obj}×  (hesaplanan {raw:.1f}×)")
        else:
            p.set("Kalibrasyon", "Ölçek çubuğu bulunamadı — piksel birimi")
            p.set("Objektif", "—")
        p.set("Hücre sayısı", f"{len(a.cell_ids)}")
        p.set("Çekirdek sayısı", f"{int(a.nuclei.max())}" if a.nuclei is not None else "— (DAPI yok)")
        p.set_mode(a)
        self.redraw(fit=first)
        self.statusBar().showMessage(f"{len(a.cell_ids)} hücre bulundu.")
        if self._pending:
            self._pending = False
            self.run_analysis()

    def redraw(self, fit=False):
        a = self.analysis
        if a is None:
            return
        gain = self.panel.gain.value() / 10
        mode = self.view_mode.currentIndex()
        dapi = self.dapi[1] if self.dapi and self.dapi[1].shape[:2] == a.fitc_arr.shape[:2] else None
        if mode == 1 and dapi is not None:
            disp = core.to_display(dapi, gain)
        elif mode == 2 and dapi is not None:
            disp = merge_display(a.fitc_arr, dapi, gain)
        else:
            disp = core.to_display(a.fitc_arr, gain)
        nuclei = a.nuclei if self.a_nuc.isChecked() else None
        self.view.set_pixmap(to_pixmap(core.overlay(disp, a.labels, set(), [], nuclei)), fit)

    def about(self):
        QMessageBox.about(self, APP_NAME,
                          f"<b>{APP_NAME} {VERSION}</b><br>Immunositokimya görüntülerinde CTCF ölçümü.<br><br>"
                          "CTCF = IntDen − (Area × Mean background)<br>McCloy et al., 2014, <i>Cell Cycle</i><br><br>"
                          "Ölçümler ImageJ/Fiji ile birebir aynıdır.<br>© Erdal Balcan, MIT lisansı")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    w = MainWindow()
    w.show()
    for arg in sys.argv[1:3]:  # komut satırından: desktop.py FITC.jpg [DAPI.jpg]
        p = Path(arg)
        arr, meta = core.load_image(str(p))
        w._set(p, arr, meta, "DAPI" if is_dapi_like(arr) else "FITC", run=False)
    if w.fitc:
        w.run_analysis()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
