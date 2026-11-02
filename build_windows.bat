@echo off
REM Bagimsiz Windows programi derler (Python gerekmez) -> dist\CellVerity_<surum>_Windows.zip
setlocal
cd /d "%~dp0"
where uv >nul 2>nul || powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
uv venv --clear --python 3.12 .build-win || goto :err
uv pip install --python .build-win\Scripts\python.exe -r requirements-desktop.txt pyinstaller==6.16.0 || goto :err
.build-win\Scripts\pyinstaller --noconfirm --clean --distpath dist\win --workpath build\win cellverity.spec || goto :err
if exist examples\PARC_control\Image_11305.jpg (
  "dist\win\CellVerity\CellVerity.exe" --selftest examples\PARC_control\Image_11305.jpg examples\PARC_control\Image_11306.jpg
  type selftest_result.json
  echo.
  echo Beklenen / Expected: "cells": 47, "nuclei": 46, "bar_um": 20.0, "english": true
)
for /f "tokens=2 delims==" %%v in ('findstr /b "VERSION = " desktop.py') do set VER=%%~v
set VER=%VER: =%
set VER=%VER:"=%
powershell -c "Compress-Archive -Force -Path 'dist\win\CellVerity' -DestinationPath 'dist\CellVerity_%VER%_Windows.zip'"
echo Tamam: dist\CellVerity_%VER%_Windows.zip
pause
exit /b 0
:err
echo HATA: derleme basarisiz.
pause
exit /b 1
