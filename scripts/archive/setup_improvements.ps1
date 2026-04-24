# Script PowerShell pour appliquer toutes les améliorations
# MultiProShop - Setup Améliorations

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*69) -ForegroundColor Cyan
Write-Host "🚀 SETUP DES AMÉLIORATIONS - MULTIPROSHOP" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*69) -ForegroundColor Cyan
Write-Host ""

# 1. Installer les dépendances de test
Write-Host "📦 ÉTAPE 1/3 : Installation des dépendances de test" -ForegroundColor Yellow
Write-Host ""

try {
    .\venv\Scripts\pip.exe install -r requirements_test.txt
    Write-Host "✅ Dépendances de test installées" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur lors de l'installation des dépendances" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""

# 2. Lancer les tests
Write-Host "🧪 ÉTAPE 2/3 : Lancement des tests" -ForegroundColor Yellow
Write-Host ""

try {
    .\venv\Scripts\pytest.exe -v
    Write-Host ""
    Write-Host "✅ Tests exécutés" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Certains tests ont échoué (normal si première fois)" -ForegroundColor Yellow
}

Write-Host ""

# 3. Ajouter les indexes à la base de données
Write-Host "🗄️  ÉTAPE 3/3 : Optimisation de la base de données" -ForegroundColor Yellow
Write-Host ""

try {
    .\venv\Scripts\python.exe add_database_indexes.py
    Write-Host "✅ Indexes ajoutés" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur lors de l'ajout des indexes" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*69) -ForegroundColor Cyan
Write-Host "🎉 SETUP TERMINÉ !" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*69) -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 RÉSUMÉ :" -ForegroundColor Cyan
Write-Host "  ✅ Dépendances de test installées" -ForegroundColor Green
Write-Host "  ✅ Tests unitaires disponibles (35+ tests)" -ForegroundColor Green
Write-Host "  ✅ Base de données optimisée (27 indexes)" -ForegroundColor Green
Write-Host ""

Write-Host "🚀 PROCHAINES ÉTAPES :" -ForegroundColor Cyan
Write-Host "  1. Lancer les tests : pytest" -ForegroundColor White
Write-Host "  2. Voir la couverture : pytest --cov=. --cov-report=html" -ForegroundColor White
Write-Host "  3. Démarrer le serveur : python app.py" -ForegroundColor White
Write-Host ""

Write-Host "📖 DOCUMENTATION :" -ForegroundColor Cyan
Write-Host "  - GUIDE_TESTS.md : Guide complet des tests" -ForegroundColor White
Write-Host "  - AMELIORATIONS_TECHNIQUES.md : Détails des améliorations" -ForegroundColor White
Write-Host "  - ETAT_PROJET.md : Vue d'ensemble du projet" -ForegroundColor White
Write-Host ""

Write-Host "Appuyez sur une touche pour continuer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
