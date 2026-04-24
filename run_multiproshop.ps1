# Script de lancement MultiProShop
# Démarre le serveur Flask en mode développement

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   MULTIPROSHOP - Démarrage Serveur" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier que l'environnement virtuel est activé
if (-not $env:VIRTUAL_ENV) {
    Write-Host "[INFO] Activation de l'environnement virtuel..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Vérifier que Redis est lancé
Write-Host "[INFO] Vérification de Redis..." -ForegroundColor Yellow
$redisRunning = Get-Process redis-server -ErrorAction SilentlyContinue
if (-not $redisRunning) {
    Write-Host "[ATTENTION] Redis n'est pas lancé !" -ForegroundColor Red
    Write-Host "            Démarrez Redis avant de continuer" -ForegroundColor Red
    Write-Host ""
}

# Lancer le serveur Flask
Write-Host "[INFO] Démarrage du serveur Flask..." -ForegroundColor Green
Write-Host ""
Write-Host "Serveur disponible sur :" -ForegroundColor Cyan
Write-Host "  - http://127.0.0.1:5000" -ForegroundColor White
Write-Host "  - http://multiproshop.local" -ForegroundColor White
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour arrêter le serveur" -ForegroundColor Yellow
Write-Host ""

python wsgi.py
