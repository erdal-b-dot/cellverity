#!/bin/zsh
# dist/<arm64|x64>/CellVerity.app → dist/CellVerity_<sürüm>_mac_<AppleSilicon|Intel>.dmg
# DMG açılınca: uygulama + Uygulamalar kısayolu + KURULUM.txt (sürükle-bırak kurulum).
set -e
cd "${0:A:h}"
VER=$(grep -m1 '^VERSION = ' desktop.py | cut -d'"' -f2)
for arch name in arm64 AppleSilicon x64 Intel; do
  APP="dist/$arch/CellVerity.app"
  [[ -d "$APP" ]] || continue
  STAGE=$(mktemp -d)
  ditto "$APP" "$STAGE/CellVerity.app"
  ln -s /Applications "$STAGE/Applications"
  cat > "$STAGE/INSTALL - KURULUM.txt" <<TXT
CellVerity $VER ($name)

ENGLISH
1) Drag the 'CellVerity' icon onto the 'Applications' folder next to it.
2) First launch: in Applications, RIGHT-CLICK the app > Open > Open
   (needed once, because the app is not notarized by Apple).
3) If macOS says the app "is damaged", run once in Terminal:
   xattr -cr "/Applications/CellVerity.app"
Requires: $([[ $name == Intel ]] && echo "Intel Mac, macOS 12.0 (Monterey) or later" || echo "Apple Silicon (M1–M4), macOS 12.3 or later")
User guide: in the app, Help > User guide (F1). Interface language: View > Language / Dil.

TÜRKÇE
1) 'CellVerity' simgesini yandaki 'Uygulamalar' klasörüne sürükleyin.
2) İlk açılışta: Uygulamalar klasöründe programa SAĞ TIKLAYIN > Aç > Aç
   (program Apple'a imzalatılmadığı için bir kez gereklidir).
3) "Hasarlı" uyarısı çıkarsa Terminal'de bir kez:
   xattr -cr "/Applications/CellVerity.app"
Gereken sistem: $([[ $name == Intel ]] && echo "Intel Mac, macOS 12.0 (Monterey) veya üstü" || echo "Apple Silicon (M1–M4), macOS 12.3 veya üstü")
Kullanım kılavuzu: programda Yardım > Kullanım kılavuzu (F1). Dil: Görünüm > Dil / Language.
TXT
  OUT="dist/CellVerity_${VER}_mac_${name}.dmg"
  rm -f "$OUT"
  hdiutil create -quiet -volname "CellVerity $VER" -srcfolder "$STAGE" -fs HFS+ -format UDZO "$OUT"
  rm -rf "$STAGE"
  echo "$OUT  $(du -h "$OUT" | cut -f1)"
done
