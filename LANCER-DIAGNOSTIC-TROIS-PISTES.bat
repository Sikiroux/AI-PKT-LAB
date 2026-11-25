@echo off
setlocal
cd /d "%~dp0"
echo Demarrage du diagnostic NetOps. Fermer NetOps et Packet Tracer avant le test.
set "NETOPS_TRIAGE_PROFILE=1"
set "NETOPS_MEMORY_DIAGNOSTIC=1"
set "NETOPS_MEMORY_SUITE=1"
set "NETOPS_NATIVE_MEMORY_PROFILE="
set "QV4_MM_AGGRESSIVE_GC="
set "ELECTRON_RUN_AS_NODE="
set "NETOPS_DIAG_LOG=%~dp0diagnostic-demarrage.log"
if not exist "%~dp0desktop\node_modules\electron\dist\electron.exe" goto missing
echo Journal : "%NETOPS_DIAG_LOG%"
echo La console attend la fermeture du logiciel. Le resultat du test est dans son rapport.
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command "$c=New-Object Net.Sockets.TcpClient;try{$c.Connect('127.0.0.1',8765);exit 1}catch{exit 0}finally{$c.Dispose()}"
if errorlevel 1 goto occupied
start "NetOps diagnostic" /wait "%~dp0desktop\node_modules\electron\dist\electron.exe" "%~dp0desktop" >"%NETOPS_DIAG_LOG%" 2>&1
set "NETOPS_EXIT_CODE=%ERRORLEVEL%"
echo Le logiciel est ferme. Code de sortie : %NETOPS_EXIT_CODE%
echo Journal de lancement : "%NETOPS_DIAG_LOG%"
if not "%NETOPS_EXIT_CODE%"=="0" type "%NETOPS_DIAG_LOG%"
goto finish
:occupied
echo NetOps est deja ouvert ou le port 8765 est utilise. Fermer cette instance avant de relancer.
goto finish
:missing
echo Electron est introuvable. Lancer LANCER-BUREAU.bat pour preparer son installation.
:finish
echo Appuyez sur une touche pour fermer cette console.
pause >nul
endlocal
