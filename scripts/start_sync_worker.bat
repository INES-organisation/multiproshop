@echo off
echo ========================================
echo   WORKER DE SYNCHRONISATION CJ
echo ========================================
echo.
echo Demarrage du worker en arriere-plan...
echo Appuyez sur Ctrl+C pour arreter
echo.

cd /d "%~dp0"

REM Activer l'environnement virtuel si présent
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Créer le dossier logs s'il n'existe pas
if not exist logs mkdir logs

REM Lancer le worker
python workers\sync_worker.py

pause
