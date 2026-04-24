# Script PowerShell pour fermer et relancer MultiProShop
# Aller dans le dossier du projet
Set-Location "C:\Users\Anthony\CascadeProjects\multiproshop"

# (Optionnel) Activer l'environnement virtuel si tu utilises un venv
if (Test-Path ".\venv\Scripts\Activate") {
    .\venv\Scripts\Activate
}

# Fermer tout processus python app.py existant
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*python.exe' -and $_.MainWindowTitle -like '*app.py*' } | ForEach-Object { $_.CloseMainWindow(); Start-Sleep -Seconds 2; if (!$_.HasExited) { $_.Kill() } }

# Lancer le serveur Flask
Start-Process python -ArgumentList 'app.py' -NoNewWindow
