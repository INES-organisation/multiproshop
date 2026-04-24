@echo off
REM Script de démarrage Flower (Monitoring Celery) pour Windows
REM À exécuter dans un terminal séparé

echo ========================================
echo DEMARRAGE FLOWER (Monitoring Celery)
echo ========================================
echo.

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Démarrer Flower
echo Demarrage de Flower...
echo Interface disponible sur: http://localhost:5555
celery -A celery_app flower

pause
