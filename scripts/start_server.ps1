# Script de démarrage du serveur Flask MultiProShop
# Arrête les processus Python existants et redémarre le serveur

Write-Host "=== DEMARRAGE MULTIPROSHOP ===" -ForegroundColor Cyan

# Arrêter les processus Python existants
Write-Host "Arret des processus Python existants..." -ForegroundColor Yellow
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

# Activer l'environnement virtuel
Write-Host "Activation de l'environnement virtuel..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Lancer le serveur
Write-Host "Demarrage du serveur Flask..." -ForegroundColor Green
Write-Host "URL: http://localhost:5000" -ForegroundColor Cyan
Write-Host "URL: http://multiproshop.local" -ForegroundColor Cyan
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour arreter le serveur" -ForegroundColor Yellow
Write-Host ""

python app.py
