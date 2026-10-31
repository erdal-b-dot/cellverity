@echo off
REM ICC CTCF Ölçer — Windows 10/11 kurulum. Bu dosyaya çift tıklayın.
chcp 65001 >nul
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  echo uv bulunamadi, kuruluyor...
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)
uv venv --python 3.12 .venv || goto :err
uv pip install --python .venv\Scripts\python.exe -r requirements-desktop.txt || goto :err
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\ICC CTCF Olcer.lnk'); $s.TargetPath='%~dp0start_windows.bat'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=7; $s.Save()"
echo.
echo Kurulum tamam. Masaustundeki "ICC CTCF Olcer" kisayoluna cift tiklayin.
pause
exit /b 0
:err
echo HATA: kurulum tamamlanamadi.
pause
exit /b 1
