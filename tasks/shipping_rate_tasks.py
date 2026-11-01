"""
Tarifs de livraison des fiches produit, enregistrés chaque semaine en base (table shipping_rate).
La fiche produit lit ce tarif au lieu d'interroger CJ à chaque visite ; le panier et la commande
gardent un calcul CJ en direct sur le panier réel.
"""
import logging

from celery_app import celery
from app import app

logger = logging.getLogger(__name__)

COUNTRIES = ('FR', 'RE')
FRESH_DAYS = 6          # un tarif de moins de 6 jours n'est pas redemandé
MAX_CJ_FAILURES = 5     # CJ injoignable ou quota atteint : on arrête et on reprendra la semaine suivante


@celery.task(name='tasks.shipping_rate_tasks.refresh_shipping_rates')
def refresh_shipping_rates(countries=COUNTRIES):
    """Une unité de chaque produit en ligne, vers chaque pays. Les appels CJ passent par la file
    partagée (1 par seconde environ), soit une vingtaine de minutes pour 400 produits et 2 pays."""
    from models.product import Product
    from models.shipping_rate import ShippingRate
    from services.shipping_service import ShippingService
    from extensions import db

    with app.app_context():
        service = ShippingService()
        if not service.cj_api:
            return {'success': False, 'reason': 'cj_unavailable'}
        products = Product.query.filter(Product.is_active == True, Product.published_at.isnot(None)) \
            .order_by(Product.id).all()
        stats = {'updated': 0, 'not_deliverable': 0, 'fresh': 0, 'skipped': 0}
        failures = 0
        for product in products:
            for country in countries:
                rate = ShippingRate.get_for_product(product.id, country)
                if rate and rate.source in ShippingService.RATE_SOURCES and not rate.is_expired(FRESH_DAYS):
                    stats['fresh'] += 1
                    continue
                try:
                    methods = service.refresh_product_rate(product, country)
                except Exception as e:
                    logger.warning(f"[Tarifs] Produit {product.id} -> {country}: {e}")
                    methods = None
                if methods is None:
                    stats['skipped'] += 1
                    if service._first_vid(product):
                        failures += 1
                        if failures >= MAX_CJ_FAILURES:
                            logger.error('[Tarifs] CJ ne répond plus, arrêt : %s', stats)
                            return {'success': False, 'reason': 'cj_failures', **stats}
                    continue
                failures = 0
                ShippingService.store_rate(product.id, country, methods, commit=False)
                stats['updated' if methods else 'not_deliverable'] += 1
            db.session.commit()
        logger.info('[Tarifs] Rafraîchissement terminé : %s', stats)
        return {'success': True, **stats}
