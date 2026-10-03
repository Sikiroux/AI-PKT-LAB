@echo off
cd /d "%~dp0"
py -3 --version >nul 2>&1
if errorlevel 1 goto usepython
py -3 tickets_app.py
goto end
:usepython
python --version >nul 2>&1
if errorlevel 1 goto missing
python tickets_app.py
goto end
:missing
echo Python 3.10 ou plus recent est necessaire. Installer Python depuis python.org.
echo Activer Add Python to PATH pendant l'installation.
:end
pause
