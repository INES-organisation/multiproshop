# Script PowerShell pour restaurer la base multiproshop automatiquement
# Adapte les chemins des fichiers SQL selon tes besoins

$mysql = 'C:\wamp64\bin\mysql\mysql8.0.31\bin\mysql.exe'
$db = 'multiproshop'
$user = 'root'
$pwd = Read-Host -Prompt 'Mot de passe MySQL pour multiproshop'

# Création de la base si besoin
& $mysql -u $user -p$pwd -e "CREATE DATABASE IF NOT EXISTS $db;"

# Patch schéma si script présent
if (Test-Path './add_missing_columns_for_seeds.sql') {
    & $mysql -u $user -p$pwd $db < './add_missing_columns_for_seeds.sql'
}

# Import de schéma, modules, seeds si présents
foreach ($sql in Get-ChildItem -Recurse -Include *.sql | Where-Object { $_.Name -notlike 'add_missing_columns_for_seeds.sql' }) {
    Write-Host "Import de $($sql.Name)..."
    & $mysql -u $user -p$pwd $db < $sql.FullName
}
Write-Host "Restauration terminée pour multiproshop. Vérifiez les résultats dans phpMyAdmin ou en ligne de commande."
