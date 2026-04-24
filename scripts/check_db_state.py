"""
Script pour vérifier l'état exact de la base de données
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from models.category import Category
from sqlalchemy import func
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    app = create_app()
    
    with app.app_context():
        logger.info("=" * 80)
        logger.info("🔍 ÉTAT EXACT DE LA BASE DE DONNÉES")
        logger.info("=" * 80)
        
        # Produits
        total_products = Product.query.count()
        cj_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
        cj_published = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True
        ).count()
        cj_in_stock = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.stock > 0
        ).count()
        
        logger.info(f"\n📦 PRODUITS:")
        logger.info(f"  Total produits: {total_products}")
        logger.info(f"  Produits CJ (cj_pid NOT NULL): {cj_products}")
        logger.info(f"  Produits CJ publiés: {cj_published}")
        logger.info(f"  Produits CJ en stock: {cj_in_stock}")
        
        # Variantes
        total_variants = ProductVariant.query.count()
        active_variants = ProductVariant.query.filter_by(active=True).count()
        
        logger.info(f"\n🎨 VARIANTES:")
        logger.info(f"  Total variantes: {total_variants}")
        logger.info(f"  Variantes actives: {active_variants}")
        
        # Catégories
        total_categories = Category.query.count()
        cj_categories = Category.query.filter(Category.cj_category_id.isnot(None)).count()
        
        logger.info(f"\n📁 CATÉGORIES:")
        logger.info(f"  Total catégories: {total_categories}")
        logger.info(f"  Catégories CJ: {cj_categories}")
        
        # Exemples de produits
        logger.info(f"\n📋 EXEMPLES DE PRODUITS CJ:")
        sample_products = Product.query.filter(
            Product.cj_pid.isnot(None)
        ).limit(5).all()
        
        for p in sample_products:
            logger.info(f"  - ID: {p.id}, CJ_PID: {p.cj_pid}, Name: {p.name[:50]}, Published: {p.published}, Stock: {p.stock}")
        
        # Test de la requête get_stats
        logger.info(f"\n🧪 TEST REQUÊTE GET_STATS:")
        from services.cj_sync_service import CjSyncService
        from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
        from config import Config
        
        cj_api = CJDropshippingApiOptimized(
            email=Config.CJ_EMAIL,
            password=Config.CJ_PASSWORD,
            dev_key=Config.CJ_DEV_KEY
        )
        sync_service = CjSyncService(cj_api)
        stats = sync_service.get_stats()
        
        logger.info(f"  Stats retournées:")
        logger.info(f"    products.total: {stats['products']['total']}")
        logger.info(f"    products.published: {stats['products']['published']}")
        logger.info(f"    products.in_stock: {stats['products']['in_stock']}")
        logger.info(f"    variants.total: {stats['variants']['total']}")
        
        logger.info("=" * 80)


if __name__ == '__main__':
    main()
