# Script de démarrage propre de MultiProShop
# Supprime les caches Python et redémarre l'application

Write-Host "Nettoyage des caches Python..." -ForegroundColor Yellow

# Supprimer tous les fichiers __pycache__
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Supprimer tous les fichiers .pyc
Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "✓ Caches supprimés" -ForegroundColor Green

# Arrêter les processus Python existants
Write-Host "Arrêt des processus Python existants..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*multiproshop*' } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "✓ Processus arrêtés" -ForegroundColor Green

# Démarrer l'application
Write-Host "Démarrage de MultiProShop..." -ForegroundColor Cyan
python app.py
