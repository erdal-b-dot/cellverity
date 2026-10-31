"""ICC CTCF Ölçer 2.0 — bağımsız masaüstü arayüzü (PySide6/Qt).

Hesaplamalar core.py'dedir (ölçüm tanımları ImageJ/Fiji ile birebir aynı). v2 çekirdek algılaması
parlak çekirdek gövdesini kullanır (core.Settings.nuc_bright_core); v1.0.0 Streamlit sürümü eskisini kullanır.
Çalıştırma:  .venv/bin/python desktop.py   (Windows: .venv\\Scripts\\python desktop.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QRectF, Qt, QThread, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QImage, QKeySequence, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QComboBox, QDockWidget,
                               QFileDialog, QFormLayout, QFrame, QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QMainWindow,
                               QMessageBox, QPushButton, QRadioButton, QScrollArea, QSlider, QSpinBox,
                               QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

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
NUCLEUS_COLOR = (255, 0, 255)  # mor: hem yeşil hem mavi zeminde görünür
TABLE_COLS = [("Cell", "Hücre", 0), ("Area", "Alan", 2), ("Mean", "Mean", 3), ("StdDev", "StdDev", 3),
              ("Min", "Min", 0), ("Max", "Max", 0), ("IntDen", "IntDen", 1), ("RawIntDen", "RawIntDen", 0),
              ("CTCF", "CTCF", 1), ("Saturated_px", "Doymuş px", 0)]
BG_COLS = [("BG", "Kutu", 0), ("x0", "x", 0), ("y0", "y", 0), ("Area_px", "Piksel", 0), ("Mean", "Mean", 3),
           ("StdDev", "StdDev", 3), ("Min", "Min", 0), ("Max", "Max", 0), ("RawIntDen", "RawIntDen", 0)]


def make_table(cols) -> QTableWidget:
    t = QTableWidget(0, len(cols))
    t.setHorizontalHeaderLabels([c[1] for c in cols])
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setAlternatingRowColors(True)
    return t


def fill(table: QTableWidget, cols, df):
    table.setRowCount(0)
    if df is None or not len(df):
        return
    table.setRowCount(len(df))
    for r, row in enumerate(df.itertuples(index=False)):
        for c, (col, _, dec) in enumerate(cols):
            v = getattr(row, col)
            it = QTableWidgetItem(f"{v:,.{dec}f}".replace(",", " ") if dec else f"{int(v)}")
            it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(r, c, it)


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
    """Fare tekerleği ile yakınlaştırma, sürükleyerek kaydırma; kısa tıklama → clicked(y, x).

    Background kutuları ayrı sahne nesneleridir: üzerine basıp sürükleyince taşınır → box_moved(i, y0, x0).
    """
    clicked = Signal(int, int)
    box_moved = Signal(int, int, int)
    BOX_COLOR = QColor(255, 60, 60)

    def __init__(self):
        super().__init__()
        self._press = None
        self._drag = None  # (kutu indeksi, fare ile kutu köşesi arasındaki fark)
        self.box_items: list[tuple[QGraphicsRectItem, QGraphicsSimpleTextItem]] = []
        self.setMouseTracking(True)
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

    # ------------------------------------------------------- kutular
    def set_boxes(self, boxes):
        for r, t in self.box_items:
            self.scene().removeItem(r)
            self.scene().removeItem(t)
        self.box_items = []
        pen = QPen(self.BOX_COLOR, 3)
        font = QFont()
        font.setPixelSize(26)
        font.setBold(True)
        for i, (y0, x0, y1, x1) in enumerate(boxes, 1):
            r = self.scene().addRect(0, 0, x1 - x0, y1 - y0, pen, QBrush(QColor(255, 60, 60, 35)))
            r.setPos(x0, y0)
            t = self.scene().addSimpleText(f"BG{i}", font)
            t.setBrush(self.BOX_COLOR)
            t.setPos(x0, y0 - 30)
            self.box_items.append((r, t))

    def box_at(self, pt) -> int | None:
        for i, (r, _) in enumerate(self.box_items):
            if r.sceneBoundingRect().contains(pt):
                return i
        return None

    def mousePressEvent(self, e):
        self._press = e.position().toPoint()
        if e.button() == Qt.MouseButton.LeftButton:
            pt = self.mapToScene(self._press)
            i = self.box_at(pt)
            if i is not None:
                self._drag = (i, pt - self.box_items[i][0].pos())
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            i, off = self._drag
            r, t = self.box_items[i]
            pm = self.item.pixmap()
            w, h = r.rect().width(), r.rect().height()
            pos = self.mapToScene(e.position().toPoint()) - off
            x = min(max(pos.x(), 0), pm.width() - w)
            y = min(max(pos.y(), 0), pm.height() - h)
            r.setPos(round(x), round(y))
            t.setPos(round(x), round(y) - 30)
            return
        super().mouseMoveEvent(e)
        if not e.buttons():
            over = self.box_at(self.mapToScene(e.position().toPoint())) is not None
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor if over else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, e):
        if self._drag is not None:
            i, _ = self._drag
            self._drag = None
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            if (e.position().toPoint() - self._press).manhattanLength() < 5:
                pt = self.mapToScene(self._press)  # taşımadan tıklama → kutu silme vb.
                self.clicked.emit(int(pt.y()), int(pt.x()))
            else:
                pos = self.box_items[i][0].pos()
                self.box_moved.emit(i, int(pos.y()), int(pos.x()))
            self._press = None
            return
        super().mouseReleaseEvent(e)
        if self._press is not None and (e.position().toPoint() - self._press).manhattanLength() < 5:
            pt = self.mapToScene(self._press)
            pm = self.item.pixmap()
            if not pm.isNull() and 0 <= pt.x() < pm.width() and 0 <= pt.y() < pm.height():
                self.clicked.emit(int(pt.y()), int(pt.x()))
        self._press = None


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
        sel = QGroupBox("Hücre seçimi")
        sl = QVBoxLayout(sel)
        sl.addWidget(QLabel("Hücreye tıklayarak seçin / bırakın."))
        row = QHBoxLayout()
        self.btn_all = QPushButton("Tüm hücreleri seç")
        self.btn_none = QPushButton("Seçimi temizle")
        row.addWidget(self.btn_all)
        row.addWidget(self.btn_none)
        sl.addLayout(row)
        self.sel_info = QLabel("Seçili: —")
        sl.addWidget(self.sel_info)
        lay.addWidget(sel)

        bg = QGroupBox("Background")
        bl = QVBoxLayout(bg)
        row = QHBoxLayout()
        self.bg_auto = QRadioButton("Otomatik")
        self.bg_manual = QRadioButton("Elle")
        self.bg_auto.setChecked(True)
        self.bg_group = QButtonGroup(self)
        self.bg_group.addButton(self.bg_auto)
        self.bg_group.addButton(self.bg_manual)
        row.addWidget(self.bg_auto)
        row.addWidget(self.bg_manual)
        row.addStretch()
        bl.addLayout(row)
        f2 = QFormLayout()
        self.bg_size = QSpinBox()
        self.bg_size.setRange(5, 500)
        self.bg_size.setSingleStep(5)
        self.bg_size.setValue(50)
        self.bg_size.setSuffix(" px")
        self.bg_n = QSpinBox()
        self.bg_n.setRange(1, 10)
        self.bg_n.setValue(3)
        f2.addRow("Kutu boyutu (kare)", self.bg_size)
        f2.addRow("Otomatik kutu sayısı", self.bg_n)
        bl.addLayout(f2)
        self.bg_hint = QLabel("Kutuları fareyle sürükleyerek taşıyabilirsiniz (otomatik kutu taşınırsa 'Elle'ye "
                              "geçilir). Elle: boş alana tıklayın → kutu eklenir; kutuya tıklayın → silinir.")
        self.bg_hint.setWordWrap(True)
        self.bg_hint.setStyleSheet("color:#666;")
        bl.addWidget(self.bg_hint)
        self.btn_bg_clear = QPushButton("Elle kutuları temizle")
        bl.addWidget(self.btn_bg_clear)
        self.bg_info = QLabel("Background ortalaması: —")
        self.bg_info.setWordWrap(True)
        bl.addWidget(self.bg_info)
        lay.addWidget(bg)

        legend = QLabel("<b>Çizgiler</b><br>"
                        "<span style='color:#9a9a9a'>━</span> hücre sınırı (numaralı)<br>"
                        "<span style='color:#d4b000'>━</span> seçili hücre (ölçülür)<br>"
                        "<span style='color:#ff00ff'>━</span> çekirdek sınırı (DAPI'den)<br>"
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
        self.selected: set[int] = set()
        self.manual_boxes: list[tuple[int, int, int, int]] = []
        self.boxes: list[tuple[int, int, int, int]] = []
        self._auto_cache = None  # (analysis id, size, n) → kutular

        self.view = ImageView()
        self.setCentralWidget(self.view)
        self.panel = InfoPanel()
        self.panel.gain.valueChanged.connect(lambda _: self.redraw(fit=False))
        self.view.clicked.connect(self.on_click)
        self.view.box_moved.connect(self.on_box_moved)
        p = self.panel
        p.btn_all.clicked.connect(self.select_all)
        p.btn_none.clicked.connect(self.select_none)
        p.bg_auto.toggled.connect(lambda _: self.update_measure())
        p.bg_size.valueChanged.connect(lambda _: self.update_measure())
        p.bg_n.valueChanged.connect(lambda _: self.update_measure())
        p.btn_bg_clear.clicked.connect(self.clear_manual_boxes)
        scroll = QScrollArea()
        scroll.setWidget(self.panel)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        dock = QDockWidget("Görüntü bilgisi ve ayarlar", self)
        dock.setWidget(scroll)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        dock.setMinimumWidth(330)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

        self.table = make_table(TABLE_COLS)
        self.bg_table = make_table(BG_COLS)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.table, "Hücreler")
        self.tabs.addTab(self.bg_table, "Background kutuları")
        tdock = QDockWidget("CTCF ölçümü  —  CTCF = IntDen − (Alan × background ortalaması)", self)
        tdock.setWidget(self.tabs)
        tdock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, tdock)
        self.resizeDocks([tdock], [190], Qt.Orientation.Vertical)
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
                self.selected, self.manual_boxes = set(), []
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
        self.selected &= set(a.cell_ids)
        self.update_measure(redraw=False)
        self.redraw(fit=first)
        self.statusBar().showMessage(f"{len(a.cell_ids)} hücre bulundu. Ölçmek için hücrelere tıklayın "
                                     "veya 'Tüm hücreleri seç'.")
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
        self.view.set_pixmap(to_pixmap(core.overlay(disp, a.labels, self.selected, [], nuclei,
                                                    nucleus_color=NUCLEUS_COLOR, nucleus_width=1)), fit)
        self.view.set_boxes(self.boxes)

    # ------------------------------------------------------ seçim / ölçüm
    def on_click(self, y, x):
        a = self.analysis
        if a is None:
            return
        for b in list(self.manual_boxes):
            if b[0] <= y < b[2] and b[1] <= x < b[3]:
                self.manual_boxes.remove(b)
                self.update_measure()
                return
        cid = int(a.labels[y, x])
        if cid:
            self.selected ^= {cid}
        elif self.panel.bg_manual.isChecked():
            box = core.box_at(y, x, self.panel.bg_size.value(), a.labels.shape)
            y0, x0, y1, x1 = box
            if (a.labels[y0:y1, x0:x1] > 0).any():
                self.statusBar().showMessage("⚠️ Kutu bir hücreye taşıyor — biraz daha uzağa tıklayın.", 5000)
                return
            self.manual_boxes.append(box)
        else:
            self.statusBar().showMessage("Boş alana tıklandı. Elle background için sağ panelde 'Elle' seçin.", 5000)
            return
        self.update_measure()

    def on_box_moved(self, i, y0, x0):
        a = self.analysis
        if a is None or i >= len(self.boxes):
            return
        oy0, ox0, oy1, ox1 = self.boxes[i]
        new = (y0, x0, y0 + oy1 - oy0, x0 + ox1 - ox0)
        if (a.labels[new[0]:new[2], new[1]:new[3]] > 0).any():
            self.statusBar().showMessage("⚠️ Kutu bir hücreye taşıyor — eski yerine döndü.", 5000)
            self.view.set_boxes(self.boxes)
            return
        if self.panel.bg_auto.isChecked():
            # otomatik kutu taşındı → kutular elle moduna geçer (diğerleri yerinde kalır)
            self.manual_boxes = list(self.boxes)
            self.manual_boxes[i] = new
            self.panel.bg_manual.setChecked(True)  # update_measure'ü tetikler
            self.statusBar().showMessage("Otomatik kutu taşındı → Background 'Elle' moduna geçti.", 5000)
        else:
            self.manual_boxes[i] = new
            self.update_measure()

    def select_all(self):
        if self.analysis:
            self.selected = set(self.analysis.cell_ids)
            self.update_measure()

    def select_none(self):
        self.selected = set()
        self.update_measure()

    def clear_manual_boxes(self):
        self.manual_boxes = []
        self.update_measure()

    def update_measure(self, redraw=True):
        a = self.analysis
        if a is None:
            return
        p = self.panel
        s = core.Settings(bg_size=p.bg_size.value(), bg_n=p.bg_n.value())
        if p.bg_auto.isChecked():
            key = (id(a), s.bg_size, s.bg_n)
            if self._auto_cache is None or self._auto_cache[0] != key:
                _, _, boxes = core.background_and_measure(a, [], s)
                self._auto_cache = (key, boxes)
            self.boxes = list(self._auto_cache[1])
        else:
            self.boxes = list(self.manual_boxes)
        p.btn_bg_clear.setEnabled(p.bg_manual.isChecked() and bool(self.manual_boxes))
        p.sel_info.setText(f"Seçili: {len(self.selected)} / {len(a.cell_ids)} hücre")
        if self.boxes:
            cells, bg, _ = core.background_and_measure(a, sorted(self.selected), s, self.boxes)
            msg = f"Background ortalaması: <b>{bg['Mean'].mean():.3f}</b>  (n = {len(bg)} kutu, " \
                  f"{s.bg_size}×{s.bg_size} px)"
            if (bg["Max"] > a.threshold * 0.5).any():
                msg += "<br><span style='color:#a60'>⚠️ Bazı kutularda sinyal/debris olabilir.</span>"
            if bg["Max"].max() == 0:
                msg += ("<br><span style='color:#555'>ℹ️ Kutulardaki tüm pikseller 0: kamera siyah seviyesi "
                        "kırpılmış (Fiji'de de 0). Bu durumda CTCF = IntDen olur; tüm görüntüler aynı "
                        "ayarla çekildiyse sorun değildir. Ayrıntı: alttaki 'Background kutuları' sekmesi.</span>")
            p.bg_info.setText(msg)
        else:
            cells = bg = None
            p.bg_info.setText("<span style='color:#b22'>Background kutusu yok — CTCF hesaplanamaz.</span>"
                              + (" Görüntüye tıklayarak kutu ekleyin." if p.bg_manual.isChecked() else
                                 " Kutu boyutunu küçültün."))
        self.fill_table(cells)
        fill(self.bg_table, BG_COLS, bg)
        self.tabs.setTabText(1, f"Background kutuları ({len(bg) if bg is not None else 0})")
        if redraw:
            self.redraw()

    def fill_table(self, cells):
        fill(self.table, TABLE_COLS, cells)
        if cells is None or not len(cells):
            return
        unit = cells["Area_unit"].iloc[0]
        self.table.horizontalHeaderItem(1).setText(f"Alan ({unit})")

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
