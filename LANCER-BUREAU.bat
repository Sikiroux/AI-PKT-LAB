@echo off
setlocal
cd /d "%~dp0desktop"
if errorlevel 1 goto missingfolder
if exist "%~dp0desktop\node_modules\electron\dist\electron.exe" goto launch
where npm >nul 2>nul
if errorlevel 1 goto missingnpm
echo Preparation du prototype bureau. Connexion Internet necessaire.
call npm --prefix "%~dp0desktop" install --include=dev --ignore-scripts=false --save-dev --save-exact electron@latest
if errorlevel 1 goto failed
if exist "%~dp0desktop\node_modules\electron\dist\electron.exe" goto launch
echo Telechargement explicite du moteur Electron...
if not exist "%~dp0desktop\node_modules\electron\install.js" goto missingpackage
set "ELECTRON_SKIP_BINARY_DOWNLOAD="
node "%~dp0desktop\node_modules\electron\install.js"
if errorlevel 1 goto failed
if not exist "%~dp0desktop\node_modules\electron\dist\electron.exe" goto missingelectron
:launch
set "ELECTRON_RUN_AS_NODE="
start "" "%~dp0desktop\node_modules\electron\dist\electron.exe" "%~dp0desktop"
if errorlevel 1 goto failed
exit /b 0
:missingfolder
echo Dossier desktop introuvable. Extraire toute l'archive avant de lancer.
goto failed
:missingnpm
echo Node.js LTS avec npm est necessaire pour preparer ce prototype.
goto failed
:missingpackage
echo Le paquet Electron est absent du dossier desktop. Details npm :
call npm --prefix "%~dp0desktop" ls electron --include=dev
goto failed
:missingelectron
echo Le moteur Electron n'a pas ete telecharge. Verifier la connexion et les messages npm ci-dessus.
:failed
echo.
echo Le lancement a echoue. Conserver une capture de cette fenetre.
pause
exit /b 1
