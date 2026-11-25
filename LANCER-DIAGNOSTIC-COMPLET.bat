@echo off
setlocal
echo Sauvegarde puis ferme Packet Tracer et NetOps avant ce lancement.
set "NETOPS_MEMORY_DIAGNOSTIC=1"
set "NETOPS_MEMORY_SUITE=1"
call "%~dp0LANCER-BUREAU.bat"
endlocal
