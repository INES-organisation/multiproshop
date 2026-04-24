"""
Script de pré-synchronisation des frais de livraison CJ
Appelle freightCalculateTip pour chaque produit CJ × pays cible
et stocke les résultats dans la table shipping_rate.

Sync progressive : respecte le quota CJ Free tier (1000 req/jour).
Sauvegarde la progression dans un fichier JSON pour reprendre le lendemain.

Usage:
    python scripts/sync_shipping_rates.py --all               # Sync progressive tous pays (priorité auto)
    python scripts/sync_shipping_rates.py --resume             # Reprendre où on s'est arrêté
    python scripts/sync_shipping_rates.py --countries FR,BE    # Sync FR + BE uniquement
    python scripts/sync_shipping_rates.py --status             # Voir la progression actuelle
    python scripts/sync_shipping_rates.py --limit 100          # Limiter à 100 produits
    python scripts/sync_shipping_rates.py --refresh            # Re-sync les expirés seulement
"""
import sys
import os
import json
import time
import argparse
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from models.shipping_rate import ShippingRate
from config import Config

# Taux de conversion USD → EUR
USD_TO_EUR = 0.92

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fichier de progression persistant
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sync_progress.json')

# Quota journalier CJ Free tier
DAILY_QUOTA = 950  # 1000 officiel, on garde 50 de marge pour le checkout

# Pays cibles pour le pré-calcul (liste COMPLÈTE CJ Dropshipping officielle)
TARGET_COUNTRIES = [
    # Europe de l'Ouest
    'FR', 'BE', 'LU', 'CH', 'DE', 'AT', 'NL', 'GB', 'IE', 'MC', 'AD', 'LI', 'GI', 'GG', 'JE', 'IM',
    # Europe du Sud
    'ES', 'PT', 'IT', 'GR', 'MT', 'CY', 'HR', 'SI', 'SM', 'VA',
    # Europe du Nord
    'DK', 'SE', 'NO', 'FI', 'IS', 'EE', 'LV', 'LT', 'FO', 'GL',
    # Europe de l'Est
    'PL', 'CZ', 'SK', 'HU', 'RO', 'BG', 'UA', 'RS', 'BA', 'ME', 'MK', 'AL', 'MD', 'XK', 'BY', 'RU',
    # Amérique du Nord
    'US', 'CA', 'MX', 'BM', 'PM',
    # Amérique centrale et Caraïbes
    'GT', 'BZ', 'HN', 'SV', 'NI', 'CR', 'PA', 'CU', 'HT', 'DO', 'JM', 'TT', 'BB', 'BS',
    'AG', 'DM', 'GD', 'KN', 'LC', 'VC', 'AI', 'AW', 'KY', 'CW', 'GP', 'MQ', 'MS', 'PR',
    'BQ', 'SX', 'MF', 'TC', 'VG', 'VI', 'AS',
    # Amérique du Sud
    'BR', 'AR', 'CL', 'CO', 'PE', 'EC', 'UY', 'PY', 'BO', 'VE', 'GY', 'SR', 'GF', 'FK',
    # Asie de l'Est
    'CN', 'JP', 'KR', 'KP', 'TW', 'HK', 'MO', 'MN',
    # Asie du Sud-Est
    'SG', 'MY', 'TH', 'ID', 'PH', 'VN', 'KH', 'MM', 'LA', 'BN', 'TL',
    # Asie du Sud
    'IN', 'PK', 'BD', 'LK', 'NP', 'BT', 'MV', 'AF',
    # Asie centrale et Caucase
    'KZ', 'UZ', 'KG', 'TJ', 'GE', 'AZ', 'AM',
    # Moyen-Orient
    'AE', 'SA', 'IL', 'TR', 'QA', 'KW', 'BH', 'OM', 'JO', 'LB', 'IQ', 'IR', 'SY', 'YE', 'PS',
    # Afrique du Nord
    'MA', 'DZ', 'TN', 'EG', 'LY', 'SD', 'SS', 'EH',
    # Afrique de l'Ouest
    'NG', 'GH', 'SN', 'CI', 'CM', 'ML', 'BF', 'NE', 'GN', 'BJ', 'TG', 'SL', 'LR', 'MR', 'GW', 'GM', 'CV', 'GQ',
    # Afrique de l'Est
    'KE', 'TZ', 'ET', 'UG', 'RW', 'BI', 'SO', 'DJ', 'ER', 'MG', 'MU', 'SC', 'KM', 'RE', 'YT',
    # Afrique australe et centrale
    'ZA', 'AO', 'CD', 'CG', 'CF', 'TD', 'GA', 'ST', 'NA', 'BW', 'ZM', 'ZW', 'MW', 'MZ', 'LS', 'SZ', 'SH',
    # Océanie
    'AU', 'NZ', 'PG', 'FJ', 'WS', 'TO', 'VU', 'SB', 'NC', 'PF', 'GU', 'MP', 'KI', 'FM', 'MH', 'PW',
    'NR', 'TV', 'CK', 'NU', 'TK', 'WF', 'NF', 'PN', 'CX', 'CC', 'HM',
    # Territoires
    'IO', 'BV', 'TF', 'GS',
]

# Pays PRIORITAIRES (marchés clés en premier, puis le reste)
PRIORITY_COUNTRIES = [
    # Tier 1 : Marchés francophones principaux
    'FR', 'BE', 'CH', 'LU', 'MC', 'CA',
    # Tier 2 : Europe de l'Ouest majeure
    'DE', 'GB', 'NL', 'AT', 'IE', 'ES', 'PT', 'IT',
    # Tier 3 : Amérique du Nord + Océanie
    'US', 'MX', 'AU', 'NZ',
    # Tier 4 : Europe du Nord
    'DK', 'SE', 'NO', 'FI',
    # Tier 5 : DOM-TOM français
    'GP', 'MQ', 'GF', 'RE', 'YT', 'NC', 'PF', 'PM', 'WF', 'MF',
]

# Délai entre les appels API (respect rate limit CJ Free tier)
API_DELAY = 1.5  # secondes entre appels
MAX_CONSECUTIVE_429 = 2  # arrêt quota après N 429 consécutifs


def get_ordered_countries():
    """Retourne TARGET_COUNTRIES ordonnés par priorité (PRIORITY d'abord, puis le reste)"""
    ordered = list(PRIORITY_COUNTRIES)
    for c in TARGET_COUNTRIES:
        if c not in ordered:
            ordered.append(c)
    return ordered


def load_progress():
    """Charger la progression depuis le fichier JSON"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        'completed_pairs': [],  # Liste de "product_id:country_code" déjà sync
        'last_run': None,
        'total_synced': 0,
        'total_empty': 0,
        'total_errors': 0,
        'daily_calls': 0,
        'daily_date': None,
    }


def save_progress(progress):
    """Sauvegarder la progression dans le fichier JSON"""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)
    except IOError as e:
        logger.error(f"Impossible de sauvegarder la progression: {e}")


def show_status():
    """Afficher l'état de la progression"""
    progress = load_progress()
    completed = len(progress.get('completed_pairs', []))
    
    app = create_app()
    with app.app_context():
        from models.product_variant import ProductVariant
        total_products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.is_active == True
        ).join(
            ProductVariant, ProductVariant.product_id == Product.id
        ).filter(
            ProductVariant.active == True,
            ProductVariant.sku.isnot(None),
            ProductVariant.sku != ''
        ).distinct().count()
    
    total_countries = len(TARGET_COUNTRIES)
    total_pairs = total_products * total_countries
    pct = (completed / total_pairs * 100) if total_pairs > 0 else 0
    remaining = total_pairs - completed
    days_left = (remaining // DAILY_QUOTA) + (1 if remaining % DAILY_QUOTA else 0)
    
    print(f"\n{'='*50}")
    print(f"  SYNC SHIPPING - PROGRESSION")
    print(f"{'='*50}")
    print(f"  Produits CJ actifs : {total_products}")
    print(f"  Pays cibles        : {total_countries}")
    print(f"  Total combinaisons : {total_pairs}")
    print(f"  Deja synchronises  : {completed} ({pct:.1f}%)")
    print(f"  Restant            : {remaining}")
    print(f"  Jours estimes      : ~{days_left} jours ({DAILY_QUOTA} req/jour)")
    print(f"  Dernier run        : {progress.get('last_run', 'jamais')}")
    print(f"  Appels aujourd'hui : {progress.get('daily_calls', 0)}")
    print(f"  Synced total       : {progress.get('total_synced', 0)}")
    print(f"  Empty total        : {progress.get('total_empty', 0)}")
    print(f"  Errors total       : {progress.get('total_errors', 0)}")
    print(f"{'='*50}\n")


def get_cj_api():
    """Initialiser l'API CJ"""
    from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
    return CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )


def get_sku_for_product(product):
    """Récupérer le SKU CJ de la première variante active d'un produit"""
    from models.product_variant import ProductVariant
    variant = ProductVariant.query.filter_by(
        product_id=product.id, active=True
    ).filter(ProductVariant.sku.isnot(None), ProductVariant.sku != '').first()
    if variant and variant.sku:
        return variant.sku
    return None


def sync_product_shipping(cj_api, product, country_code):
    """
    Calculer et stocker les frais de livraison pour un produit et un pays
    via freightCalculateTip + SKU.
    Retourne: 'synced', 'empty', 'quota_hit', ou 'error'
    """
    try:
        sku = get_sku_for_product(product)
        if not sku:
            return 'error'
        
        # Appeler freightCalculateTip avec SKU
        freight_data = {
            'reqDTOS': [{
                'srcAreaCode': 'CN',
                'destAreaCode': country_code,
                'productProp': ['COMMON'],
                'freightTrialSkuList': [{'skuQuantity': 1, 'sku': sku}],
                'skuList': [sku],
                'platforms': ['Shopify']
            }]
        }
        
        response = cj_api._make_request('POST', 'logistic/freightCalculateTip', max_retries=1, json=freight_data)
        
        if response is None:
            return 'quota_hit'
        
        # Vérifier si c'est un rate limit dans le JSON
        if response.get('code') == 1600200:
            return 'quota_hit'
        
        if response.get('result') is False:
            ShippingRate.upsert(product.id, country_code, [], source='cj_empty')
            return 'empty'
        
        raw_methods = response.get('data', [])
        if not raw_methods:
            ShippingRate.upsert(product.id, country_code, [], source='cj_empty')
            return 'empty'
        
        # Formater les méthodes (format freightCalculateTip, prix convertis en EUR)
        methods = []
        for m in raw_methods:
            option = m.get('option', {})
            price_usd = float(m.get('discountFee', m.get('postage', 0)))
            price_eur = round(price_usd * USD_TO_EUR, 2)
            methods.append({
                'code': option.get('enName', 'UNKNOWN'),
                'name': option.get('enName', 'Méthode inconnue'),
                'price': price_eur,
                'price_usd': price_usd,
                'price_cny': float(m.get('discountFeeCNY', m.get('postageCNY', 0))),
                'delivery_time': m.get('arrivalTime', 'N/A'),
                'source': 'cj'
            })
        
        # Stocker en DB
        ShippingRate.upsert(product.id, country_code, methods, source='cj')
        return 'synced'
        
    except Exception as e:
        logger.error(f"  Erreur sync P{product.id} -> {country_code}: {e}")
        return 'error'


def run_sync(countries, limit=None, refresh_only=False, max_age_days=7, resume=False):
    """
    Sync progressive des frais de livraison.
    Respecte le quota journalier CJ (950 req/jour).
    Sauvegarde la progression pour reprendre le lendemain.
    """
    
    app = create_app()
    with app.app_context():
        # Charger la progression
        progress = load_progress()
        completed_set = set(progress.get('completed_pairs', []))
        
        # Reset compteur journalier si nouveau jour
        today = datetime.now().strftime('%Y-%m-%d')
        if progress.get('daily_date') != today:
            progress['daily_calls'] = 0
            progress['daily_date'] = today
        
        daily_calls = progress['daily_calls']
        
        if daily_calls >= DAILY_QUOTA:
            logger.warning(f"Quota journalier atteint ({daily_calls}/{DAILY_QUOTA}). Relancez demain.")
            logger.info("Utilisez --status pour voir la progression.")
            save_progress(progress)
            return
        
        remaining_quota = DAILY_QUOTA - daily_calls
        logger.info(f"Quota restant aujourd'hui: {remaining_quota}/{DAILY_QUOTA}")
        
        # Récupérer les produits CJ actifs AVEC un SKU valide
        from models.product_variant import ProductVariant
        query = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.is_active == True
        ).join(
            ProductVariant, ProductVariant.product_id == Product.id
        ).filter(
            ProductVariant.active == True,
            ProductVariant.sku.isnot(None),
            ProductVariant.sku != ''
        ).distinct().order_by(Product.id)
        
        if limit:
            query = query.limit(limit)
        
        products = query.all()
        total_products = len(products)
        
        # Construire la liste des paires (product, country) à traiter
        pairs_todo = []
        for country in countries:
            for product in products:
                pair_key = f"{product.id}:{country}"
                if resume and pair_key in completed_set:
                    continue
                if refresh_only:
                    existing = ShippingRate.get_for_product(product.id, country)
                    if existing and not existing.is_expired(max_age_days):
                        continue
                pairs_todo.append((product, country, pair_key))
        
        total_todo = len(pairs_todo)
        total_overall = total_products * len(countries)
        will_do = min(total_todo, remaining_quota)
        
        logger.info(f"=== Sync Shipping Progressive ===")
        logger.info(f"Produits CJ: {total_products}")
        logger.info(f"Pays cibles: {len(countries)}")
        logger.info(f"Deja fait: {len(completed_set)} paires")
        logger.info(f"Restant: {total_todo} paires")
        logger.info(f"Session: {will_do} paires (quota {remaining_quota})")
        logger.info(f"Duree estimee: ~{(will_do * API_DELAY) / 60:.0f} min")
        logger.info(f"Progression globale: {len(completed_set)}/{total_overall} ({len(completed_set)/total_overall*100:.1f}%)" if total_overall > 0 else "")
        logger.info(f"=================================")
        
        if total_todo == 0:
            logger.info("Tout est deja synchronise !")
            return
        
        # Initialiser l'API CJ
        try:
            cj_api = get_cj_api()
            from services.api_providers.cj_dropshipping_optimized import _memory_cache
            _memory_cache['min_interval'] = 1.5
            logger.info("[OK] API CJ initialisee (min_interval=1.5s)")
        except Exception as e:
            logger.error(f"[ERREUR] Impossible d'initialiser l'API CJ: {e}")
            return
        
        stats = {'synced': 0, 'empty': 0, 'errors': 0, 'quota_hit': False}
        start_time = time.time()
        consecutive_429 = 0
        current_country = None
        country_synced = 0
        
        for i, (product, country, pair_key) in enumerate(pairs_todo):
            # Vérifier quota
            if daily_calls >= DAILY_QUOTA:
                logger.warning(f"Quota journalier atteint ({daily_calls}/{DAILY_QUOTA}). Arret propre.")
                stats['quota_hit'] = True
                break
            
            # Log changement de pays
            if country != current_country:
                if current_country is not None:
                    db.session.commit()
                    logger.info(f"  -> {current_country}: {country_synced} synced cette session")
                current_country = country
                country_synced = 0
                logger.info(f"[{country}] Debut sync...")
            
            # Appeler l'API CJ
            result = sync_product_shipping(cj_api, product, country)
            daily_calls += 1
            
            if result == 'synced':
                stats['synced'] += 1
                country_synced += 1
                completed_set.add(pair_key)
                consecutive_429 = 0
            elif result == 'empty':
                stats['empty'] += 1
                completed_set.add(pair_key)
                consecutive_429 = 0
            elif result == 'quota_hit':
                consecutive_429 += 1
                stats['errors'] += 1
                if consecutive_429 >= MAX_CONSECUTIVE_429:
                    logger.warning(f"Quota CJ epuise ({consecutive_429} x 429 consecutifs). Arret.")
                    stats['quota_hit'] = True
                    break
            else:
                stats['errors'] += 1
                consecutive_429 = 0
            
            # Respecter le rate limit
            time.sleep(API_DELAY)
            
            # Log progression tous les 25 appels
            if (i + 1) % 25 == 0:
                elapsed = time.time() - start_time
                total_done = len(completed_set)
                pct = total_done / total_overall * 100 if total_overall > 0 else 0
                logger.info(
                    f"  [{i+1}/{will_do}] {stats['synced']}ok {stats['empty']}empty {stats['errors']}err "
                    f"| Global: {total_done}/{total_overall} ({pct:.1f}%) "
                    f"| Quota: {daily_calls}/{DAILY_QUOTA} "
                    f"| {elapsed/60:.1f}min"
                )
            
            # Commit tous les 50 appels
            if (i + 1) % 50 == 0:
                db.session.commit()
                # Sauvegarder progression (paires + quota seulement, totaux à la fin)
                progress['completed_pairs'] = list(completed_set)
                progress['daily_calls'] = daily_calls
                save_progress(progress)
        
        # Commit final
        db.session.commit()
        
        # Sauvegarder progression finale
        progress['completed_pairs'] = list(completed_set)
        progress['daily_calls'] = daily_calls
        progress['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        progress['total_synced'] = progress.get('total_synced', 0) + stats['synced']
        progress['total_empty'] = progress.get('total_empty', 0) + stats['empty']
        progress['total_errors'] = progress.get('total_errors', 0) + stats['errors']
        save_progress(progress)
        
        # Résultats
        elapsed = time.time() - start_time
        total_done = len(completed_set)
        pct = total_done / total_overall * 100 if total_overall > 0 else 0
        remaining = total_overall - total_done
        days_left = (remaining // DAILY_QUOTA) + (1 if remaining % DAILY_QUOTA else 0)
        
        logger.info(f"\n{'='*50}")
        logger.info(f"  SESSION TERMINEE")
        logger.info(f"{'='*50}")
        logger.info(f"  Synced:  {stats['synced']}")
        logger.info(f"  Empty:   {stats['empty']}")
        logger.info(f"  Errors:  {stats['errors']}")
        logger.info(f"  Duree:   {elapsed/60:.1f} min")
        logger.info(f"  Quota:   {daily_calls}/{DAILY_QUOTA} utilise")
        logger.info(f"{'='*50}")
        logger.info(f"  PROGRESSION GLOBALE")
        logger.info(f"  Fait:    {total_done}/{total_overall} ({pct:.1f}%)")
        logger.info(f"  Restant: {remaining}")
        logger.info(f"  Jours:   ~{days_left} jours restants")
        if stats['quota_hit']:
            logger.info(f"  -> Relancez demain: python scripts/sync_shipping_rates.py --resume")
        logger.info(f"{'='*50}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync progressive shipping rates from CJ API')
    parser.add_argument('--countries', type=str, default=None,
                        help='Pays cibles séparés par virgule (ex: FR,BE,CH)')
    parser.add_argument('--all', action='store_true',
                        help='Synchroniser TOUS les pays CJ (ordre prioritaire)')
    parser.add_argument('--resume', action='store_true',
                        help='Reprendre la sync progressive où on s\'est arrêté')
    parser.add_argument('--status', action='store_true',
                        help='Afficher la progression actuelle')
    parser.add_argument('--reset', action='store_true',
                        help='Remettre la progression à zéro')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limiter le nombre de produits')
    parser.add_argument('--refresh', action='store_true',
                        help='Re-sync uniquement les expirés (> 7 jours)')
    parser.add_argument('--max-age', type=int, default=7,
                        help='Âge max en jours avant refresh (défaut: 7)')
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
        sys.exit(0)
    
    if args.reset:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            print("Progression remise a zero.")
        else:
            print("Pas de fichier de progression.")
        sys.exit(0)
    
    # Déterminer les pays
    if args.resume or args.all:
        countries = get_ordered_countries()
        resume = True
    elif args.countries:
        countries = [c.strip().upper() for c in args.countries.split(',')]
        resume = False
    else:
        countries = get_ordered_countries()
        resume = True
    
    run_sync(countries, limit=args.limit, refresh_only=args.refresh,
             max_age_days=args.max_age, resume=resume)
