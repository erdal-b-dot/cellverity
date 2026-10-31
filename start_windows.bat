@echo off
REM ICC CTCF Ölçer: sunucu çalışmıyorsa başlatır, tarayıcıda açar.
cd /d "%~dp0"
curl -s http://localhost:8517/_stcore/health >nul 2>nul
if errorlevel 1 (
  start "ICC CTCF Olcer sunucu" /min .venv\Scripts\streamlit.exe run app.py --server.headless true --server.port 8517 --server.maxUploadSize 500 --browser.gatherUsageStats false
  timeout /t 6 /nobreak >nul
)
start "" http://localhost:8517
