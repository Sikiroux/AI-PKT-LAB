@echo off
REM Construit pkt_lab.exe (une seule fois).
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY (
  echo Python est introuvable. Installe-le avec :  winget install Python.Python.3.12
  pause
  exit /b 1
)
%PY% -m pip install --upgrade pyinstaller
%PY% -m PyInstaller --onefile --name pkt_lab --add-data "templates;templates" ^
  --exclude-module twofish --exclude-module Crypto --exclude-module Cryptodome main.py
echo.
echo Termine : l'executable est dans dist\pkt_lab.exe
pause
