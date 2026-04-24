"""
Script pour récupérer les STOCKS via listV2 SANS filtre catégorie
Pagine sur toutes les pages disponibles (max 1000 pages x 100 produits)
pour matcher un maximum de produits en BDD

listV2 est le SEUL endpoint CJ qui retourne warehouseInventoryNum (le stock réel)
"""
import sys
import os
import time
import requests
import warnings
from pathlib import Path

# Supprimer les warnings SSL
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

stats = {
    'pages_fetched': 0,
    'api_products_seen': 0,
    'products_matched': 0,
    'stocks_updated': 0,
    'total_stock': 0,
    'errors': 0
}


def get_token():
    """Obtenir un token CJ avec gestion du rate limit"""
    base_url = 'https://developers.cjdropshipping.com/api2.0/v1'
    
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
                    return data['data']['accessToken']
            
            logger.warning(f"  Tentative {attempt+1} - HTTP {resp.status_code} - attente 60s...")
            time.sleep(60)
        except Exception as e:
            logger.error(f"  Erreur: {e}")
            time.sleep(30)
    
    return None


def main():
    logger.info("=" * 80)
    logger.info("📦 SYNCHRONISATION GLOBALE DES STOCKS VIA listV2")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # État initial
            total_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
            products_in_stock = Product.query.filter(Product.cj_pid.isnot(None), Product.stock > 0).count()
            logger.info(f"\n📊 ÉTAT INITIAL: {total_products} produits CJ, {products_in_stock} en stock")
            
            # Indexer tous les produits par PID
            logger.info("🔍 Indexation des produits...")
            all_products = Product.query.filter(Product.cj_pid.isnot(None)).all()
            pid_to_product = {str(p.cj_pid): p for p in all_products}
            logger.info(f"  {len(pid_to_product)} produits indexés")
            
            # Obtenir un token
            logger.info("\n🔑 Connexion API CJ...")
            token = get_token()
            if not token:
                logger.error("❌ Impossible d'obtenir un token")
                return 1
            logger.info("✅ Token obtenu")
            
            base_url = 'https://developers.cjdropshipping.com/api2.0/v1'
            headers = {
                'CJ-Access-Token': token,
                'Content-Type': 'application/json'
            }
            if Config.CJ_DEV_KEY:
                headers['CJ-DEV-KEY'] = Config.CJ_DEV_KEY
            
            # Paginer sur listV2 sans filtre
            logger.info("\n📦 RÉCUPÉRATION DES STOCKS (listV2 global)")
            logger.info("-" * 80)
            logger.info("  Mode: Pagination globale sans filtre")
            logger.info("  Pages max: 1000 (limite API)")
            logger.info("  Produits par page: 100")
            
            start_time = time.time()
            max_page = 1000  # Limite API CJ
            consecutive_empty = 0
            
            for page in range(1, max_page + 1):
                try:
                    resp = requests.get(
                        f"{base_url}/product/listV2",
                        params={'page': page, 'size': 100},
                        headers=headers, verify=False, timeout=30
                    )
                    
                    if resp.status_code == 429:
                        logger.warning(f"  ⚠️ Rate limit 429 - attente 60s...")
                        time.sleep(60)
                        # Réessayer
                        resp = requests.get(
                            f"{base_url}/product/listV2",
                            params={'page': page, 'size': 100},
                            headers=headers, verify=False, timeout=30
                        )
                        if resp.status_code == 429:
                            logger.warning(f"  ⚠️ Rate limit persistant - attente 120s...")
                            time.sleep(120)
                            continue
                    
                    if resp.status_code != 200:
                        stats['errors'] += 1
                        continue
                    
                    data = resp.json()
                    if not data.get('result'):
                        stats['errors'] += 1
                        consecutive_empty += 1
                        if consecutive_empty >= 3:
                            logger.info(f"  3 pages vides consécutives - arrêt")
                            break
                        continue
                    
                    content = data.get('data', {}).get('content', [])
                    total_pages = data.get('data', {}).get('totalPages', 0)
                    
                    if not content:
                        consecutive_empty += 1
                        if consecutive_empty >= 3:
                            logger.info(f"  3 pages vides consécutives - arrêt")
                            break
                        continue
                    
                    consecutive_empty = 0
                    page_matched = 0
                    
                    for item in content:
                        for p in item.get('productList', []):
                            pid = str(p.get('id', ''))
                            stock = int(p.get('warehouseInventoryNum', 0) or 0)
                            stats['api_products_seen'] += 1
                            
                            if pid in pid_to_product:
                                product = pid_to_product[pid]
                                if product.stock != stock:
                                    product.stock = stock
                                    stats['stocks_updated'] += 1
                                    if stock > 0:
                                        stats['total_stock'] += stock
                                stats['products_matched'] += 1
                                page_matched += 1
                    
                    stats['pages_fetched'] += 1
                    
                    # Commit toutes les 5 pages
                    if page % 5 == 0:
                        db.session.commit()
                    
                    # Rapport toutes les 10 pages
                    if page % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = page / elapsed if elapsed > 0 else 0
                        remaining = min(total_pages, max_page) - page
                        eta_minutes = int((remaining / rate) / 60) if rate > 0 else 0
                        
                        logger.info(
                            f"📊 Page {page}/{min(total_pages, max_page)} | "
                            f"Vus: {stats['api_products_seen']} | "
                            f"Matchés: {stats['products_matched']} | "
                            f"MAJ: {stats['stocks_updated']} | "
                            f"En stock: {stats['total_stock']} | "
                            f"ETA: ~{eta_minutes}min"
                        )
                    
                    # Arrêter si on a dépassé le nombre de pages
                    if page >= total_pages:
                        logger.info(f"  Toutes les pages traitées ({total_pages})")
                        break
                    
                    # Délai entre pages
                    time.sleep(1.5)
                    
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"❌ Erreur page {page}: {e}")
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
            logger.info(f"  Pages API: {stats['pages_fetched']}")
            logger.info(f"  Produits vus dans API: {stats['api_products_seen']}")
            logger.info(f"  Produits matchés en BDD: {stats['products_matched']}")
            logger.info(f"  Stocks mis à jour: {stats['stocks_updated']}")
            logger.info(f"  Produits en stock: {products_in_stock_final}")
            logger.info(f"  Erreurs: {stats['errors']}")
            logger.info(f"  Temps: {int(elapsed_total / 60)}min {int(elapsed_total % 60)}s")
            logger.info("=" * 80)
            
            logger.info("\n💡 Vider le cache: python scripts\\clear_cache_and_enrich.py")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
