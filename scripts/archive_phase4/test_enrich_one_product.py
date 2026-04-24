"""
Script de test pour enrichir UN SEUL produit et voir ce qui se passe
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_sync_service import CjSyncService
from services.cj_variant_sync_service import CjVariantSyncService
from config import Config
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    app = create_app()
    
    with app.app_context():
        logger.info("=" * 80)
        logger.info("🧪 TEST ENRICHISSEMENT D'UN PRODUIT")
        logger.info("=" * 80)
        
        # Prendre le premier produit CJ
        product = Product.query.filter(Product.cj_pid.isnot(None)).first()
        
        if not product:
            logger.error("❌ Aucun produit CJ trouvé")
            return 1
        
        logger.info(f"\n📦 PRODUIT SÉLECTIONNÉ:")
        logger.info(f"  ID: {product.id}")
        logger.info(f"  CJ_PID: {product.cj_pid}")
        logger.info(f"  Nom: {product.name}")
        logger.info(f"  Stock actuel: {product.stock}")
        logger.info(f"  Variantes actuelles: {ProductVariant.query.filter_by(product_id=product.id).count()}")
        
        # Initialiser l'API
        logger.info(f"\n🔑 CONNEXION API CJ")
        cj_api = CJDropshippingApiOptimized(
            email=Config.CJ_EMAIL,
            password=Config.CJ_PASSWORD,
            dev_key=Config.CJ_DEV_KEY
        )
        
        # Test 1: Récupérer les détails du produit
        logger.info(f"\n📋 TEST 1: Récupération des détails")
        logger.info("-" * 80)
        try:
            details = cj_api.get_product_details(product.cj_pid)
            if details:
                logger.info(f"✅ Détails récupérés:")
                data = details.get('data', {})
                logger.info(f"  Nom: {data.get('productNameEn', 'N/A')}")
                logger.info(f"  Description: {len(data.get('description', ''))} caractères")
                logger.info(f"  Poids: {data.get('productWeight', 'N/A')}")
                logger.info(f"  Prix: {data.get('sellPrice', 'N/A')}")
            else:
                logger.error(f"❌ Aucun détail récupéré")
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
        
        # Test 2: Récupérer les variantes
        logger.info(f"\n🎨 TEST 2: Récupération des variantes")
        logger.info("-" * 80)
        try:
            variants_data = cj_api.get_product_variants(product.cj_pid)
            if variants_data and variants_data.get('data'):
                variants = variants_data['data'].get('list', [])
                logger.info(f"✅ {len(variants)} variantes récupérées de l'API")
                
                if len(variants) > 0:
                    logger.info(f"\n  Exemple de variante:")
                    v = variants[0]
                    logger.info(f"    VID: {v.get('vid')}")
                    logger.info(f"    Nom: {v.get('variantNameEn')}")
                    logger.info(f"    SKU: {v.get('variantSku')}")
                    logger.info(f"    Stock: {v.get('variantStock')}")
                    logger.info(f"    Prix: {v.get('variantSellPrice')}")
            else:
                logger.warning(f"⚠️ Aucune variante récupérée")
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
        
        # Test 3: Enrichir via le service
        logger.info(f"\n⚡ TEST 3: Enrichissement complet via service")
        logger.info("-" * 80)
        try:
            sync_service = CjSyncService(cj_api)
            result = sync_service.enrich_product(product.cj_pid)
            
            if result.get('success'):
                logger.info(f"✅ Enrichissement réussi:")
                logger.info(f"  Rating: {result.get('rating', 'N/A')}")
                logger.info(f"  Avis: {result.get('review_count', 0)}")
            else:
                logger.error(f"❌ Enrichissement échoué: {result.get('error', 'Erreur inconnue')}")
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 4: Synchroniser les variantes
        logger.info(f"\n🔄 TEST 4: Synchronisation des variantes")
        logger.info("-" * 80)
        try:
            variant_service = CjVariantSyncService(cj_api)
            variant_result = variant_service.sync_product_variants(product.id)
            
            if variant_result.get('success'):
                logger.info(f"✅ Variantes synchronisées:")
                logger.info(f"  Total: {variant_result.get('total_variants', 0)}")
                logger.info(f"  Créées: {variant_result.get('created', 0)}")
                logger.info(f"  Mises à jour: {variant_result.get('updated', 0)}")
                
                # Vérifier en base
                db.session.commit()
                product = Product.query.get(product.id)
                variant_count = ProductVariant.query.filter_by(product_id=product.id).count()
                logger.info(f"\n  Variantes en base: {variant_count}")
                logger.info(f"  Stock produit: {product.stock}")
            else:
                logger.error(f"❌ Sync variantes échoué: {variant_result.get('error', 'Erreur inconnue')}")
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ TEST TERMINÉ")
        logger.info("=" * 80)


if __name__ == '__main__':
    main()
