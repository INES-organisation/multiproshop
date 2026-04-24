# Script d'initialisation automatique de la base de données

# Fonction pour afficher les messages en couleur
function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "INFO"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    switch ($Status) {
        "SUCCESS" { $color = "Green" }
        "ERROR"   { $color = "Red" }
        "WARNING" { $color = "Yellow" }
        default   { $color = "Cyan" }
    }
    Write-Host "[$timestamp] [$Status] $Message" -ForegroundColor $color
}

# Vérifier si MySQL est accessible
try {
    $mysqlCmd = "mysql -u root -e 'SHOW DATABASES;' 2>$null"
    $result = cmd /c $mysqlCmd 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        throw "Impossible de se connecter à MySQL. Vérifiez que le service MySQL est démarré."
    }
    Write-Status "Connexion à MySQL réussie" "SUCCESS"
}
catch {
    Write-Status "Erreur: $_" "ERROR"
    exit 1
}

# Créer la base de données si elle n'existe pas
$dbName = "multiproshop"
Write-Status "Création de la base de données $dbName..."
try {
    $createDbCmd = "mysql -u root -e 'CREATE DATABASE IF NOT EXISTS $dbName;'"
    $result = cmd /c $createDbCmd 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Échec de la création de la base de données"
    }
    Write-Status "Base de données créée avec succès" "SUCCESS"
}
catch {
    Write-Status "Erreur lors de la création de la base de données: $_" "ERROR"
    exit 1
}

# Vérifier si Python est disponible
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python n'est pas installé ou n'est pas dans le PATH"
    }
    Write-Status "Python trouvé: $pythonVersion" "SUCCESS"
}
catch {
    Write-Status "Erreur: $_" "ERROR"
    exit 1
}

# Installer les dépendances Python
Write-Status "Installation des dépendances Python..."
try {
    pip install -r requirements.txt 2>&1 | ForEach-Object { Write-Status "$_"; Start-Sleep -Milliseconds 100 }
    if ($LASTEXITCODE -ne 0) {
        throw "Échec de l'installation des dépendances"
    }
    Write-Status "Dépendances installées avec succès" "SUCCESS"
}
catch {
    Write-Status "Erreur lors de l'installation des dépendances: $_" "ERROR"
    exit 1
}

# Exécuter le script d'initialisation de la base de données
Write-Status "Initialisation de la base de données..."
try {
    $output = python init_db.py 2>&1
    $output | ForEach-Object { Write-Status "$_"; Start-Sleep -Milliseconds 50 }
    if ($LASTEXITCODE -ne 0) {
        throw "Échec de l'initialisation de la base de données"
    }
    Write-Status "Base de données initialisée avec succès" "SUCCESS"
}
catch {
    Write-Status "Erreur lors de l'initialisation: $_" "ERROR"
    exit 1
}

# Vérifier et exécuter create_admin.py si disponible
if (Test-Path "create_admin.py") {
    Write-Status "Création d'un compte administrateur..."
    try {
        $output = python create_admin.py 2>&1
        $output | ForEach-Object { Write-Status "$_"; Start-Sleep -Milliseconds 50 }
        Write-Status "Compte administrateur créé avec succès" "SUCCESS"
    }
    catch {
        Write-Status "Avertissement: Impossible de créer le compte administrateur: $_" "WARNING"
    }
}

# Démarrer l'application
Write-Status "Démarrage de l'application..." "SUCCESS"
Write-Host "`nPour démarrer l'application, exécutez :" -ForegroundColor Green
Write-Host "flask run --host=0.0.0.0 --port=5000" -ForegroundColor Cyan
Write-Host "`nPuis ouvrez http://waohost:5000 dans votre navigateur" -ForegroundColor Green
