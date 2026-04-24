import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.api_provider import ApiSyncLog, ProductSource
from models.product import Product

with app.app_context():
    print("\n" + "="*80)
    print("VERIFICATION DES LOGS DE SYNCHRONISATION")
    print("="*80 + "\n")
    
    # Récupérer les derniers logs
    logs = ApiSyncLog.query.order_by(ApiSyncLog.started_at.desc()).limit(5).all()
    
    print(f"Dernières synchronisations ({len(logs)}):\n")
    
    for log in logs:
        print(f"ID: {log.id}")
        print(f"  Statut: {log.status}")
        print(f"  Démarré: {log.started_at}")
        print(f"  Terminé: {log.completed_at}")
        if log.duration_seconds:
            print(f"  Durée: {log.duration_seconds}s")
        print(f"  Créés: {log.items_created}")
        print(f"  Mis à jour: {log.items_updated}")
        print(f"  Échecs: {log.items_failed}")
        print(f"  Total traités: {log.items_processed}")
        print()
    
    print("="*80)
    print("ÉTAT ACTUEL")
    print("="*80 + "\n")
    
    total_products = Product.query.count()
    total_sources = ProductSource.query.count()
    
    print(f"Total produits (Product): {total_products}")
    print(f"Total sources (ProductSource): {total_sources}")
    print()
