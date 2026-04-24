@echo off
REM Script de démarrage Celery Beat pour Windows
REM À exécuter dans un terminal séparé

echo ========================================
echo DEMARRAGE CELERY BEAT (Planificateur)
echo ========================================
echo.

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Démarrer Celery Beat
echo Demarrage du planificateur Celery Beat...
celery -A celery_app beat --loglevel=info

pause
