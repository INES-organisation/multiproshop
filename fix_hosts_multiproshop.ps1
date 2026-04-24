# Script pour optimiser le fichier hosts pour multiproshop.local
# Supprime les doublons et l'entrée IPv6 qui cause la lenteur

$hostsPath = "C:\Windows\System32\drivers\etc\hosts"

Write-Host "Lecture du fichier hosts..." -ForegroundColor Cyan

# Lire le contenu
$content = Get-Content $hostsPath

# Créer une sauvegarde
$backupPath = "$hostsPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $hostsPath $backupPath
Write-Host "Sauvegarde créée: $backupPath" -ForegroundColor Green

# Filtrer les lignes
$newContent = @()
$multiproshopAdded = $false

foreach ($line in $content) {
    # Supprimer les lignes multiproshop.local (IPv4 et IPv6)
    if ($line -match "multiproshop\.local") {
        # Ajouter une seule fois l'entrée IPv4 optimale
        if (-not $multiproshopAdded) {
            $newContent += "127.0.0.1`tmultiproshop.local"
            $multiproshopAdded = $true
            Write-Host "Ajout de l'entrée optimisée: 127.0.0.1 multiproshop.local" -ForegroundColor Yellow
        }
        continue
    }
    
    # Garder toutes les autres lignes
    $newContent += $line
}

# Écrire le nouveau contenu
$newContent | Set-Content $hostsPath -Encoding ASCII

Write-Host "`nFichier hosts optimisé avec succès!" -ForegroundColor Green
Write-Host "Vidage du cache DNS..." -ForegroundColor Cyan

# Vider le cache DNS
ipconfig /flushdns | Out-Null

Write-Host "Cache DNS vidé!" -ForegroundColor Green
Write-Host "`nOptimisation terminée. Testez maintenant http://multiproshop.local/" -ForegroundColor Cyan
