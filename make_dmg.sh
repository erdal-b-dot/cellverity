#!/bin/zsh
# dist/<arm64|x64>/ICC CTCF Ölçer.app → dist/ICC_CTCF_Olcer_<sürüm>_mac_<AppleSilicon|Intel>.dmg
# DMG açılınca: uygulama + Uygulamalar kısayolu + KURULUM.txt (sürükle-bırak kurulum).
set -e
cd "${0:A:h}"
VER=$(grep -m1 '^VERSION = ' desktop.py | cut -d'"' -f2)
for arch name in arm64 AppleSilicon x64 Intel; do
  APP="dist/$arch/ICC CTCF Ölçer.app"
  [[ -d "$APP" ]] || continue
  STAGE=$(mktemp -d)
  ditto "$APP" "$STAGE/ICC CTCF Ölçer.app"
  ln -s /Applications "$STAGE/Applications"
  cat > "$STAGE/INSTALL - KURULUM.txt" <<TXT
ICC CTCF Ölçer $VER ($name)

ENGLISH
1) Drag the 'ICC CTCF Ölçer' icon onto the 'Applications' folder next to it.
2) First launch: in Applications, RIGHT-CLICK the app > Open > Open
   (needed once, because the app is not notarized by Apple).
3) If macOS says the app "is damaged", run once in Terminal:
   xattr -cr "/Applications/ICC CTCF Ölçer.app"
Requires: $([[ $name == Intel ]] && echo "Intel Mac, macOS 12.0 (Monterey) or later" || echo "Apple Silicon (M1–M4), macOS 12.3 or later")
User guide: in the app, Help > User guide (F1). Interface language: View > Language / Dil.

TÜRKÇE
1) 'ICC CTCF Ölçer' simgesini yandaki 'Uygulamalar' klasörüne sürükleyin.
2) İlk açılışta: Uygulamalar klasöründe programa SAĞ TIKLAYIN > Aç > Aç
   (program Apple'a imzalatılmadığı için bir kez gereklidir).
3) "Hasarlı" uyarısı çıkarsa Terminal'de bir kez:
   xattr -cr "/Applications/ICC CTCF Ölçer.app"
Gereken sistem: $([[ $name == Intel ]] && echo "Intel Mac, macOS 12.0 (Monterey) veya üstü" || echo "Apple Silicon (M1–M4), macOS 12.3 veya üstü")
Kullanım kılavuzu: programda Yardım > Kullanım kılavuzu (F1). Dil: Görünüm > Dil / Language.
TXT
  OUT="dist/ICC_CTCF_Olcer_${VER}_mac_${name}.dmg"
  rm -f "$OUT"
  hdiutil create -quiet -volname "ICC CTCF Ölçer $VER" -srcfolder "$STAGE" -fs HFS+ -format UDZO "$OUT"
  rm -rf "$STAGE"
  echo "$OUT  $(du -h "$OUT" | cut -f1)"
done
