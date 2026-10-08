@echo off
cd /d "%~dp0web"
py -3 --version >nul 2>&1
if errorlevel 1 goto usepython
py -3 diagnose_icmp.py
goto end
:usepython
python diagnose_icmp.py
:end
pause
