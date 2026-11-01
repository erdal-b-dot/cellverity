@echo off
REM Bagimsiz Windows programi derler (Python gerekmez) -> dist\ICC_CTCF_Olcer_<surum>_Windows.zip
setlocal
cd /d "%~dp0"
where uv >nul 2>nul || powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
uv venv --clear --python 3.12 .build-win || goto :err
uv pip install --python .build-win\Scripts\python.exe -r requirements-desktop.txt pyinstaller==6.16.0 || goto :err
.build-win\Scripts\pyinstaller --noconfirm --clean --distpath dist\win --workpath build\win icc_ctcf.spec || goto :err
if exist ornek\Image_392.jpg (
  "dist\win\ICC CTCF Olcer\ICC CTCF Olcer.exe" --selftest ornek\Image_392.jpg ornek\Image_393.jpg
  type selftest_result.json
  echo.
  echo Beklenen: area [478.58, 495.48], ctcf [70203.4, 69111.2]
)
for /f "tokens=2 delims==" %%v in ('findstr /b "VERSION = " desktop.py') do set VER=%%~v
set VER=%VER: =%
set VER=%VER:"=%
powershell -c "Compress-Archive -Force -Path 'dist\win\ICC CTCF Olcer' -DestinationPath 'dist\ICC_CTCF_Olcer_%VER%_Windows.zip'"
echo Tamam: dist\ICC_CTCF_Olcer_%VER%_Windows.zip
pause
exit /b 0
:err
echo HATA: derleme basarisiz.
pause
exit /b 1
