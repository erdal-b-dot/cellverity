#!/bin/zsh
# macOS kurulum (Apple Silicon ve Intel, macOS 11 Big Sur ve üzeri — Monterey dahil).
# Kullanım: Terminal'de bu klasöre gidip ./install_mac.sh
set -e
APP_DIR="${0:A:h}"
cd "$APP_DIR"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv bulunamadı, kuruluyor (https://docs.astral.sh/uv/)…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-desktop.txt
chmod +x start.sh stop.sh run.command
mkdir -p "$HOME/Applications"
osacompile -o "$HOME/Applications/ICC CTCF Ölçer v1 (tarayıcı).app" -e "do shell script quoted form of \"$APP_DIR/start.sh\" & \" > /dev/null 2>&1\""
ln -sf "$HOME/Applications/ICC CTCF Ölçer v1 (tarayıcı).app" "$HOME/Desktop/ICC CTCF Ölçer v1 (tarayıcı).app"
echo "✅ Kurulum tamam. Masaüstündeki 'ICC CTCF Ölçer' simgesine çift tıklayın."
