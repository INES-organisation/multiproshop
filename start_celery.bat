@echo off
echo ========================================
echo Demarrage Celery MultiProShop
echo ========================================

cd C:\Users\Anthony\CascadeProjects\multiproshop

echo.
echo [1/2] Lancement Celery Worker...
start "Celery Worker" cmd /k "venv\Scripts\activate && celery -A celery_app worker --loglevel=info --pool=solo"

timeout /t 3 /nobreak > nul

echo [2/2] Lancement Celery Beat...
start "Celery Beat" cmd /k "venv\Scripts\activate && celery -A celery_app beat --loglevel=info"

echo.
echo ========================================
echo Celery demarre !
echo 2 fenetres ouvertes (Worker + Beat)
echo ========================================
pause
