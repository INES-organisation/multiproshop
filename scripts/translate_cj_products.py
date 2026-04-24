"""
Script de traduction automatique des produits CJ
Traduit les noms et descriptions des produits CJ de l'anglais vers le français
"""
import sys
import os
from datetime import datetime
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from services.translation_service import TranslationService
from extensions import db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def translate_products(max_products=20, skip_translated=True):
    """
    Traduire les produits CJ en français
    
    Args:
        max_products: Nombre max de produits à traduire
        skip_translated: Ignorer les produits déjà traduits
    """
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🌍 TRADUCTION AUTOMATIQUE PRODUITS CJ")
        logger.info("="*70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Limite: {max_products} produits")
        
        # Initialiser le service de traduction
        try:
            translator = TranslationService(provider='google')
            logger.info("✅ Service de traduction initialisé (Google Translate)")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation traduction: {e}")
            return False
        
        # Récupérer les produits CJ à traduire
        query = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.cj_pid != ''
        )
        
        if skip_translated:
            # Ignorer les produits dont le nom ne contient pas de caractères anglais typiques
            # ou qui ont déjà été traduits (heuristique simple)
            query = query.filter(
                Product.name.like('%-%') |  # Contient des tirets (souvent anglais)
                Product.name.like('%&%') |  # Contient &
                Product.name.like('%For%') |  # Contient "For"
                Product.name.like('%With%')  # Contient "With"
            )
        
        products = query.limit(max_products).all()
        
        total_products = len(products)
        logger.info(f"\n📦 Produits à traduire: {total_products}")
        
        if total_products == 0:
            logger.info("✅ Aucun produit à traduire")
            return True
        
        # Statistiques
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        # Traduire chaque produit
        for i, product in enumerate(products, 1):
            logger.info(f"\n[{i}/{total_products}] Produit: {product.name[:60]}...")
            logger.info(f"  ID: {product.id} | CJ PID: {product.cj_pid}")
            
            try:
                # Sauvegarder les valeurs originales
                original_name = product.name
                original_description = product.description or ''
                
                # Détecter la langue du nom
                detected_lang = translator.detect_language(original_name)
                logger.info(f"  Langue détectée: {detected_lang}")
                
                # Si déjà en français, ignorer
                if detected_lang == 'fr':
                    logger.info(f"  ⏭️ Déjà en français, ignoré")
                    skipped_count += 1
                    continue
                
                # Traduire le nom
                translated_name = translator.translate_text(
                    original_name,
                    source_lang=detected_lang,
                    target_lang='fr'
                )
                
                # Traduire la description (si présente)
                translated_description = ''
                if original_description and len(original_description) > 10:
                    # Limiter la longueur pour éviter les timeouts
                    desc_to_translate = original_description[:500]
                    translated_description = translator.translate_text(
                        desc_to_translate,
                        source_lang=detected_lang,
                        target_lang='fr'
                    )
                    # Ajouter le reste non traduit si tronqué
                    if len(original_description) > 500:
                        translated_description += original_description[500:]
                
                # Mettre à jour le produit
                product.name = translated_name
                if translated_description:
                    product.description = translated_description
                product.updated_at = datetime.now()
                
                db.session.commit()
                
                logger.info(f"  ✅ Traduit:")
                logger.info(f"     EN: {original_name[:50]}...")
                logger.info(f"     FR: {translated_name[:50]}...")
                success_count += 1
                
                # Délai pour éviter rate limiting
                if i < total_products:
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"  ❌ Erreur: {e}")
                db.session.rollback()
                error_count += 1
        
        # Résumé
        logger.info("\n" + "="*70)
        logger.info("📊 RÉSUMÉ DE LA TRADUCTION")
        logger.info("="*70)
        logger.info(f"Total produits: {total_products}")
        logger.info(f"✅ Traduits: {success_count}")
        logger.info(f"⏭️ Ignorés: {skipped_count}")
        logger.info(f"❌ Erreurs: {error_count}")
        if total_products > 0:
            logger.info(f"Taux de réussite: {(success_count/(total_products-skipped_count)*100):.1f}%")
        logger.info("="*70)
        
        return error_count == 0


if __name__ == '__main__':
    try:
        # Paramètres par défaut
        max_products = 20
        skip_translated = True
        
        # Permettre de passer des arguments
        if len(sys.argv) > 1:
            max_products = int(sys.argv[1])
        if len(sys.argv) > 2:
            skip_translated = sys.argv[2].lower() in ['true', '1', 'yes']
        
        success = translate_products(max_products, skip_translated)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
