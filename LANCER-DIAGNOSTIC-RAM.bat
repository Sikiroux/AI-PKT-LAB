@echo off
setlocal
echo Ferme toutes les fenetres NetOps avant ce lancement.
set "NETOPS_MEMORY_DIAGNOSTIC=1"
call "%~dp0LANCER-BUREAU.bat"
endlocal
