"""Répare la couleur et la taille des variantes CJ coupées au premier tiret du nom (ancien import).

Usage (conteneur multiproshop-web) :
    python scripts/repair_variant_options.py            # simulation : affiche ce qui changerait
    python scripts/repair_variant_options.py --apply    # applique, après sauvegarde JSON des anciennes valeurs
Options : --all (toutes les variantes, pas seulement celles des produits en ligne), --backup FICHIER.
Les libellés saisis à la main (sans les valeurs de la clé CJ) ne sont jamais modifiés.
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--backup', default=f"instance/variantes_avant_{datetime.utcnow():%Y%m%d_%H%M}.json")
    args = parser.parse_args()

    from app import app
    from extensions import db, cache
    from models.product import Product
    from models.product_variant import ProductVariant
    from utils.variant_keys import product_key_names, repair_variant

    with app.app_context():
        query = Product.query.filter(Product.cj_pid.isnot(None))
        if not args.all:
            query = query.filter(Product.is_active.is_(True))
        changes, products = [], set()
        for product in query.all():
            names = product_key_names(product)
            for v in ProductVariant.query.filter_by(product_id=product.id).all():
                before = (v.color, v.size)
                if repair_variant(v, names):
                    changes.append({'variant_id': v.id, 'product_id': product.id, 'key': v.variant_key,
                                    'before': before, 'after': (v.color, v.size)})
                    products.add(product.id)
        for c in changes[:40]:
            print(f"#{c['product_id']} v{c['variant_id']} [{c['key']}] {c['before']} -> {c['after']}")
        print(f'{len(changes)} variantes sur {len(products)} produits à corriger')
        if not args.apply:
            db.session.rollback()
            print('Simulation : rien n’est enregistré (ajoutez --apply).')
            return
        os.makedirs(os.path.dirname(args.backup) or '.', exist_ok=True)
        with open(args.backup, 'w') as f:
            json.dump(changes, f, ensure_ascii=False, indent=1)
        db.session.commit()
        for pid in products:
            try:
                cache.delete(f'flask_cache_view//products/{pid}')
            except Exception:
                pass
        print(f'Appliqué. Sauvegarde des anciennes valeurs : {args.backup}')


if __name__ == '__main__':
    main()
