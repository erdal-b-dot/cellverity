#!/bin/zsh
# Bağımsız macOS uygulaması derler (Python gerekmez). İki paket üretir:
#   dist/CellVerity_<sürüm>_mac_AppleSilicon.zip  (M1/M2/M3/M4, macOS 12.3+)
#   dist/CellVerity_<sürüm>_mac_Intel.zip         (Intel, macOS 12.0+; Apple Silicon'da Rosetta ile derlenir)
# Paketler macOS 12 (Monterey) uyumlu tekerleklerle kurulur; bu Mac'in yeni (macOS 14) paketleri kullanılmaz.
set -e
cd "${0:A:h}"
VER=$(grep -m1 '^VERSION = ' desktop.py | cut -d'"' -f2)
build() {  # $1 = arm64 | x64   $2 = uv python   $3 = platform   $4 = arch komutu
  uv venv --clear --python "$2" ".build-$1" -q
  uv pip install -q --python ".build-$1/bin/python" --python-platform "$3" -r requirements-desktop.txt pyinstaller==6.16.0
  $=4 ".build-$1/bin/pyinstaller" --noconfirm --clean --distpath "dist/$1" --workpath "build/$1" cellverity.spec
  $=4 "dist/$1/CellVerity.app/Contents/MacOS/CellVerity" --selftest examples/PARC_control/Image_11305.jpg examples/PARC_control/Image_11306.jpg
  echo 'Beklenen / Expected: "cells": 47, "nuclei": 46, "bar_um": 20.0, "english": true, "system_language": tr/en'
  rm -f selftest_result.json
}
build arm64 3.12 aarch64-apple-darwin "arch -arm64"
ditto -c -k --keepParent "dist/arm64/CellVerity.app" "dist/CellVerity_${VER}_mac_AppleSilicon.zip"
if arch -x86_64 /usr/bin/true 2>/dev/null; then
  uv python install cpython-3.12-macos-x86_64-none -q
  build x64 cpython-3.12-macos-x86_64-none x86_64-apple-darwin "arch -x86_64"
  ditto -c -k --keepParent "dist/x64/CellVerity.app" "dist/CellVerity_${VER}_mac_Intel.zip"
else
  echo "Rosetta yok: Intel paketi atlandı (softwareupdate --install-rosetta)."
fi
ls -lh dist/*.zip

# Sürükle-bırak kurulum paketleri (.dmg)
./make_dmg.sh
