"""
Script pour vider le cache et lancer l'enrichissement
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import cache
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("🧹 NETTOYAGE DU CACHE")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Vider le cache Redis
            logger.info("\n🔄 Vidage du cache Redis...")
            cache.clear()
            logger.info("✅ Cache Redis vidé")
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ CACHE NETTOYÉ")
            logger.info("=" * 80)
            logger.info("\n💡 ACTIONS À FAIRE:")
            logger.info("  1. Rafraîchir la page http://multiproshop.local/admin/cj/products (Ctrl+F5)")
            logger.info("  2. Les compteurs devraient maintenant afficher 5014 produits")
            logger.info("\n💡 POUR ENRICHIR LES PRODUITS:")
            logger.info("  Lancez: python scripts\\fast_enrich_products.py")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
