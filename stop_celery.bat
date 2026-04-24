@echo off
echo ========================================
echo Arret Celery MultiProShop
echo ========================================

echo Recherche des processus Celery...
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like '*celery*'} | Stop-Process -Force"

timeout /t 2 /nobreak > nul

echo.
echo Celery arrete !
echo ========================================
pause
