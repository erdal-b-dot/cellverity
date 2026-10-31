#!/bin/zsh
# ICC CTCF Ölçer: sunucu çalışmıyorsa başlatır, sonra tarayıcıda açar.
APP_DIR="${0:A:h}"
PORT=8517
cd "$APP_DIR"
if ! curl -s "localhost:$PORT/_stcore/health" >/dev/null; then
  nohup .venv/bin/streamlit run app.py --server.headless true --server.port $PORT \
        --server.maxUploadSize 500 --browser.gatherUsageStats false > "$APP_DIR/server.log" 2>&1 &
  for i in {1..30}; do curl -s "localhost:$PORT/_stcore/health" >/dev/null && break; sleep 1; done
fi
open "http://localhost:$PORT"
