@echo off
REM Lance pkt_lab. Cherche Python via le lanceur "py" puis via "python".
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY (
  echo Python est introuvable depuis l'invite de commandes.
  echo Installe-le avec :  winget install Python.Python.3.12
  echo puis ferme et rouvre cette fenetre.
  pause
  exit /b 1
)
%PY% main.py
pause
