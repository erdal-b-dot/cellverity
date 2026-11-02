#!/usr/bin/env bash
# Bağımsız Linux paketi derler (Python gerekmez).
#   x86_64 : Ubuntu 22.04 (glibc 2.35) üzerinde → Ubuntu 22.04+, Debian 12+, Fedora 36+, Mint 21+ vb.
#   aarch64: Ubuntu 24.04 (glibc 2.39) üzerinde → PySide6 6.9.3'ün arm64 tekerleği glibc 2.39 istiyor
# Çıktılar (dist/):
#   CellVerity_<sürüm>_Linux_<mimari>.AppImage   — tek dosya: chmod +x, çift tık
#   CellVerity_<sürüm>_Linux_<mimari>.tar.gz     — klasör: aç, ./CellVerity/CellVerity
# Kullanım:
#   ./build_linux.sh            → Docker'da (macOS/Linux; bu makinenin mimarisinde) derler
#   ./build_linux.sh --native   → doğrudan bu Ubuntu makinesinde derler (GitHub Actions bunu kullanır)
set -euo pipefail
cd "$(dirname "$0")"
VER=$(grep -m1 '^VERSION = ' desktop.py | cut -d'"' -f2)

if [ "${1:-}" != "--native" ]; then
  # Kaba yalnızca depo dosyaları (commit edilmemiş değişiklikler dahil) gönderilir; .venv/build/dist karışmaz.
  mkdir -p dist
  case "$(uname -m)" in x86_64|amd64) BASE=ubuntu:22.04 ;; *) BASE=ubuntu:24.04 ;; esac
  git ls-files -co --exclude-standard -z | COPYFILE_DISABLE=1 tar --no-xattrs --null -T - -cf - | \
    docker run --rm -i -v "$PWD/dist:/out" "$BASE" bash -c '
      set -e; mkdir /src && cd /src && tar -xf -
      ./build_linux.sh --native && cp dist/CellVerity_*_Linux_* /out/'
  ls -lh dist/CellVerity_"${VER}"_Linux_*
  exit 0
fi

export DEBIAN_FRONTEND=noninteractive
ARCH=$(uname -m)                         # x86_64 | aarch64
SUDO=""; [ "$(id -u)" != 0 ] && SUDO="sudo"
# Qt'nin (xcb/wayland) çalışma kitaplıkları + derleme araçları
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq --no-install-recommends ca-certificates curl file binutils git \
  libgl1 libegl1 libglib2.0-0 libfontconfig1 libfreetype6 libdbus-1-3 libxkbcommon0 libxkbcommon-x11-0 \
  libx11-xcb1 libxcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
  libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 libxcb-xfixes0 libxrender1 libxi6 \
  libsm6 libice6 libwayland-client0 libwayland-cursor0 libwayland-egl1 >/dev/null
command -v uv >/dev/null || { curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null; export PATH="$HOME/.local/bin:$PATH"; }

uv venv --clear --python 3.12 .build-linux -q
uv pip install -q --python .build-linux/bin/python -r requirements-desktop.txt pyinstaller==6.16.0
.build-linux/bin/pyinstaller --noconfirm --clean --distpath dist/linux --workpath build/linux cellverity.spec

# Öz-test (ekransız)
QT_QPA_PLATFORM=offscreen dist/linux/CellVerity/CellVerity --selftest \
  examples/PARC_control/Image_11305.jpg examples/PARC_control/Image_11306.jpg
echo 'Beklenen / Expected: "cells": 47, "nuclei": 46, "bar_um": 20.0, "english": true'
.build-linux/bin/python - <<'PY'
import json; r = json.load(open("selftest_result.json"))
assert r["cells"] == 47 and r["nuclei"] == 46 and r["bar_um"] == 20.0 and r["english"] and r["excel"], r
print("Öz-test GEÇTİ / Self-test PASSED")
PY
rm -f selftest_result.json

# Temiz masaüstü kurulumlarında çoğu zaman bulunmayan küçük xcb-util kitaplıklarını pakete göm
# (Qt 6.5+ libxcb-cursor0 olmadan "could not load the Qt platform plugin xcb" hatası verir).
# OpenGL/EGL, glib, fontconfig, X11/Wayland çekirdek kitaplıkları sistemden gelir, gömülmez.
LIBDIR=/usr/lib/$ARCH-linux-gnu
for so in libxcb-cursor.so.0 libxcb-icccm.so.4 libxcb-image.so.0 libxcb-keysyms.so.1 libxcb-render-util.so.0; do
  cp -L "$LIBDIR/$so" dist/linux/CellVerity/_internal/
done

# .tar.gz
tar -C dist/linux -czf "dist/CellVerity_${VER}_Linux_${ARCH}.tar.gz" CellVerity

# AppImage
APPDIR=build/CellVerity.AppDir
rm -rf "$APPDIR"; mkdir -p "$APPDIR/usr/lib" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"
cp -a dist/linux/CellVerity "$APPDIR/usr/lib/"
cp assets/icon.png "$APPDIR/cellverity.png"; cp assets/icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/cellverity.png"
cat > "$APPDIR/cellverity.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=CellVerity
GenericName=CTCF fluorescence quantification
Comment=Verifiable per-cell fluorescence (CTCF) quantification for immunocytochemistry images
Comment[tr]=İmmünositokimya görüntülerinde doğrulanabilir hücre başına floresan (CTCF) ölçümü
Exec=CellVerity %F
Icon=cellverity
Categories=Science;Biology;Graphics;
MimeType=image/jpeg;image/tiff;image/png;
Terminal=false
DESK
cp "$APPDIR/cellverity.desktop" "$APPDIR/usr/share/applications/"
cat > "$APPDIR/AppRun" <<'RUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/CellVerity/CellVerity" "$@"
RUN
chmod +x "$APPDIR/AppRun"
TOOL=build/appimagetool-$ARCH.AppImage
[ -f "$TOOL" ] || curl -Ls -o "$TOOL" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage"
chmod +x "$TOOL"
# Kapta FUSE yok → aracı açıp çalıştır
ARCH=$ARCH APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" --no-appstream "$APPDIR" "dist/CellVerity_${VER}_Linux_${ARCH}.AppImage" >/dev/null
ls -lh dist/CellVerity_"${VER}"_Linux_*
