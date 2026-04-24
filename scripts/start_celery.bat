@echo off
REM Script de démarrage Celery Worker pour Windows
REM À exécuter dans un terminal séparé

echo ========================================
echo DEMARRAGE CELERY WORKER
echo ========================================
echo.

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Démarrer le worker Celery
echo Demarrage du worker Celery...
celery -A celery_app worker --loglevel=info --pool=solo

pause
