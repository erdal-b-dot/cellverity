# PyInstaller tarifi — ICC CTCF Ölçer 2 (masaüstü). Derleme: ./build_mac.sh  /  build_windows.bat
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
a = Analysis(
    ["desktop.py"],
    pathex=["."],
    datas=[("assets/icon.png", "assets"), ("docs/kilavuz.html", "docs"), ("docs/user_guide.html", "docs"),
           ("locales/en.json", "locales")],
    hiddenimports=collect_submodules("skimage.feature") + collect_submodules("skimage.segmentation")
    + collect_submodules("skimage.measure") + collect_submodules("skimage.filters")
    + collect_submodules("skimage.morphology") + collect_submodules("skimage.draw")
    + collect_submodules("scipy._external") + collect_submodules("scipy.stats")
    + ["matplotlib.backends.backend_qtagg", "openpyxl", "roifile", "tifffile", "scipy.stats"],
    excludes=["streamlit", "streamlit_image_coordinates", "pyarrow", "tkinter", "IPython", "jupyter",
              "PySide6.QtWebEngineCore", "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="ICC CTCF Olcer", console=False,
          icon="assets/icon.ico" if sys.platform == "win32" else "assets/icon.icns")
coll = COLLECT(exe, a.binaries, a.datas, name="ICC CTCF Olcer")
if sys.platform == "darwin":
    app = BUNDLE(coll, name="ICC CTCF Ölçer.app", icon="assets/icon.icns", bundle_identifier="tr.edu.cbu.icc-ctcf",
                 info_plist={"CFBundleShortVersionString": "2.0.0", "NSHighResolutionCapable": True,
                             "LSMinimumSystemVersion": "12.0", "NSHumanReadableCopyright": "© Erdal Balcan, MIT"})
