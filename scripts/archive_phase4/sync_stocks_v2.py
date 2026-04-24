"""
Script pour récupérer les STOCKS de tous les produits CJ via l'endpoint listV2
qui est le SEUL endpoint CJ qui retourne warehouseInventoryNum (le stock réel)

L'endpoint product/query ne retourne PAS les stocks (inventories = None)
"""
import sys
import os
import time
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from models.category import Category
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized, _memory_cache
from config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

stats = {
    'pages_fetched': 0,
    'products_matched': 0,
    'stocks_updated': 0,
    'total_stock': 0,
    'errors': 0
}


def get_token():
    """Obtenir un token CJ avec gestion du rate limit"""
    base_url = 'https://developers.cjdropshipping.com/api2.0/v1'
    
    # Réutiliser le token existant si valide
    if _memory_cache.get('access_token') and _memory_cache.get('token_expires_at', 0) > time.time():
        return _memory_cache['access_token']
    
    _memory_cache['rate_limit_until'] = 0
    
    for attempt in range(10):
        try:
            resp = requests.post(
                f"{base_url}/authentication/getAccessToken",
                json={'email': Config.CJ_EMAIL, 'password': Config.CJ_PASSWORD},
                headers={'Content-Type': 'application/json'},
                verify=False, timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('result') and data.get('data', {}).get('accessToken'):
                    token = data['data']['accessToken']
                    _memory_cache['access_token'] = token
                    _memory_cache['token_expires_at'] = time.time() + (14 * 24 * 3600)
                    return token
            
            logger.warning(f"  Tentative {attempt+1} - HTTP {resp.status_code} - attente 60s...")
            time.sleep(60)
        except Exception as e:
            logger.error(f"  Erreur: {e}")
            time.sleep(30)
    
    return None


def fetch_stocks_by_sku(token, sku_list):
    """Chercher les stocks via listV2 en utilisant le SKU comme mot-clé"""
    base_url = 'https://developers.cjdropshipping.com/api2.0/v1'
    headers = {
        'CJ-Access-Token': token,
        'Content-Type': 'application/json'
    }
    if Config.CJ_DEV_KEY:
        headers['CJ-DEV-KEY'] = Config.CJ_DEV_KEY
    
    results = {}
    
    for sku in sku_list:
        try:
            resp = requests.get(
                f"{base_url}/product/listV2",
                params={'page': 1, 'size': 5, 'keyWord': sku},
                headers=headers, verify=False, timeout=30
            )
            
            if resp.status_code == 429:
                logger.warning("Rate limit 429 - attente 60s...")
                time.sleep(60)
                continue
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('result'):
                    content = data.get('data', {}).get('content', [])
                    for item in content:
                        for p in item.get('productList', []):
                            pid = p.get('id')
                            stock = int(p.get('warehouseInventoryNum', 0) or 0)
                            results[pid] = stock
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Erreur fetch SKU {sku}: {e}")
    
    return results


def fetch_stocks_by_category(token, category_id, max_pages=10):
    """Récupérer les stocks de tous les produits d'une catégorie via listV2"""
    base_url = 'https://developers.cjdropshipping.com/api2.0/v1'
    headers = {
        'CJ-Access-Token': token,
        'Content-Type': 'application/json'
    }
    if Config.CJ_DEV_KEY:
        headers['CJ-DEV-KEY'] = Config.CJ_DEV_KEY
    
    results = {}
    
    for page in range(1, max_pages + 1):
        try:
            resp = requests.get(
                f"{base_url}/product/listV2",
                params={'page': page, 'size': 100, 'categoryId': category_id},
                headers=headers, verify=False, timeout=30
            )
            
            if resp.status_code == 429:
                logger.warning("Rate limit 429 - attente 60s...")
                time.sleep(60)
                # Réessayer la même page
                resp = requests.get(
                    f"{base_url}/product/listV2",
                    params={'page': page, 'size': 100, 'categoryId': category_id},
                    headers=headers, verify=False, timeout=30
                )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('result'):
                    content = data.get('data', {}).get('content', [])
                    total_pages = data.get('data', {}).get('totalPages', 0)
                    
                    if not content:
                        break
                    
                    for item in content:
                        for p in item.get('productList', []):
                            pid = p.get('id')
                            stock = int(p.get('warehouseInventoryNum', 0) or 0)
                            results[pid] = stock
                    
                    stats['pages_fetched'] += 1
                    
                    if page >= total_pages:
                        break
                else:
                    break
            else:
                break
            
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Erreur page {page}: {e}")
            time.sleep(5)
    
    return results


def main():
    logger.info("=" * 80)
    logger.info("📦 SYNCHRONISATION DES STOCKS VIA listV2")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # État initial
            logger.info("\n📊 ÉTAT INITIAL")
            logger.info("-" * 80)
            total_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
            products_in_stock = Product.query.filter(Product.cj_pid.isnot(None), Product.stock > 0).count()
            logger.info(f"  Produits CJ: {total_products}")
            logger.info(f"  Produits en stock: {products_in_stock}")
            
            # Obtenir un token
            logger.info("\n🔑 CONNEXION API CJ")
            logger.info("-" * 80)
            token = get_token()
            if not token:
                logger.error("❌ Impossible d'obtenir un token")
                return 1
            logger.info("✅ Token obtenu")
            
            # Récupérer les catégories CJ de niveau 3 (les plus spécifiques)
            categories = Category.query.filter(
                Category.cj_category_id.isnot(None),
                Category.level == 3
            ).all()
            
            total_cats = len(categories)
            logger.info(f"\n📁 {total_cats} catégories de niveau 3 à traiter")
            
            # Créer un index PID -> Product pour mise à jour rapide
            logger.info("\n🔍 Indexation des produits...")
            all_products = Product.query.filter(Product.cj_pid.isnot(None)).all()
            pid_to_product = {p.cj_pid: p for p in all_products}
            logger.info(f"  {len(pid_to_product)} produits indexés")
            
            # Récupérer les stocks par catégorie
            logger.info("\n📦 RÉCUPÉRATION DES STOCKS PAR CATÉGORIE")
            logger.info("-" * 80)
            logger.info(f"  Méthode: listV2 (seul endpoint avec warehouseInventoryNum)")
            logger.info(f"  Catégories: {total_cats}")
            logger.info(f"  Max pages par catégorie: 10 (1000 produits)")
            
            start_time = time.time()
            
            for idx, cat in enumerate(categories, 1):
                try:
                    stock_data = fetch_stocks_by_category(token, cat.cj_category_id, max_pages=10)
                    
                    # Mettre à jour les produits en BDD
                    for pid, stock in stock_data.items():
                        if pid in pid_to_product:
                            product = pid_to_product[pid]
                            if product.stock != stock:
                                product.stock = stock
                                stats['stocks_updated'] += 1
                                stats['total_stock'] += stock
                            stats['products_matched'] += 1
                    
                    # Commit par lot de 10 catégories
                    if idx % 10 == 0:
                        db.session.commit()
                        
                        elapsed = time.time() - start_time
                        rate = idx / elapsed if elapsed > 0 else 0
                        remaining = total_cats - idx
                        eta_minutes = int((remaining / rate) / 60) if rate > 0 else 0
                        
                        logger.info(f"📊 [{idx}/{total_cats}] | Matchés: {stats['products_matched']} | MAJ: {stats['stocks_updated']} | Stock total: {stats['total_stock']} | ETA: ~{eta_minutes}min")
                    
                    # Délai entre catégories
                    time.sleep(2)
                    
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"❌ Erreur catégorie {cat.name}: {e}")
                    time.sleep(5)
            
            # Commit final
            db.session.commit()
            
            # Statistiques finales
            elapsed_total = time.time() - start_time
            products_in_stock_final = Product.query.filter(
                Product.cj_pid.isnot(None), Product.stock > 0
            ).count()
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ SYNCHRONISATION DES STOCKS TERMINÉE")
            logger.info("=" * 80)
            logger.info(f"  Pages API récupérées: {stats['pages_fetched']}")
            logger.info(f"  Produits matchés: {stats['products_matched']}")
            logger.info(f"  Stocks mis à jour: {stats['stocks_updated']}")
            logger.info(f"  Stock total: {stats['total_stock']}")
            logger.info(f"  Produits en stock: {products_in_stock_final}")
            logger.info(f"  Erreurs: {stats['errors']}")
            logger.info(f"  Temps total: {int(elapsed_total / 60)}min {int(elapsed_total % 60)}s")
            logger.info("=" * 80)
            
            logger.info("\n💡 PROCHAINES ÉTAPES:")
            logger.info("  1. Vider le cache: python scripts\\clear_cache_and_enrich.py")
            logger.info("  2. Vérifier sur: http://multiproshop.local/admin/cj/products")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
