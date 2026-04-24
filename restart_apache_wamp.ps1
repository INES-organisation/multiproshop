# Script pour redémarrer Apache WAMP
# Doit être exécuté en tant qu'administrateur

Write-Host "Redémarrage d'Apache WAMP..." -ForegroundColor Cyan

try {
    # Arrêter le service
    Write-Host "Arrêt du service wampapache64..." -ForegroundColor Yellow
    net stop wampapache64
    
    # Attendre 2 secondes
    Start-Sleep -Seconds 2
    
    # Démarrer le service
    Write-Host "Démarrage du service wampapache64..." -ForegroundColor Yellow
    net start wampapache64
    
    Write-Host "`nApache WAMP redémarré avec succès!" -ForegroundColor Green
    Write-Host "Testez maintenant: http://multiproshop.local/" -ForegroundColor Cyan
}
catch {
    Write-Host "`nErreur lors du redémarrage: $_" -ForegroundColor Red
    Write-Host "`nUtilisez l'interface WAMP:" -ForegroundColor Yellow
    Write-Host "1. Clic droit sur l'icône WAMP (barre des tâches)" -ForegroundColor White
    Write-Host "2. Apache -> Service -> Restart Service" -ForegroundColor White
}
