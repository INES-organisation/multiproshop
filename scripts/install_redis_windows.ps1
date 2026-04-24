# Script d'installation Redis pour Windows (Memurai)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION REDIS POUR WINDOWS (MEMURAI)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si Redis est déjà installé
Write-Host "Vérification de Redis..." -ForegroundColor Yellow

$redisInstalled = $false
try {
    $result = redis-cli ping 2>$null
    if ($result -eq "PONG") {
        Write-Host "✅ Redis est déjà installé et fonctionne !" -ForegroundColor Green
        $redisInstalled = $true
    }
} catch {
    Write-Host "❌ Redis n'est pas installé" -ForegroundColor Red
}

if (-not $redisInstalled) {
    Write-Host ""
    Write-Host "📥 OPTIONS D'INSTALLATION :" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option 1 : Memurai (Recommandé pour Windows)" -ForegroundColor White
    Write-Host "  - Télécharger : https://www.memurai.com/get-memurai" -ForegroundColor Gray
    Write-Host "  - Version Developer (gratuite)" -ForegroundColor Gray
    Write-Host "  - Installation automatique" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option 2 : Redis via WSL" -ForegroundColor White
    Write-Host "  - Nécessite WSL installé" -ForegroundColor Gray
    Write-Host "  - Commandes :" -ForegroundColor Gray
    Write-Host "    wsl --install" -ForegroundColor DarkGray
    Write-Host "    sudo apt update && sudo apt install redis-server" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Option 3 : Redis via Docker" -ForegroundColor White
    Write-Host "  - Nécessite Docker installé" -ForegroundColor Gray
    Write-Host "  - Commande :" -ForegroundColor Gray
    Write-Host "    docker run -d -p 6379:6379 --name redis redis:alpine" -ForegroundColor DarkGray
    Write-Host ""
    
    # Proposer d'ouvrir le site Memurai
    $response = Read-Host "Voulez-vous ouvrir le site de téléchargement Memurai ? (O/N)"
    if ($response -eq "O" -or $response -eq "o") {
        Start-Process "https://www.memurai.com/get-memurai"
        Write-Host "✅ Site ouvert dans le navigateur" -ForegroundColor Green
        Write-Host ""
        Write-Host "Après installation, relancez ce script pour vérifier." -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "🔧 CONFIGURATION MULTIPROSHOP POUR REDIS" -ForegroundColor Cyan
    Write-Host ""
    
    # Installer le package Python redis
    Write-Host "Installation du package Python redis..." -ForegroundColor Yellow
    & .\venv\Scripts\pip.exe install redis
    
    Write-Host ""
    Write-Host "✅ Configuration terminée !" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 PROCHAINES ÉTAPES :" -ForegroundColor Cyan
    Write-Host "1. Modifier config.py pour activer Redis" -ForegroundColor White
    Write-Host "2. Redémarrer le serveur" -ForegroundColor White
    Write-Host "3. Tester les performances" -ForegroundColor White
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
