"""ICC CTCF Ölçer 2.0 — bağımsız masaüstü arayüzü (PySide6/Qt).

Hesaplamalar core.py'dedir (ölçüm tanımları ImageJ/Fiji ile birebir aynı). v2 çekirdek algılaması
parlak çekirdek gövdesini kullanır (core.Settings.nuc_bright_core); v1.0.0 Streamlit sürümü eskisini kullanır.
Çalıştırma:  .venv/bin/python desktop.py   (Windows: .venv\\Scripts\\python desktop.py)
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from PySide6.QtCore import QObject, QRectF, QSettings, Qt, QThread, Signal
from PySide6.QtGui import (QAction, QActionGroup, QBrush, QColor, QFont, QImage, QKeySequence, QPainter,
                           QPainterPath, QPen, QPixmap)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog,
                               QDockWidget, QLineEdit, QPlainTextEdit, QProgressBar,
                               QFileDialog, QFormLayout, QFrame, QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QMainWindow,
                               QDoubleSpinBox, QMessageBox, QPushButton, QRadioButton, QScrollArea,
                               QSlider, QSpinBox,
                               QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

import batch
import core
import fiji
import report
from batch import guess_kind

APP_NAME = "ICC CTCF Ölçer"
VERSION = "2.0.0"
IMAGE_FILTER = "Görüntüler (*.jpg *.jpeg *.tif *.tiff *.png)"
AUTOSAVE = Path.home() / "Documents" / "ICC CTCF Olcer" / "otomatik_kayit.xlsx"


def result_meta(a: core.Analysis, fitc: Path, dapi: Path | None, group: str, bg_mode: str, bg_size: int,
                bg_n: int, note: str = "", experiment: str = "", edits: str = "", fiji_check: str = "") -> dict:
    """Her hücre satırına yazılan bağlam (yöntem bölümü ve tekrarlanabilirlik için)."""
    return {"Group": group, "Experiment": experiment, "Image": fitc.name, "Image_path": str(fitc), "DAPI_image": dapi.name if dapi else "",
            "Channel": "G", "um_per_px": a.um_per_px or np.nan, "Scale_bar_um": a.bar_um,
            "Scale_source": a.bar_um_source, "Objective": a.objective[0] if a.objective else np.nan,
            "BG_mode": bg_mode, "BG_box_px": bg_size, "BG_n": bg_n,
            "Segmentation": a.segmentation_mode,
            "Nucleus_method": a.nuc_method,
            "DAPI_overlap": a.dapi_overlap if a.dapi_overlap is not None else np.nan,
            "Touching_pairs": "; ".join(f"{i}-{j}" for i, j in a.touching),
            "Cells_in_field": len(a.cell_ids),
            "Nuclei_in_field": int(a.nuclei.max()) if a.nuclei is not None else np.nan,
            "Selection": note, "Manual_edits": edits, "Fiji_check": fiji_check, "App_version": VERSION, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")}


def is_dapi_like(arr: np.ndarray) -> bool:
    """Mavi kanalın baskın olduğu (DAPI) görüntüyü tanır; sürükle-bırakta FITC/DAPI ayrımı için."""
    return guess_kind(arr) == "DAPI"


def message(parent, kind: str, text: str, ask: bool = False) -> bool:
    """Qt'nin kendi ileti penceresi. macOS'un yerel uyarı penceresi (NSAlert) bazı macOS sürümlerinde
    simgesini çizerken programı çökertiyor (2026-10-31, Darwin 27) → yerel pencere kullanılmaz."""
    box = QMessageBox(parent)
    box.setOption(QMessageBox.Option.DontUseNativeDialog, True)
    box.setWindowTitle(APP_NAME)
    box.setText(text)
    box.setIcon({"warning": QMessageBox.Icon.Warning, "critical": QMessageBox.Icon.Critical,
                 "question": QMessageBox.Icon.Question}.get(kind, QMessageBox.Icon.Information))
    if ask:
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.Yes)
    return box.exec() == QMessageBox.StandardButton.Yes


VIEW_MODES = ("FITC", "DAPI", "Birleşik (FITC + DAPI)")
NUCLEUS_COLOR = (255, 0, 255)  # mor: hem yeşil hem mavi zeminde görünür
TABLE_COLS = [("Cell", "Hücre", 0), ("Area", "Alan", 2), ("Mean", "Mean", 3), ("StdDev", "StdDev", 3),
              ("Min", "Min", 0), ("Max", "Max", 0), ("IntDen", "IntDen", 1), ("RawIntDen", "RawIntDen", 0),
              ("CTCF", "CTCF", 1), ("Saturated_px", "Doymuş px", 0)]
RES_COLS = [("Group", "Grup", None), ("Experiment", "Deney", None), ("Image", "Görüntü", None), ("Cell", "Hücre", 0), ("Area", "Alan", 2),
            ("Mean", "Mean", 3), ("IntDen", "IntDen", 1), ("BG_Mean", "BG Mean", 3), ("CTCF", "CTCF", 1),
            ("Objective", "Objektif", 0)]
SUM_COLS = [("Group", "Grup", None), ("n", "n", 0), ("Mean", "Ortalama", 1), ("SD", "SD", 1),
            ("SEM", "SEM", 1), ("Median", "Medyan", 1), ("Min", "Min", 1), ("Max", "Max", 1)]
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
    names = [c[0] for c in cols]
    for r, row in enumerate(df.reindex(columns=names).itertuples(index=False, name=None)):
        for c, (col, _, dec) in enumerate(cols):
            v = row[c]  # sütun adında boşluk/parantez olabilir → konumla eriş
            if dec is None or isinstance(v, str):
                txt = str(v)
            elif v != v:  # NaN
                txt = "—"
            else:
                txt = f"{v:,.{dec}f}".replace(",", " ") if dec else f"{int(v)}"
            it = QTableWidgetItem(txt)
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
    path_drawn = Signal(list)          # çizim/bölme modunda fareyle çizilen yol [(x, y), …]
    DRAW_MODES = ("split", "draw")
    BOX_COLOR = QColor(255, 60, 60)

    def __init__(self):
        super().__init__()
        self._press = None
        self._drag = None  # (kutu indeksi, fare ile kutu köşesi arasındaki fark)
        self.mode = "select"
        self._path = None  # çizilmekte olan yol (sahne koordinatları)
        self._path_item = None
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

    def set_mode(self, mode):
        self.mode = mode
        self.setDragMode(QGraphicsView.DragMode.NoDrag if mode in self.DRAW_MODES
                         else QGraphicsView.DragMode.ScrollHandDrag)
        self.viewport().setCursor(Qt.CursorShape.CrossCursor if mode != "select" else Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, e):
        self._press = e.position().toPoint()
        alt = bool(e.modifiers() & Qt.KeyboardModifier.AltModifier)
        if self.mode in self.DRAW_MODES and e.button() == Qt.MouseButton.LeftButton and not alt:
            pt = self.mapToScene(self._press)
            self._path = [(pt.x(), pt.y())]
            color = QColor(0, 230, 255) if self.mode == "split" else QColor(255, 220, 0)
            pen = QPen(color, 2)
            pen.setCosmetic(True)  # yakınlaştırmadan bağımsız kalınlık
            self._path_item = self.scene().addPath(QPainterPath(), pen)
            return
        if self.mode in self.DRAW_MODES and alt:  # ⌥ + sürükle → kaydır
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        if e.button() == Qt.MouseButton.LeftButton and self.mode == "select":
            pt = self.mapToScene(self._press)
            i = self.box_at(pt)
            if i is not None:
                self._drag = (i, pt - self.box_items[i][0].pos())
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._path is not None:
            pt = self.mapToScene(e.position().toPoint())
            self._path.append((pt.x(), pt.y()))
            path = QPainterPath()
            path.moveTo(*self._path[0])
            for x, y in self._path[1:]:
                path.lineTo(x, y)
            if self.mode == "draw" and len(self._path) > 2:
                path.lineTo(*self._path[0])
            self._path_item.setPath(path)
            return
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
        if not e.buttons() and self.mode == "select":
            over = self.box_at(self.mapToScene(e.position().toPoint())) is not None
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor if over else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, e):
        if self._path is not None:
            pts, self._path = self._path, None
            self.scene().removeItem(self._path_item)
            self._path_item = None
            if len(pts) >= 2 and (e.position().toPoint() - self._press).manhattanLength() >= 5:
                self.path_drawn.emit(pts)
            self._press = None
            return
        if self.mode in self.DRAW_MODES:
            super().mouseReleaseEvent(e)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._press = None
            return
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

    def __init__(self, fitc, meta, dapi, settings):
        super().__init__()
        self.args = fitc, meta, dapi, settings

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
        self.bar_um = QDoubleSpinBox()
        self.bar_um.setRange(0, 5000)
        self.bar_um.setDecimals(0)
        self.bar_um.setSuffix(" µm")
        self.bar_um.setSpecialValueText("otomatik (etiketten)")
        self.bar_um.setToolTip("Ölçek çubuğunun altında yazan değer. 'otomatik' = program etiketi okur.\n"
                               "Yanlış okunduysa buraya doğru değeri yazın.")
        form.insertRow(2, "<b>Ölçek çubuğu</b>", self.bar_um)
        lay.addLayout(form)
        self.calib_warn = QLabel()
        self.calib_warn.setWordWrap(True)
        self.calib_warn.setStyleSheet("background:#fbe4e4; color:#922; padding:6px; border-radius:4px;")
        self.calib_warn.hide()
        lay.addWidget(self.calib_warn)
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

        res = QGroupBox("Sonuçlar")
        rl = QVBoxLayout(res)
        f3 = QFormLayout()
        self.group = QLineEdit("Kontrol")
        self.group.setToolTip("Bu görüntünün ait olduğu grup/koşul, ör. 'CD44 ilaçsız', 'Ax 10 µM 24 sa'.\n"
                              "Grafik ve istatistik bu etikete göre gruplanır.")
        f3.addRow("Grup / koşul", self.group)
        self.experiment = QLineEdit("1")
        self.experiment.setToolTip("Bağımsız deney (biyolojik tekrar) numarası/adı, ör. 1, 2, 3 ya da 'Deney_1'.\n"
                                   "İstatistiği deney ortalamaları üzerinden yapmak için gerekir.")
        f3.addRow("Deney / tekrar", self.experiment)
        rl.addLayout(f3)
        self.btn_add = QPushButton("➕ Sonuç tablosuna ekle")
        self.btn_add.setStyleSheet("font-weight:bold; padding:6px;")
        self.btn_add.setToolTip("Seçili hücrelerin ölçümlerini biriken tabloya ekler (⌘↩ / Ctrl+Enter).\n"
                                "Aynı görüntü yeniden eklenirse eskisinin yerine geçer.")
        rl.addWidget(self.btn_add)
        self.res_info = QLabel("Biriken: 0 hücre")
        self.res_info.setWordWrap(True)
        rl.addWidget(self.res_info)
        row = QHBoxLayout()
        self.btn_excel = QPushButton("Excel'e kaydet…")
        self.btn_plot = QPushButton("Grafik…")
        row.addWidget(self.btn_excel)
        row.addWidget(self.btn_plot)
        rl.addLayout(row)
        lay.addWidget(res)

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
        elif a.nuclei is not None and a.dapi_overlap is not None and a.dapi_overlap < 0.5:
            self.mode.setText(f"⚠️ <b>DAPI bu FITC ile aynı alana ait görünmüyor</b> — çekirdeklerin "
                              f"%{100 * (1 - a.dapi_overlap):.0f}'i hücrelerin dışında kalıyor. Aynı alanın DAPI "
                              "görüntüsünü açın (dosya numaraları ardışık olsa bile alan farklı olabilir).")
            self.mode.setStyleSheet("background:#fbe4e4; color:#922; padding:6px; border-radius:4px;")
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


# ------------------------------------------------------------- Klasör işleme
class BatchWorker(QObject):
    progress = Signal(int, int, str)
    item_done = Signal(object, object, object, object)  # item, Analysis, cells, bg
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, mode, payload):
        super().__init__()
        self.mode, self.payload, self.stop = mode, payload, False

    def run(self):
        try:
            if self.mode == "scan":
                folder, recursive = self.payload
                self.finished.emit(batch.scan(folder, recursive, lambda i, n, t: self.progress.emit(i, n, t)))
            else:
                items, s, edge = self.payload
                errors = []
                for k, it in enumerate(items):
                    if self.stop:
                        break
                    self.progress.emit(k, len(items), f"Ölçülüyor: {it.fitc.name}")
                    try:
                        a, cells, bg = batch.measure(it, s, edge)
                        self.item_done.emit(it, a, cells, bg)
                    except Exception as ex:  # bir görüntü bozuksa diğerleri sürsün
                        errors.append(f"{it.fitc.name}: {type(ex).__name__}: {ex}")
                self.finished.emit(errors)
        except Exception as ex:
            self.failed.emit(f"{type(ex).__name__}: {ex}")


class BatchDialog(QDialog):
    COLS = ["Ölç", "Grup", "Deney", "FITC", "DAPI", "Örtüşme", "Durum"]

    def __init__(self, main):
        super().__init__(main)
        self.main, self.items, self._thread = main, [], None
        self.setWindowTitle("Klasörü toplu ölç")
        self.resize(980, 620)
        lay = QVBoxLayout(self)
        intro = QLabel("Klasördeki görüntüler FITC/DAPI olarak tanınır; her FITC, aynı klasördeki yakın numaralı "
                       "DAPI'ler arasından <b>gerçekten aynı alana ait olanla</b> (çekirdek–hücre örtüşmesi ≥ %50) "
                       "eşleştirilir. Grup = alt klasör adı; deney = onun üstündeki klasör (ör. Deney_1/Kontrol/…) — "
                       "ikisini de tabloda değiştirebilirsiniz. Her görüntüde tüm "
                       "hücreler ve otomatik background ölçülür; sağ paneldeki kutu boyutu/sayısı kullanılır.")
        intro.setWordWrap(True)
        lay.addWidget(intro)
        row = QHBoxLayout()
        self.btn_folder = QPushButton("Klasör seç…")
        self.folder_lbl = QLabel("—")
        self.recursive = QCheckBox("Alt klasörler dahil")
        self.recursive.setChecked(True)
        row.addWidget(self.btn_folder)
        row.addWidget(self.folder_lbl, 1)
        row.addWidget(self.recursive)
        lay.addLayout(row)
        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table, 1)
        self.edge = QCheckBox("Görüntü kenarına değen (kesik) hücreleri hariç tut")
        self.edge.setChecked(True)
        self.edge.setToolTip("Kenarda kesilmiş hücrenin alanı ve IntDen'i eksik ölçülür; genellikle hariç tutulur.")
        lay.addWidget(self.edge)
        self.bar = QProgressBar()
        self.bar.hide()
        self.status = QLabel()
        self.status.setWordWrap(True)
        lay.addWidget(self.bar)
        lay.addWidget(self.status)
        row = QHBoxLayout()
        row.addStretch()
        self.btn_run = QPushButton("Seçilenleri ölç ve tabloya ekle")
        self.btn_run.setStyleSheet("font-weight:bold; padding:6px 14px;")
        self.btn_run.setEnabled(False)
        self.btn_close = QPushButton("Kapat")
        row.addWidget(self.btn_run)
        row.addWidget(self.btn_close)
        lay.addLayout(row)
        self.btn_folder.clicked.connect(self.choose)
        self.btn_run.clicked.connect(self.run)
        self.btn_close.clicked.connect(self.reject)

    def _start(self, mode, payload, done):
        self.bar.show()
        self.bar.setValue(0)
        for b in (self.btn_folder, self.btn_run, self.btn_close):
            b.setEnabled(False)
        self._thread = QThread(self)
        self._worker = BatchWorker(mode, payload)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.on_progress)
        self._worker.item_done.connect(self.on_item)
        self._worker.finished.connect(done)
        self._worker.failed.connect(self.on_fail)
        self._thread.start()

    def _stop(self):
        self._thread.quit()
        self._thread.wait()
        self._thread = None
        self.bar.hide()
        for b in (self.btn_folder, self.btn_close):
            b.setEnabled(True)
        self.btn_run.setEnabled(any(it.use for it in self.items))

    def on_progress(self, i, n, text):
        self.bar.setMaximum(max(n, 1))
        self.bar.setValue(i)
        self.status.setText(text)

    def on_fail(self, msg):
        self._stop()
        message(self, "critical", f"Hata:\n{msg}")

    def choose(self, folder: str | None = None):
        if not folder:
            start = str(self.main.fitc[0].parent) if self.main.fitc else str(Path.home())
            folder = QFileDialog.getExistingDirectory(self, "Görüntü klasörünü seçin", start)
        if folder:
            self.folder = Path(folder)
            self.folder_lbl.setText(str(self.folder))
            self._start("scan", (self.folder, self.recursive.isChecked()), self.on_scanned)

    def on_scanned(self, items):
        self._stop()
        self.items = items
        self.table.setRowCount(len(items))
        for r, it in enumerate(items):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Checked if it.use else Qt.CheckState.Unchecked)
            if it.fitc is None:
                chk.setFlags(Qt.ItemFlag.NoItemFlags)
            self.table.setItem(r, 0, chk)
            self.table.setItem(r, 1, QTableWidgetItem(it.group))
            self.table.setItem(r, 2, QTableWidgetItem(it.experiment))
            for c, txt in ((3, it.fitc.name if it.fitc else "—"), (4, it.dapi.name if it.dapi else "—"),
                           (5, f"%{100 * it.overlap:.0f}" if it.overlap is not None else "—"), (6, it.status)):
                cell = QTableWidgetItem(txt)
                cell.setFlags(Qt.ItemFlag.ItemIsEnabled)
                if c == 6:
                    color = "#2a7" if it.status == "hazır" else ("#c80" if it.status.startswith("DAPI") else "#999")
                    cell.setForeground(QColor(color))
                self.table.setItem(r, c, cell)
        ready = sum(it.status == "hazır" for it in items)
        nod = sum(it.status.startswith("DAPI yok") for it in items)
        skip = sum(it.status.startswith("atlandı") for it in items)
        self.status.setText(f"<b>{ready}</b> çift hazır · <span style='color:#c80'>{nod} FITC'nin DAPI'si "
                            f"bulunamadı</span> (yalnız şekle göre ayrılır) · <span style='color:#999'>{skip} dosya "
                            "atlandı</span> (merge, işlenmiş, eşleşmeyen DAPI). Ölçülmesini istemediklerinizin "
                            "işaretini kaldırın.")
        self.btn_run.setEnabled(any(it.use for it in items))

    def run(self):
        todo = []
        for r, it in enumerate(self.items):
            if it.fitc is not None and self.table.item(r, 0).checkState() == Qt.CheckState.Checked:
                it.group = self.table.item(r, 1).text().strip() or it.group
                it.experiment = self.table.item(r, 2).text().strip()
                todo.append(it)
        if not todo:
            return
        p = self.main.panel
        self.settings = core.Settings(bg_size=p.bg_size.value(), bg_n=p.bg_n.value())
        self.n_cells = 0
        self._start("measure", (todo, self.settings, self.edge.isChecked()), self.on_measured)

    def on_item(self, it, a, cells, bg):
        if cells is None or not len(cells):
            return
        meta = result_meta(a, it.fitc, it.dapi, it.group, "auto", self.settings.bg_size, len(bg),
                           "batch: all cells" + (", edge excluded" if self.edge.isChecked() else ""),
                           it.experiment)
        self.main.add_measurement(cells, bg, meta)
        self.n_cells += len(cells)

    def on_measured(self, errors):
        self._stop()
        txt = f"Bitti: {self.n_cells} hücre biriken tabloya eklendi."
        if errors:
            txt += "\n\nÖlçülemeyenler:\n" + "\n".join(errors)
        self.status.setText(txt.replace("\n", "<br>"))
        self.main.tabs.setCurrentIndex(2)

    def reject(self):
        if self._thread is None:
            super().reject()


# ------------------------------------------------------------- Fiji köprüsü
class FijiWorker(QObject):
    finished = Signal(object, str)
    failed = Signal(str)

    def __init__(self, exe, tif, rois, upp):
        super().__init__()
        self.args = exe, tif, rois, upp

    def run(self):
        try:
            df, ver = fiji.measure_in_fiji(*self.args)
            self.finished.emit(df, ver)
        except Exception as ex:
            self.failed.emit(str(ex))


class TableDialog(QDialog):
    """Bir tabloyu (ve isteğe bağlı grafiği) gösterir; CSV/Excel olarak kaydedilebilir."""

    def __init__(self, parent, title, df, header_html="", fig_fn=None, extra_buttons=()):
        super().__init__(parent)
        self.df = df
        self.setWindowTitle(title)
        self.resize(1100, 640 if fig_fn else 480)
        lay = QVBoxLayout(self)
        head = QLabel(header_html)
        head.setWordWrap(True)
        head.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(head)
        if fig_fn is not None:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            from matplotlib.figure import Figure
            self.fig = Figure(dpi=100, layout="constrained")
            fig_fn(self.fig)
            lay.addWidget(FigureCanvasQTAgg(self.fig), 3)
        cols = [(c, c, None if df[c].dtype == object else (0 if str(df[c].dtype).startswith("int") else 4))
                for c in df.columns]
        t = make_table(cols)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        fill(t, [(c, c, d) for c, _, d in cols], df.rename(columns=lambda c: c))
        lay.addWidget(t, 2)
        row = QHBoxLayout()
        for text, fn in extra_buttons:
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        row.addStretch()
        b = QPushButton("Kaydet (Excel)…")
        b.clicked.connect(self.save)
        row.addWidget(b)
        if fig_fn is not None:
            b = QPushButton("Grafiği kaydet (PNG 600 dpi)…")
            b.clicked.connect(self.save_fig)
            row.addWidget(b)
        b = QPushButton("Kapat")
        b.clicked.connect(self.accept)
        row.addWidget(b)
        lay.addLayout(row)

    def save(self):
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        path, _ = QFileDialog.getSaveFileName(self, "Kaydet", str(Path.home() / f"{self.windowTitle()}_{stamp}.xlsx"),
                                              "Excel (*.xlsx)")
        if path:
            self.df.to_excel(path, index=False)

    def save_fig(self):
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        path, _ = QFileDialog.getSaveFileName(self, "Grafiği kaydet", str(Path.home() / f"Bland_Altman_{stamp}.png"),
                                              "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)")
        if path:
            self.fig.savefig(path, dpi=600, bbox_inches="tight")


# ------------------------------------------------------------- Grafik penceresi
class PlotDialog(QDialog):
    """GraphPad tarzı: kontrol grubu, grup sırası, istatistik düzeyi (hücre/görüntü/deney), Dunnett/Tukey."""

    def __init__(self, parent, results):
        super().__init__(parent)
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        self.results = results
        self.setWindowTitle("Grafik ve istatistik")
        self.resize(1100, 700)
        lay = QHBoxLayout(self)
        self.fig = Figure(dpi=110, layout="constrained")  # pencere boyutu değişince eksen yazıları kesilmesin
        self.canvas = FigureCanvasQTAgg(self.fig)
        lay.addWidget(self.canvas, 3)
        side = QVBoxLayout()
        groups = list(dict.fromkeys(results["Group"]))
        form = QFormLayout()
        self.control_box = QComboBox()
        self.control_box.addItems(groups)
        guess = next((g for g in groups if g.lower().startswith(("kontrol", "control", "ctrl", "ilaçsız"))), None)
        if guess:
            self.control_box.setCurrentText(guess)
        self.control_box.setToolTip("Dunnett testinde ve normalizasyonda referans alınan grup (GraphPad'deki "
                                    "'control column').")
        self.metric_box = QComboBox()
        self.metric_box.addItems(list(report.METRICS))
        self.level_box = QComboBox()
        for k, v in report.LEVELS.items():
            self.level_box.addItem(v, k)
        has_exp = "Experiment" in results and results["Experiment"].astype(str).str.strip().replace(
            {"nan": ""}).ne("").any() and results.groupby("Group")["Experiment"].nunique().min() >= 2
        self.level_box.setCurrentIndex(2 if has_exp else 1)
        self.level_box.setToolTip("Testte n neyi sayıyor? Hücreler aynı deneyden geldiği için bağımsız değildir;\n"
                                  "yayın için bağımsız deney ortalamaları önerilir.")
        self.cmp_box = QComboBox()
        for k, v in report.COMPARISONS.items():
            self.cmp_box.addItem(v, k)
        self.kind_box = QComboBox()
        self.kind_box.addItems(report.PLOT_KINDS)
        form.addRow("Kontrol grubu", self.control_box)
        form.addRow("Değişken", self.metric_box)
        form.addRow("İstatistik birimi", self.level_box)
        form.addRow("Çoklu karşılaştırma", self.cmp_box)
        form.addRow("Grafik tipi", self.kind_box)
        side.addLayout(form)
        side.addWidget(QLabel("<b>Grup sırası</b> (sürükleyerek değiştirin; kontrol hep başta)"))
        from PySide6.QtWidgets import QListWidget
        self.order_list = QListWidget()
        self.order_list.addItems(groups)
        self.order_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.order_list.setMaximumHeight(110)
        side.addWidget(self.order_list)
        self.norm_box = QCheckBox("Kontrole göre normalize et (kontrol = 1)")
        self.stars_box = QCheckBox("Anlamlılık yıldızlarını göster")
        self.stars_box.setChecked(True)
        side.addWidget(self.norm_box)
        side.addWidget(self.stars_box)
        self.stats = QPlainTextEdit()
        self.stats.setReadOnly(True)
        side.addWidget(self.stats, 1)
        row = QHBoxLayout()
        for fmt in ("png", "pdf", "svg"):
            b = QPushButton(f"{fmt.upper()}{' 600 dpi' if fmt == 'png' else ''}")
            b.setToolTip(f"Grafiği {fmt.upper()} olarak kaydet")
            b.clicked.connect(lambda _, f=fmt: self.save(f))
            row.addWidget(b)
        b = QPushButton("İstatistik metni")
        b.setToolTip("İstatistik sonucunu .txt olarak kaydet")
        b.clicked.connect(self.save_txt)
        row.addWidget(b)
        side.addWidget(QLabel("<b>Kaydet</b>"))
        side.addLayout(row)
        lay.addLayout(side, 2)
        for w in (self.control_box, self.metric_box, self.level_box, self.cmp_box, self.kind_box):
            w.currentIndexChanged.connect(self.draw)
        for w in (self.norm_box, self.stars_box):
            w.toggled.connect(self.draw)
        self.order_list.model().rowsMoved.connect(lambda *_: self.draw())
        self.draw()

    def draw(self):
        order = [self.order_list.item(i).text() for i in range(self.order_list.count())]
        _, txt = report.plot(self.results, self.metric_box.currentText(), self.kind_box.currentText(),
                             self.norm_box.isChecked(), fig=self.fig, level=self.level_box.currentData(),
                             control=self.control_box.currentText(), order=order,
                             comparison=self.cmp_box.currentData(), stars=self.stars_box.isChecked())
        self.stats.setPlainText(txt)
        self.canvas.draw()

    def _path(self, ext, title):
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        start = str(Path.home() / f"CTCF_{self.metric_box.currentText()}_{self.level_box.currentData()}_{stamp}.{ext}")
        path, _ = QFileDialog.getSaveFileName(self, title, start, f"{ext.upper()} (*.{ext})")
        return path

    def save(self, fmt):
        path = self._path(fmt, "Grafiği kaydet")
        if path:
            self.fig.savefig(path, format=fmt, dpi=600 if fmt == "png" else None, bbox_inches="tight")

    def save_txt(self):
        path = self._path("txt", "İstatistik metnini kaydet")
        if path:
            head = (f"Değişken: {self.metric_box.currentText()}\nİstatistik birimi: {self.level_box.currentText()}\n"
                    f"Kontrol: {self.control_box.currentText()}\n\n")
            Path(path).write_text(head + self.stats.toPlainText(), encoding="utf-8")


# ---------------------------------------------------------------- Ana pencere
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {VERSION}")
        self.resize(1400, 900)
        self.setAcceptDrops(True)
        self.fitc = self.dapi = None  # (Path, arr, meta)
        self.results = pd.DataFrame()     # biriken hücre ölçümleri (tüm görüntüler)
        self.bg_results = pd.DataFrame()
        self.cur_cells = self.cur_bg = None
        self._dirty = False               # kaydedilmemiş sonuç var mı
        self.fiji_check = ""
        self.validation = pd.DataFrame()  # elle (Fiji) vs otomatik ROI karşılaştırmaları (yöntem doğrulaması)
        self.settings_store = QSettings("ErdalBalcan", "ICC CTCF Olcer")
        self.analysis: core.Analysis | None = None
        self._thread = None
        self._pending = False  # analiz sürerken yeni görüntü gelirse bitince yeniden çalıştır
        self.selected: set[int] = set()
        self.undo_stack, self.redo_stack = [], []   # (labels, selected, edit_log) anlık görüntüleri
        self.edit_log: list[str] = []
        self._merge_first = None
        self.manual_boxes: list[tuple[int, int, int, int]] = []
        self.boxes: list[tuple[int, int, int, int]] = []
        self._auto_cache = None  # (analysis id, size, n) → kutular

        self.view = ImageView()
        self.setCentralWidget(self.view)
        self.panel = InfoPanel()
        self.panel.gain.valueChanged.connect(lambda _: self.redraw(fit=False))
        self.panel.bar_um.editingFinished.connect(self.run_analysis)
        self.view.clicked.connect(self.on_click)
        self.view.box_moved.connect(self.on_box_moved)
        self.view.path_drawn.connect(self.on_path)
        p = self.panel
        p.btn_all.clicked.connect(self.select_all)
        p.btn_none.clicked.connect(self.select_none)
        p.bg_auto.toggled.connect(lambda _: self.update_measure())
        p.bg_size.valueChanged.connect(lambda _: self.update_measure())
        p.bg_n.valueChanged.connect(lambda _: self.update_measure())
        p.btn_bg_clear.clicked.connect(self.clear_manual_boxes)
        p.btn_add.clicked.connect(self.add_to_results)
        p.btn_excel.clicked.connect(lambda: self.export_results("xlsx"))
        p.btn_plot.clicked.connect(self.show_plot)
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
        self.res_table = make_table(RES_COLS)
        self.sum_table = make_table(SUM_COLS)
        self.tabs.addTab(self.table, "Hücreler")
        self.tabs.addTab(self.bg_table, "Background kutuları")
        self.tabs.addTab(self.res_table, "Biriken sonuçlar (0)")
        self.tabs.addTab(self.sum_table, "Grup özeti (CTCF)")
        tdock = QDockWidget("CTCF ölçümü  —  CTCF = IntDen − (Alan × background ortalaması)", self)
        tdock.setWidget(self.tabs)
        tdock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, tdock)
        self.resizeDocks([tdock], [190], Qt.Orientation.Vertical)
        self._build_actions()
        self.refresh_results()
        self.panel.btn_add.setEnabled(False)
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
        self.a_close = act("Görüntüleri kapat", self.close_images, QKeySequence.StandardKey.Close)
        self.a_close.setToolTip("Açık FITC ve DAPI görüntülerini kapatır (⌘W / Ctrl+W).")
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
        m.addActions([self.a_fitc, self.a_dapi, self.a_close])
        m.addSeparator()
        m.addAction(act("Çıkış", self.close, QKeySequence.StandardKey.Quit))
        self.a_add = act("Sonuç tablosuna ekle", self.add_to_results, "Ctrl+Return")
        self.a_xlsx = act("Excel olarak kaydet…", lambda: self.export_results("xlsx"), "Ctrl+E")
        self.a_csv = act("CSV olarak kaydet…", lambda: self.export_results("csv"))
        self.a_plot = act("Grafik ve istatistik…", self.show_plot, "Ctrl+G")
        self.a_roi = act("ROI görüntüsü (PNG)…", self.export_roi_png)
        self.a_ij = act("ImageJ/Fiji karşılaştırma paketi (ZIP)…", self.export_imagej)
        self.a_reset = act("Biriken sonuçları sıfırla…", self.reset_results)
        self.a_batch = act("Klasörü toplu ölç…", self.batch_dialog, "Ctrl+B")
        self.a_batch.setToolTip("Bir klasördeki tüm FITC/DAPI çiftlerini bulur ve hepsini ölçer.")
        self.a_load = act("Önceki sonuçları aç (Excel)…", self.load_excel)
        m = self.menuBar().addMenu("Sonuçlar")
        m.addActions([self.a_add, self.a_batch])
        m.addSeparator()
        m.addActions([self.a_xlsx, self.a_csv, self.a_load, self.a_plot])
        m.addSeparator()
        m.addActions([self.a_roi, self.a_ij])
        m.addSeparator()
        m.addAction(self.a_reset)
        self.edit_group = QActionGroup(self)
        self.edit_acts = {}
        tips = {"select": ("Seç", "Hücreye tıklayarak seçin/bırakın; kutuları sürükleyin; görüntüyü sürükleyerek kaydırın."),
                "split": ("Böl", "Yapışık hücrelerin üzerine ayırma çizgisi çekin → hücre çizgiden bölünür.\n"
                                 "Kaydırmak için ⌥ (Option/Alt) tuşuyla sürükleyin."),
                "merge": ("Birleştir", "Önce bir hücreye, sonra birleşeceği komşusuna tıklayın."),
                "delete": ("Sil", "Hücre olmayan (debris) ya da yanlış bulunmuş bölgeye tıklayın."),
                "draw": ("Çiz", "Programın kaçırdığı/yanlış çizdiği hücrenin sınırını fareyle çizin (bırakınca kapanır).\n"
                                "Çizilen alan diğer hücrelerin üzerine yazar. Kaydırmak için ⌥ ile sürükleyin.")}
        for key, (txt, tip) in tips.items():
            a_ = QAction(txt, self, checkable=True)
            a_.setToolTip(f"<b>{txt}</b><br>{tip.replace(chr(10), '<br>')}")
            a_.triggered.connect(lambda _, k=key: self.set_edit_mode(k))
            self.edit_group.addAction(a_)
            self.edit_acts[key] = a_
        self.edit_acts["select"].setChecked(True)
        self.a_undo = act("Geri al", self.undo, QKeySequence.StandardKey.Undo)
        self.a_redo = act("Yinele", self.redo, QKeySequence.StandardKey.Redo)
        self.a_undo.setEnabled(False)
        self.a_redo.setEnabled(False)
        self.a_fiji_verify = act("Fiji ile doğrula", self.fiji_verify, "Ctrl+Shift+F")
        self.a_fiji_verify.setToolTip("Seçili hücreleri ve background kutularını Fiji'nin kendi 'Measure' motoruna "
                                      "arka planda ölçtürür ve sonuçları programınkilerle yan yana koyar.")
        self.a_fiji_open = act("Fiji'de aç (görüntü + ROI'ler + Measure)", self.fiji_open)
        self.a_manual = act("Fiji'de elle çizilmiş ROI'lerle karşılaştır (RoiSet.zip)…", self.manual_compare)
        self.a_valid = act("Yöntem doğrulama tablosu ve Bland–Altman…", self.show_validation)
        self.a_fiji_path = act("Fiji konumunu seç…", self.choose_fiji)
        m = self.menuBar().addMenu("Fiji")
        m.addActions([self.a_fiji_verify, self.a_fiji_open])
        m.addSeparator()
        m.addActions([self.a_manual, self.a_valid])
        m.addSeparator()
        m.addAction(self.a_fiji_path)
        m = self.menuBar().addMenu("Düzelt")
        m.addActions(list(self.edit_acts.values()))
        m.addSeparator()
        m.addActions([self.a_undo, self.a_redo])
        m = self.menuBar().addMenu("Görünüm")
        m.addActions([self.a_fit, self.a_in, self.a_out])
        m.addSeparator()
        m.addAction(self.a_nuc)
        m = self.menuBar().addMenu("Yardım")
        m.addAction(act("Kullanım kılavuzu", self.open_manual, QKeySequence.StandardKey.HelpContents))
        m.addAction(act("Hakkında", self.about))

        tb = self.addToolBar("Araçlar")
        tb.setMovable(False)
        tb.addActions([self.a_fitc, self.a_dapi, self.a_close])
        tb.addSeparator()
        tb.addActions([self.a_fit, self.a_in, self.a_out])
        tb.addSeparator()
        tb.addWidget(QLabel(" Görüntü: "))
        tb.addWidget(self.view_mode)
        tb.addAction(self.a_nuc)
        tb.addSeparator()
        self.addToolBarBreak()
        tb2 = self.addToolBar("Sınır düzeltme")
        tb2.setMovable(False)
        tb2.addWidget(QLabel(" Sınır düzeltme: "))
        tb2.addActions(list(self.edit_acts.values()))
        tb2.addSeparator()
        tb2.addActions([self.a_undo, self.a_redo])
        self.edit_info = QLabel()
        self.edit_info.setStyleSheet("color:#666; padding-left:8px;")
        tb2.addWidget(self.edit_info)
        tb2.addSeparator()
        tb2.addWidget(QLabel(" Sonuçlar: "))
        tb2.addActions([self.a_add, self.a_batch, self.a_xlsx, self.a_plot])
        tb2.addSeparator()
        tb2.addAction(self.a_fiji_verify)

    # ---------------------------------------------------------- dosya açma
    def close_images(self):
        if self._thread is not None:
            return
        self.fitc = self.dapi = self.analysis = None
        self.selected, self.manual_boxes, self.boxes = set(), [], []
        self.cur_cells = self.cur_bg = None
        self.panel.btn_add.setEnabled(False)
        self.edit_log, self.undo_stack, self.redo_stack = [], [], []
        self._update_edit_ui()
        self.view.set_boxes([])
        self.view.item.setPixmap(QPixmap())
        self.view.placeholder.show()
        p = self.panel
        for key in p.fields:
            p.set(key, "—")
        p.set_mode(None)
        p.bar_um.setValue(0)
        p.calib_warn.hide()
        p.sel_info.setText("Seçili: —")
        p.bg_info.setText("Background ortalaması: —")
        p.bg_auto.setChecked(True)
        self.fill_table(None)
        fill(self.bg_table, BG_COLS, None)
        self.statusBar().showMessage("Görüntüler kapatıldı — yeni FITC ve DAPI çiftini sürükleyin.")

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
                message(self, "warning", f"{p.name} açılamadı:\n{ex}")
        loaded.sort(key=lambda t: is_dapi_like(t[1]))  # önce FITC, sonra DAPI
        for p, arr, meta in loaded:
            self._set(p, arr, meta, "DAPI" if is_dapi_like(arr) else "FITC", run=False)
        if loaded:
            self.run_analysis()

    def load(self, path: Path, kind: str):
        try:
            arr, meta = core.load_image(str(path))
        except Exception as ex:
            message(self, "warning", f"{path.name} açılamadı:\n{ex}")
            return
        looks = guess_kind(arr)
        if looks is not None and looks != kind:
            color = "mavi" if looks == "DAPI" else "yeşil"
            if message(self, "question", f"{path.name} bir {looks} görüntüsüne benziyor ({color} baskın), "
                       f"ama {kind} olarak açılıyor.\n\n{looks} olarak açılsın mı?", ask=True):
                kind = looks
        self._set(path, arr, meta, kind)

    def _set(self, path, arr, meta, kind, run=True):
        if kind == "FITC":
            if self.fitc is None or self.fitc[0] != path:
                self.analysis = None
                self.selected, self.manual_boxes = set(), []
                self.panel.bar_um.setValue(0)  # yeni görüntü → etiketten oku
                if self.fitc is not None and self.dapi is not None:  # önceki alanın DAPI'si yanlış ayırır
                    self.dapi = None
                    self.panel.set("DAPI", "— (yeni FITC açıldı; aynı alanın DAPI'sini açın)")
            self.fitc = (path, arr, meta)
            self.panel.set("FITC", path.name)
            if path.suffix.lower() in (".jpg", ".jpeg") and not meta.get("model") and not meta.get("software"):
                message(self, "warning", f"{path.name}: kamera bilgisi (EXIF) yok.\n\nBu genellikle birleştirilmiş "
                        "(merge) ya da başka programda yeniden kaydedilmiş bir görüntü demektir. CTCF için "
                        "mikroskobun doğrudan kaydettiği tek kanal FITC görüntüsünü kullanın.")
            if meta.get("software"):
                message(self, "warning", f"Görüntü yazılımla işlenmiş görünüyor: {meta['software']}.\n"
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
            message(self, "warning", "FITC ve DAPI görüntülerinin boyutları farklı; DAPI kullanılmadı.")
            dapi = None
        self.statusBar().showMessage("Hücreler algılanıyor…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self._thread = QThread(self)
        bar = self.panel.bar_um.value()
        self._worker = AnalysisWorker(arr, meta, dapi, core.Settings(bar_um=bar or None))
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
        message(self, "critical", f"Analiz sırasında hata:\n{msg}")

    def on_done(self, a: core.Analysis):
        first = self.analysis is None
        if self.edit_log:
            self.statusBar().showMessage("Yeniden analiz edildi: önceki elle düzeltmeler sıfırlandı.", 8000)
        self.edit_log, self.undo_stack, self.redo_stack = [], [], []
        self._update_edit_ui()
        self._stop_thread()
        self.analysis = a
        p = self.panel
        if a.um_per_px:
            src = {"label": "etiketten okundu", "user": "elle girildi",
                   "default": "etiket OKUNAMADI, varsayıldı"}[a.bar_um_source]
            p.set("Kalibrasyon", f"{a.um_per_px:.4f} µm/piksel  (çubuk {a.scale_bar.bar_px} px = "
                                 f"{a.bar_um:g} µm, {src})")
            if a.bar_um_source == "default":
                p.calib_warn.setText("⚠️ Ölçek çubuğunun değeri okunamadı; 20 µm varsayıldı. Görüntünün sağ alt "
                                     "köşesindeki değere bakıp yukarıdaki 'Ölçek çubuğu' kutusuna yazın — yanlış "
                                     "değer alan ve IntDen'i kat kat değiştirir.")
                p.calib_warn.show()
            else:
                p.calib_warn.hide()
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
        mode = self.view.mode
        if mode in ("delete", "merge"):
            cid = int(a.labels[y, x])
            if not cid:
                self.statusBar().showMessage("Bir hücrenin içine tıklayın.", 4000)
                return
            if mode == "delete":
                self.apply_edit(core.delete_cell(a.labels, cid), f"sil {cid}")
                return
            if self._merge_first is None or self._merge_first == cid:
                self._merge_first = cid
                self.statusBar().showMessage(f"Hücre {cid} seçildi — şimdi birleşeceği komşu hücreye tıklayın.")
                return
            first, self._merge_first = self._merge_first, None
            if first in self.selected or cid in self.selected:
                self.selected |= {first}
            self.apply_edit(core.merge_cells(a.labels, first, cid), f"birleştir {first}+{cid}")
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

    # ------------------------------------------------- elle sınır düzeltme
    def set_edit_mode(self, mode):
        self._merge_first = None
        self.view.set_mode(mode)
        hints = {"select": "", "split": "Ayırma çizgisini hücrenin bir kenarından öbürüne çekin.",
                 "merge": "Birleştirilecek iki hücreye sırayla tıklayın.", "delete": "Silinecek bölgeye tıklayın.",
                 "draw": "Hücre sınırını fareyle çizin; bırakınca kapanır."}
        self.statusBar().showMessage(hints[mode], 6000)

    def on_path(self, pts):
        a = self.analysis
        if a is None:
            return
        if self.view.mode == "split":
            new, split = core.split_cells(a.labels, pts)
            if not split:
                self.statusBar().showMessage("Çizgi hiçbir hücreyi ikiye ayırmadı — hücrenin bir kenarından "
                                             "öbür kenarına kadar çekin.", 6000)
                return
            parent_sel = set(split) & self.selected
            new_ids = set(np.unique(new)) - set(np.unique(a.labels))
            if parent_sel:
                self.selected |= {int(i) for i in new_ids}
            self.apply_edit(new, "böl " + ",".join(map(str, split)))
        elif self.view.mode == "draw":
            new, cid = core.add_cell(a.labels, pts, a.exclude)
            if not cid:
                self.statusBar().showMessage("Çizilen alan çok küçük.", 4000)
                return
            self.selected.add(cid)
            self.apply_edit(new, f"çiz {cid}")

    def apply_edit(self, labels, note):
        a = self.analysis
        self.undo_stack.append((a.labels, set(self.selected), list(self.edit_log)))
        del self.undo_stack[:-30]
        self.redo_stack.clear()
        self._set_labels(labels)
        self.edit_log.append(note)
        self._update_edit_ui()
        self.statusBar().showMessage(f"✓ {note}  (geri almak için ⌘Z / Ctrl+Z)", 5000)

    def _set_labels(self, labels):
        self.analysis = core.relabeled(self.analysis, labels)
        self.selected &= set(self.analysis.cell_ids)
        self.panel.set("Hücre sayısı", f"{len(self.analysis.cell_ids)}"
                       + (" (elle düzeltildi)" if self.edit_log or self.undo_stack else ""))
        self.update_measure()

    def undo(self):
        if not self.undo_stack or self.analysis is None:
            return
        self.redo_stack.append((self.analysis.labels, set(self.selected), list(self.edit_log)))
        labels, sel, log = self.undo_stack.pop()
        self.selected, self.edit_log = sel, log
        self._set_labels(labels)
        self._update_edit_ui()

    def redo(self):
        if not self.redo_stack or self.analysis is None:
            return
        self.undo_stack.append((self.analysis.labels, set(self.selected), list(self.edit_log)))
        labels, sel, log = self.redo_stack.pop()
        self.selected, self.edit_log = sel, log
        self._set_labels(labels)
        self._update_edit_ui()

    def _update_edit_ui(self):
        self.a_undo.setEnabled(bool(self.undo_stack))
        self.a_redo.setEnabled(bool(self.redo_stack))
        self.edit_info.setText(f"{len(self.edit_log)} elle düzeltme" if self.edit_log else "")

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
        self.cur_cells, self.cur_bg = cells, bg
        self.fiji_check = ""  # seçim/kutu/sınır değişti → önceki Fiji doğrulaması geçersiz
        p.btn_add.setEnabled(cells is not None and len(cells) > 0)
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

    # ------------------------------------------------------- sonuçlar
    def add_to_results(self):
        a, cells = self.analysis, self.cur_cells
        if a is None or cells is None or not len(cells):
            self.statusBar().showMessage("Önce hücre seçin (tıklayın veya 'Tüm hücreleri seç').", 5000)
            return
        group = self.panel.group.text().strip() or "Grup"
        fpath = self.fitc[0]
        meta = result_meta(a, fpath, self.dapi[0] if self.dapi else None, group,
                           "auto" if self.panel.bg_auto.isChecked() else "manual",
                           self.panel.bg_size.value(), len(self.cur_bg), "manual click",
                           self.panel.experiment.text().strip(), "; ".join(self.edit_log), self.fiji_check)
        replaced = len(self.results) and (self.results["Image_path"] == str(fpath)).any()
        self.add_measurement(cells, self.cur_bg, meta)
        self.tabs.setCurrentIndex(2)
        self.statusBar().showMessage(f"{len(cells)} hücre '{group}' grubuna eklendi"
                                     + (" (bu görüntünün önceki ölçümünün yerine)." if replaced else "."), 6000)

    def add_measurement(self, cells, bg, meta):
        self.results = report.add_image(self.results, cells, meta)
        self.bg_results = report.add_background(self.bg_results, bg, meta["Image"], meta["Image_path"],
                                                meta["Group"])
        self._dirty = True
        self.autosave()
        self.refresh_results()

    def autosave(self):
        """Her eklemeden sonra Belgeler/ICC CTCF Olcer/otomatik_kayit.xlsx — çökme/elektrik kesintisine karşı."""
        try:
            AUTOSAVE.parent.mkdir(parents=True, exist_ok=True)
            report.write_excel(AUTOSAVE, self.results, self.bg_results, VERSION, self.validation)
        except Exception as ex:  # otomatik kayıt başarısızlığı ölçümü durdurmasın
            self.statusBar().showMessage(f"Otomatik kayıt yapılamadı: {ex}", 6000)

    def load_excel(self, path: Path | None = None):
        """Daha önce kaydedilmiş Excel'i (Cells + Background) yükler → kaldığınız yerden devam."""
        if path is None:
            fn, _ = QFileDialog.getOpenFileName(self, "Önceki sonuçları aç (Excel)", str(Path.home()),
                                                "Excel (*.xlsx)")
            if not fn:
                return
            path = Path(fn)
        try:
            cells = pd.read_excel(path, sheet_name="Cells")
            try:
                bg = pd.read_excel(path, sheet_name="Background")
            except ValueError:
                bg = pd.DataFrame()
            try:
                self.validation = pd.read_excel(path, sheet_name="Validation")
            except ValueError:
                pass
        except Exception as ex:
            message(self, "warning", f"{path.name} okunamadı:\n{ex}\n\nBu programın kaydettiği Excel olmalı "
                    "('Cells' sayfası).")
            return
        if "Image_path" not in cells:
            cells["Image_path"] = cells.get("Image", "")
        if len(bg) and "Image_path" not in bg:
            bg["Image_path"] = bg.get("Image", "")
        if len(self.results):  # açık tabloyla birleştir; aynı görüntü varsa Excel'deki geçerli
            new = set(cells["Image_path"])
            cells = pd.concat([self.results[~self.results["Image_path"].isin(new)], cells], ignore_index=True)
            if len(self.bg_results):
                bg = pd.concat([self.bg_results[~self.bg_results["Image_path"].isin(new)], bg], ignore_index=True)
        self.results, self.bg_results = report.ordered(cells), bg
        self._dirty = path == AUTOSAVE
        self.refresh_results()
        self.tabs.setCurrentIndex(2)
        self.statusBar().showMessage(f"{path.name}: {len(self.results)} hücre yüklendi — eklemeye devam edebilirsiniz.",
                                     8000)

    def offer_restore(self):
        if not AUTOSAVE.exists():
            return
        try:
            n = len(pd.read_excel(AUTOSAVE, sheet_name="Cells"))
        except Exception:
            return
        when = datetime.fromtimestamp(AUTOSAVE.stat().st_mtime).strftime("%d.%m.%Y %H:%M")
        if n and message(self, "question", f"Son oturumdan otomatik kaydedilmiş {n} hücrelik sonuç var "
                         f"({when}).\n\nKaldığınız yerden devam edilsin mi?", ask=True):
            self.load_excel(AUTOSAVE)

    def batch_dialog(self):
        BatchDialog(self).exec()

    def refresh_results(self):
        if len(self.results) and "Experiment" not in self.results:  # eski Excel'ler
            self.results["Experiment"] = ""
        r = self.results
        fill(self.res_table, RES_COLS, r if len(r) else None)
        fill(self.sum_table, SUM_COLS, report.group_summary(r) if len(r) else None)
        n_img = r["Image_path"].nunique() if len(r) else 0
        n_grp = r["Group"].nunique() if len(r) else 0
        self.tabs.setTabText(2, f"Biriken sonuçlar ({len(r)})")
        self.panel.res_info.setText(f"Biriken: <b>{len(r)}</b> hücre, {n_img} görüntü, {n_grp} grup"
                                    + ("  <span style='color:#a60'>(kaydedilmedi)</span>" if self._dirty else "")
                                    + (f"<br><span style='color:#b22'>{report.mixed_objectives(r)}</span>"
                                       if len(r) and report.mixed_objectives(r) else ""))
        for w in (self.panel.btn_excel, self.panel.btn_plot):
            w.setEnabled(len(r) > 0)
        for a_ in (self.a_xlsx, self.a_csv, self.a_plot, self.a_reset):
            a_.setEnabled(len(r) > 0)

    def _save_path(self, title, name, filt):
        start = str((self.fitc[0].parent if self.fitc else Path.home()) / name)
        path, _ = QFileDialog.getSaveFileName(self, title, start, filt)
        return Path(path) if path else None

    def export_results(self, fmt):
        if not len(self.results):
            return False
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        if fmt == "xlsx":
            path = self._save_path("Excel olarak kaydet", f"CTCF_{stamp}.xlsx", "Excel (*.xlsx)")
        else:
            path = self._save_path("CSV olarak kaydet", f"CTCF_{stamp}.csv", "CSV (*.csv)")
        if path is None:
            return False
        try:
            if fmt == "xlsx":
                report.write_excel(path, self.results, self.bg_results, VERSION, self.validation)
            else:
                report.write_csv(path, self.results)
        except Exception as ex:
            message(self, "critical", f"Kaydedilemedi:\n{ex}\n\nDosya Excel'de açıksa kapatıp yeniden deneyin.")
            return False
        self._dirty = False
        self.refresh_results()
        self.statusBar().showMessage(f"Kaydedildi: {path}", 8000)
        return True

    def export_roi_png(self):
        a = self.analysis
        if a is None:
            return
        path = self._save_path("ROI görüntüsünü kaydet", f"ROI_{self.fitc[0].stem}.png", "PNG (*.png)")
        if path:
            disp = core.to_display(a.fitc_arr, self.panel.gain.value() / 10)
            core.overlay(disp, a.labels, self.selected, self.boxes, a.nuclei, nucleus_color=NUCLEUS_COLOR,
                         nucleus_width=1).save(path)
            self.statusBar().showMessage(f"Kaydedildi: {path}", 8000)

    def export_imagej(self):
        a = self.analysis
        if a is None or not self.selected:
            self.statusBar().showMessage("ImageJ paketi için önce hücre seçin.", 5000)
            return
        base = self.fitc[0].stem
        path = self._save_path("ImageJ/Fiji paketini kaydet", f"ImageJ_{base}.zip", "ZIP (*.zip)")
        if path:
            path.write_bytes(core.imagej_export_zip(a.fitc_ch, a.labels, sorted(self.selected), self.boxes, base))
            message(self, "info", f"Kaydedildi: {path.name}\n\nFiji'de: TIFF'i açın → Analyze ▸ Set Scale: "
                    f"{a.scale_bar.bar_px} piksel = {a.bar_um:g} µm → ROI Manager ▸ Open: RoiSet.zip → Measure.\n"
                    "Ayrıntılar ZIP içindeki NASIL_KULLANILIR.txt dosyasında.")

    def reset_results(self):
        if len(self.results) and message(self, "question", f"Biriken {len(self.results)} hücrelik tablo silinsin mi?"
                                         + ("\n\nKaydedilmemiş sonuçlar kaybolur." if self._dirty else ""),
                                         ask=True):
            self.results, self.bg_results, self._dirty = pd.DataFrame(), pd.DataFrame(), False
            AUTOSAVE.unlink(missing_ok=True)
            self.refresh_results()

    def show_plot(self):
        if len(self.results):
            PlotDialog(self, self.results).exec()

    def closeEvent(self, e):
        if self._dirty and len(self.results):
            if message(self, "question", f"Kaydedilmemiş {len(self.results)} hücrelik sonuç var.\n\n"
                       "Çıkmadan önce Excel'e kaydetmek ister misiniz?", ask=True):
                if not self.export_results("xlsx"):
                    e.ignore()
                    return
        e.accept()

    # ---------------------------------------------------------- Fiji
    def fiji_exe(self, ask=True):
        exe = fiji.find_fiji(self.settings_store.value("fiji_path", "") or None)
        if exe is None and ask:
            message(self, "info", "Fiji bulunamadı. Bir sonraki pencerede Fiji klasörünü (ya da Fiji.app'i) "
                    "seçin.\n\nFiji yüklü değilse: https://imagej.net/software/fiji/downloads")
            exe = self.choose_fiji()
        return exe

    def choose_fiji(self):
        d = QFileDialog.getExistingDirectory(self, "Fiji klasörünü seçin (Fiji / Fiji.app)", str(Path.home()))
        if not d:
            return None
        exe = fiji.resolve(d)
        if exe is None:
            message(self, "warning", f"{d} içinde Fiji başlatıcısı bulunamadı.")
            return None
        self.settings_store.setValue("fiji_path", str(exe))
        self.statusBar().showMessage(f"Fiji: {exe}", 6000)
        return exe

    def _fiji_package(self, folder: Path):
        a = self.analysis
        ids = sorted(self.selected) or list(a.cell_ids)
        return fiji.write_package(folder, a, ids, self.boxes, self.fitc[0].stem), ids

    def fiji_verify(self):
        a = self.analysis
        if a is None or self._thread is not None:
            return
        exe = self.fiji_exe()
        if exe is None:
            return
        import tempfile
        self._fiji_tmp = tempfile.TemporaryDirectory()
        (tif, rois), ids = self._fiji_package(Path(self._fiji_tmp.name))
        cells, bg, _ = core.background_and_measure(a, ids, core.Settings(bg_size=self.panel.bg_size.value(),
                                                                         bg_n=self.panel.bg_n.value()), self.boxes)
        self._fiji_app = (cells, bg)
        self.statusBar().showMessage(f"Fiji arka planda ölçüyor ({len(ids)} hücre + {len(self.boxes)} kutu)…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self._thread = QThread(self)
        self._worker = FijiWorker(exe, tif, rois, a.um_per_px)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self.on_fiji_done)
        self._worker.failed.connect(self.on_fiji_fail)
        self._thread.start()

    def on_fiji_fail(self, msg):
        self._stop_thread()
        self._fiji_tmp.cleanup()
        self.statusBar().showMessage("Fiji ölçümü başarısız.", 6000)
        message(self, "critical", msg)

    def on_fiji_done(self, df, ver):
        self._stop_thread()
        self._fiji_tmp.cleanup()
        cells, bg = self._fiji_app
        cmp = fiji.compare(cells, bg, df)
        worst = cmp["Max fark (%)"].max()
        missing = int(cmp.isna().any(axis=1).sum())
        ok = worst < 1e-3 and not missing
        self.fiji_check = f"OK ({ver}, max fark {worst:.1e} %)" if ok else f"FARK VAR (max {worst:.3g} %)"
        head = (f"<b>{'✅ Birebir aynı' if ok else '⚠️ Fark var'}</b> — {len(cmp)} ROI ({len(cells)} hücre, "
                f"{len(bg)} background kutusu), Fiji {ver}. En büyük fark: <b>{worst:.2g} %</b>"
                + (f", eşleşmeyen ROI: {missing}" if missing else "")
                + "<br>Fiji, programın dışa aktardığı TIFF ve RoiSet.zip'i kendi <i>Measure</i> motoruyla ölçtü "
                  "(Area, Mean, StdDev, Min, Max, IntDen, RawIntDen). Bu sonuç, görüntü sonuç tablosuna "
                  "eklendiğinde Excel'de <i>Fiji_check</i> sütununa yazılır.")
        self.statusBar().showMessage(f"Fiji doğrulaması: {self.fiji_check}", 10000)
        TableDialog(self, "Fiji doğrulaması", cmp, head).exec()

    def fiji_open(self):
        a = self.analysis
        if a is None:
            return
        exe = self.fiji_exe()
        if exe is None:
            return
        folder = AUTOSAVE.parent / "Fiji" / self.fitc[0].stem
        (tif, rois), ids = self._fiji_package(folder)
        fiji.open_in_fiji(exe, tif, rois, a.scale_bar.bar_px, a.bar_um)
        self.statusBar().showMessage(f"Fiji açılıyor: {len(ids)} hücre + {len(self.boxes)} kutu, ölçek "
                                     f"{a.scale_bar.bar_px} px = {a.bar_um:g} µm. Dosyalar: {folder}", 10000)

    def manual_compare(self):
        a = self.analysis
        if a is None:
            self.statusBar().showMessage("Önce FITC (ve DAPI) görüntüsünü açın.", 5000)
            return
        fn, _ = QFileDialog.getOpenFileName(self, "Fiji'de elle çizilmiş ROI'ler (RoiSet.zip / .roi)",
                                            str(self.fitc[0].parent), "ImageJ ROI (*.zip *.roi)")
        if not fn:
            return
        try:
            man = core.read_imagej_rois(Path(fn).read_bytes(), a.labels.shape)
        except Exception as ex:
            message(self, "warning", f"ROI dosyası okunamadı:\n{ex}")
            return
        man = [(n, m) for n, m in man if not n.upper().startswith("BG")]
        bg_mean = float(self.cur_bg["Mean"].mean()) if self.cur_bg is not None and len(self.cur_bg) else 0.0
        cmp = core.compare_manual(a.fitc_ch, a.labels, man, bg_mean, a.um_per_px)
        if not len(cmp):
            message(self, "warning", "Dosyada hücre ROI'si bulunamadı.")
            return
        cmp.insert(0, "Image", self.fitc[0].name)
        cmp.insert(1, "Group", self.panel.group.text().strip())
        cmp["Nucleus_method"] = a.nuc_method
        cmp["Manual_edits"] = "; ".join(self.edit_log)
        cmp["Image_path"] = str(self.fitc[0])

        def add():
            v = self.validation
            if len(v):
                v = v[v["Image_path"] != str(self.fitc[0])]
            self.validation = pd.concat([v, cmp], ignore_index=True)
            if len(self.results):
                self.autosave()
            self.statusBar().showMessage(f"Doğrulama tablosu: {len(self.validation)} hücre, "
                                         f"{self.validation['Image'].nunique()} görüntü.", 6000)
            dlg.accept()
            self.show_validation()

        head = (f"<b>{len(cmp)} elle çizilmiş ROI</b> ↔ otomatik hücreler (aynı background: {bg_mean:.3f}). "
                f"Ortalama Dice {cmp['Dice'].mean():.3f}; CTCF farkı ortalama {cmp['CTCF_diff_%'].mean():+.1f} %.<br>"
                "Birden çok görüntüde yapıp <b>doğrulama tablosuna ekleyin</b> → Bland–Altman analizi.")
        dlg = TableDialog(self, "Elle vs otomatik", cmp.drop(columns=["Image_path"]), head,
                          extra_buttons=[("➕ Doğrulama tablosuna ekle", add)])
        dlg.exec()

    def show_validation(self):
        v = self.validation
        if not len(v):
            message(self, "info", "Doğrulama tablosu boş. Fiji ▸ 'Elle çizilmiş ROI'lerle karşılaştır' ile "
                    "görüntü ekleyin.")
            return
        st = report.agreement(v)
        TableDialog(self, "Yöntem doğrulaması (elle vs otomatik)", v.drop(columns=["Image_path"]),
                    report.agreement_text(st).replace("\n", "<br>"),
                    fig_fn=lambda f: report.bland_altman_plot(v, fig=f)).exec()

    def open_manual(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        path = resource("docs/kilavuz.html")
        if not path.exists():
            message(self, "warning", f"Kılavuz bulunamadı: {path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def about(self):
        message(self, "info",
                f"<b>{APP_NAME} {VERSION}</b><br>Immunositokimya görüntülerinde CTCF ölçümü.<br><br>"
                          "CTCF = IntDen − (Area × Mean background)<br>McCloy et al., 2014, <i>Cell Cycle</i><br><br>"
                          "Ölçümler ImageJ/Fiji ile birebir aynıdır.<br>"
                "Atıf: <a href='https://doi.org/10.5281/zenodo.23860020'>doi:10.5281/zenodo.23860020</a> (v2.0.0: 10.5281/zenodo.23860021)<br>"
                "© Erdal Balcan, MIT lisansı")


def resource(rel: str) -> Path:
    """Paketlenmiş (.app/.exe) sürümde dosyalar PyInstaller'ın açtığı klasördedir."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / rel


def selftest(fitc: str, dapi: str) -> int:
    """Paketlenmiş sürümü pencere açmadan sınar: analiz, ölçüm, Excel, grafik, Qt grafik tuvali."""
    import json
    import tempfile
    f, m = core.load_image(fitc)
    d = core.load_image(dapi)[0]
    a = core.analyze(f, m, d)
    cells, bg, _ = core.background_and_measure(a, a.cell_ids)
    meta = result_meta(a, Path(fitc), Path(dapi), "test", "auto", 50, len(bg))
    res = report.add_image(pd.DataFrame(), cells, meta)
    with tempfile.TemporaryDirectory() as t:
        report.write_excel(Path(t) / "x.xlsx", res, bg, VERSION)
        report.plot(res)[0].savefig(Path(t) / "x.png")
        ok_xlsx = (Path(t) / "x.xlsx").stat().st_size > 0
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg  # noqa: F401
    out = json.dumps({"version": VERSION, "bar_um": a.bar_um, "um_per_px": a.um_per_px, "cells": len(a.cell_ids),
                      "nuclei": int(a.nuclei.max()), "area": cells["Area"].round(2).tolist(),
                      "ctcf": cells["CTCF"].round(1).tolist(), "excel": ok_xlsx}, ensure_ascii=False)
    Path("selftest_result.json").write_text(out, encoding="utf-8")  # Windows'ta pencereli .exe'nin konsolu yok
    if sys.stdout is not None:
        print(out)
    return 0


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--selftest":
        sys.exit(selftest(sys.argv[2], sys.argv[3]))
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    from PySide6.QtGui import QIcon
    app.setWindowIcon(QIcon(str(resource("assets/icon.png"))))
    w = MainWindow()
    w.show()
    if len(sys.argv) < 2:
        w.offer_restore()
    for arg in sys.argv[1:3]:  # komut satırından: desktop.py FITC.jpg [DAPI.jpg]
        p = Path(arg)
        arr, meta = core.load_image(str(p))
        w._set(p, arr, meta, "DAPI" if is_dapi_like(arr) else "FITC", run=False)
    if w.fitc:
        w.run_analysis()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
