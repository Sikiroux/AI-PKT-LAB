@echo off
setlocal
set "NETOPS_CAPTURE_ROOT=%~dp0"
cd /d "%~dp0"
echo Demarrage de la capture des allocations...
echo Dossier : "%~dp0"
if not exist "%~dp0tools\native_memory\Capture-Allocations.ps1" goto missing
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NoExit -File "%~dp0tools\native_memory\Capture-Allocations.ps1"
echo.
echo PowerShell termine. Code de sortie : %ERRORLEVEL%
goto finish
:missing
echo ERREUR : tools\native_memory\Capture-Allocations.ps1 introuvable.
echo Extraire le ZIP dans le dossier NetOps avant de lancer ce BAT.
:finish
echo.
echo Appuyez sur une touche pour fermer cette fenetre.
pause >nul
endlocal
