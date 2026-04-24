@echo off
echo ========================================
echo Nettoyage du cache et redemarrage
echo ========================================

echo.
echo [1/3] Nettoyage du cache Redis...
redis-cli FLUSHALL
if %ERRORLEVEL% NEQ 0 (
    echo Redis non disponible, passage a l'etape suivante...
)

echo.
echo [2/3] Suppression des fichiers cache Python...
cd C:\Users\Anthony\CascadeProjects\multiproshop
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

echo.
echo [3/3] Cache nettoye !
echo.
echo ========================================
echo IMPORTANT: Redemarrez le serveur Flask
echo ========================================
echo.
echo Appuyez sur une touche pour continuer...
pause > nul
