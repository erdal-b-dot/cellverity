# PyInstaller tarifi — CellVerity (eski adı ICC CTCF Ölçer) masaüstü programı. Derleme: ./build_mac.sh  /  build_windows.bat
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
import re
_VER = re.search(r'^VERSION = "([^"]+)"', open("desktop.py", encoding="utf-8").read(), re.M).group(1).removesuffix("-dev")
# Derleme bilgisi (Yardım ▸ Hakkında): commit + tarih; git yoksa yalnızca tarih
import datetime
import subprocess
try:
    _c = subprocess.run(["git", "log", "-1", "--format=%h"], capture_output=True, text=True, timeout=10).stdout.strip()
except Exception:
    _c = ""
open("build_info.txt", "w", encoding="utf-8").write(
    (f"commit {_c} · " if _c else "") + "built " + datetime.date.today().isoformat() + f" ({sys.platform})")
a = Analysis(
    ["desktop.py"],
    pathex=["."],
    datas=[("build_info.txt", "."), ("assets/icon.png", "assets"), ("docs/kilavuz.html", "docs"), ("docs/user_guide.html", "docs"),
           ("locales/en.json", "locales"),
           # Tema (Meriç Balcan): stylesheet ve araç çubuğu simgeleri paketin içine girmezse
           # program açılır ama tamamen renksiz/simgesiz görünür.
           ("theme.qss", "."), ("assets/icons", "assets/icons")],
    hiddenimports=collect_submodules("skimage.feature") + collect_submodules("skimage.segmentation")
    + collect_submodules("skimage.measure") + collect_submodules("skimage.filters")
    + collect_submodules("skimage.morphology") + collect_submodules("skimage.draw")
    + collect_submodules("scipy._external") + collect_submodules("scipy.stats") + collect_submodules("imagecodecs")
    + ["matplotlib.backends.backend_qtagg", "openpyxl", "roifile", "tifffile", "scipy.stats", "updates", "certifi"],
    excludes=["streamlit", "streamlit_image_coordinates", "pyarrow", "tkinter", "IPython", "jupyter",
              "PySide6.QtWebEngineCore", "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="CellVerity", console=False,
          icon="assets/icon.ico" if sys.platform == "win32" else "assets/icon.icns")
coll = COLLECT(exe, a.binaries, a.datas, name="CellVerity")
if sys.platform == "darwin":
    app = BUNDLE(coll, name="CellVerity.app", icon="assets/icon.icns", bundle_identifier="tr.edu.cbu.cellverity",
                 # Dil beyanı olmazsa macOS paketlenmiş uygulamaya sistem dili Türkçe olsa da İngilizce bildirir
                 info_plist={"CFBundleShortVersionString": _VER, "NSHighResolutionCapable": True,
                             "CFBundleDevelopmentRegion": "tr", "CFBundleLocalizations": ["tr", "en"],
                             "CFBundleAllowMixedLocalizations": True,
                             "LSMinimumSystemVersion": "12.0", "NSHumanReadableCopyright": "© Erdal Balcan, MIT"})
