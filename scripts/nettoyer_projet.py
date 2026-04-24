"""
Script de nettoyage du projet MultiProShop
Supprime les fichiers inutiles et réorganise la structure
"""
import os
import shutil
from pathlib import Path

# Fichiers de documentation à garder (les plus importants)
DOCS_A_GARDER = [
    'README.md',
    'BILAN_COMPLET_MARKETPLACE.md',
    'PLAN_STRATEGIQUE_MARKETPLACE.md',
    'OPTIMISATIONS_FINALES_REUSSIES.md',
    'DEMARRAGE_RAPIDE.md',
    'GUIDE_TESTS.md',
]

# Fichiers de documentation à supprimer (redondants)
DOCS_A_SUPPRIMER = [
    'AMELIORATIONS_APPLIQUEES.md',
    'AMELIORATIONS_TECHNIQUES.md',
    'ANALYSE_COMPLETE_ET_PLAN_ACTION.md',
    'ARCHITECTURE.md',
    'BILAN_FINAL_COMPLET.md',
    'CATEGORIES_RESTAUREES.md',
    'CATEGORIES_STRUCTURE.md',
    'CHANGELOG_ARCHITECTURE.md',
    'CHANGEMENT_COULEURS.md',
    'COMPARAISON_CATEGORIES.md',
    'CONFIGURATION_RAPIDE.md',
    'CORRECTION_ACCES_API.md',
    'CORRECTION_ELEMENTS_BLEUS.md',
    'CORRECTION_PAGINATION.md',
    'ETAT_PROJET.md',
    'FIX_CATEGORIES_VIDES.md',
    'GUIDE_CONFIGURATION.md',
    'IMPLEMENTATION_COMPLETE.md',
    'IMPLEMENTATION_FINALE.md',
    'LAYOUT_MODERNISATION.md',
    'MODERNISATION_100_POURCENT_COMPLETE.md',
    'MODERNISATION_FINALE.md',
    'MODERNISATION_PAGES.md',
    'OPTIMISATIONS_APPLIQUEES.md',
    'OPTIMISATIONS_AVANCEES_APPLIQUEES.md',
    'OPTIMISATIONS_IMMEDIATES.md',
    'OPTIMISATIONS_REUSSIES.md',
    'PLAN_ACTION_IMMEDIAT.md',
    'PROCHAINES_AMELIORATIONS.md',
    'PROGRESSION_COMPLETE.md',
    'PROGRESSION_PHASE_1_2.md',
    'RAPPORT_FINAL_MODERNISATION.md',
    'RECAPITULATIF_FINAL.md',
    'RECAPITULATIF_MODERNISATION_COMPLETE.md',
    'RESUME_MODERNISATION.md',
    'SERVEUR_DEMARRE.md',
    'SIDEBAR_CATEGORIES_FIX.md',
    'SUCCES_TOTAL_MODERNISATION.md',
    'SUPPRESSION_BLEU_FINAL.md',
    'SYNTHESE_FINALE_COMPLETE.md',
    'VERIFICATION_BOUTONS_LIENS.md',
    'VICTOIRE_TOTALE_100_POURCENT.md',
]

# Scripts temporaires à supprimer
SCRIPTS_A_SUPPRIMER = [
    'add_all_remaining_categories.py',
    'add_sample_products.py',
    'add_stripe_field.py',
    'check_admin_role.py',
    'complete_categories_massive.py',
    'create_admin_user.py',
    'debug_sqlalchemy_issue.py',
    'import_categories_data.py',
    'init_db.py',
    'merge_duplicate_categories.py',
    'migrate_api_tables.py',
    'migrate_categories.py',
    'migrate_orders.py',
    'migrate_products_model.py',
    'migrate_to_hierarchical_categories.py',
    'recreate_database.py',
    'setup_database.ps1',
    'setup_harmonized_categories.py',
    'setup_improvements.ps1',
    'test_advanced_features.py',
    'test_config.py',
    'test_email.py',
    'upgrade_database_products.py',
]

def nettoyer_projet():
    """Nettoyer le projet"""
    print("="*70)
    print("🧹 NETTOYAGE DU PROJET MULTIPROSHOP")
    print("="*70)
    print()
    
    # Créer dossier docs/archive si nécessaire
    docs_dir = Path('docs')
    archive_dir = docs_dir / 'archive'
    scripts_dir = Path('scripts') / 'archive'
    
    docs_dir.mkdir(exist_ok=True)
    archive_dir.mkdir(exist_ok=True, parents=True)
    scripts_dir.mkdir(exist_ok=True, parents=True)
    
    count_docs = 0
    count_scripts = 0
    
    # Déplacer docs à garder dans docs/
    print("📚 Déplacement documentation importante...")
    for doc in DOCS_A_GARDER:
        if os.path.exists(doc):
            dest = docs_dir / doc
            if not dest.exists():
                shutil.move(doc, dest)
                print(f"  ✅ {doc} → docs/")
    
    # Archiver docs redondantes
    print("\n📦 Archivage documentation redondante...")
    for doc in DOCS_A_SUPPRIMER:
        if os.path.exists(doc):
            dest = archive_dir / doc
            shutil.move(doc, dest)
            count_docs += 1
            print(f"  ✅ {doc} → docs/archive/")
    
    # Archiver scripts temporaires
    print("\n🗂️  Archivage scripts temporaires...")
    for script in SCRIPTS_A_SUPPRIMER:
        if os.path.exists(script):
            dest = scripts_dir / script
            shutil.move(script, dest)
            count_scripts += 1
            print(f"  ✅ {script} → scripts/archive/")
    
    # Déplacer scripts utiles dans scripts/
    print("\n🔧 Organisation scripts utiles...")
    scripts_utiles = [
        'add_database_indexes.py',
        'add_lazy_loading.py',
        'optimize_images_webp.py',
        'optimiser_maintenant.ps1',
        'run_multiproshop.ps1',
    ]
    
    for script in scripts_utiles:
        if os.path.exists(script):
            dest = Path('scripts') / script
            if not dest.exists():
                shutil.copy(script, dest)
                print(f"  ✅ {script} → scripts/")
    
    print()
    print("="*70)
    print("📊 RÉSUMÉ DU NETTOYAGE")
    print("="*70)
    print(f"📚 Documents archivés: {count_docs}")
    print(f"🗂️  Scripts archivés: {count_scripts}")
    print(f"✅ Documentation organisée dans docs/")
    print(f"✅ Scripts organisés dans scripts/")
    print()
    print("🎉 Nettoyage terminé !")
    print("="*70)

if __name__ == '__main__':
    nettoyer_projet()
