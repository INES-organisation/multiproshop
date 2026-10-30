"""
Publication des produits retenus par select_cj_products.py.

Pour chaque produit de la liste (JSON produit par la sélection) :
  1. la fiche CJ complète (1 requête product/query : description, photos, variantes) ;
  2. création du produit, ou mise à jour s'il existe déjà (même cj_pid), publié tout de suite ;
  3. prix : ceux de la sélection (coût CJ × coefficient, arrondi à x,90 €), et pour chaque
     variante le même calcul sur son propre coût. Jamais de prix barré inventé.

Le nom affiché est `nom_fr` s'il est présent dans le fichier, sinon le nom anglais de CJ.
Les identifiants créés ou mis à jour sont écrits dans <fichier>.publies.json, pour pouvoir
dépublier ce lot d'un coup (--unpublish).

Usage (dans le conteneur web) :
  python scripts/import_selection.py instance/selection_cj_1.json --dry-run
  python scripts/import_selection.py instance/selection_cj_1.json
  python scripts/import_selection.py instance/selection_cj_1.json --unpublish
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app  # noqa: E402
from extensions import db  # noqa: E402
from models.category import Category  # noqa: E402
from models.product import Product  # noqa: E402
from models.product_variant import ProductVariant  # noqa: E402
from scripts.select_cj_products import QuotaExhausted, cj_call, selling_price  # noqa: E402
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized  # noqa: E402

COEFFICIENTS = [(10, 2.5), (30, 2.0), (float('inf'), 1.6)]


def unique_slug(name):
    from slugify import slugify
    base = slugify(name)[:200] or 'produit'
    slug, n = base, 1
    while Product.query.filter_by(slug=slug).first():
        n += 1
        slug = f'{base}-{n}'
    return slug


def category_for(item, details):
    """Catégorie CJ du produit ; à défaut sa sous-catégorie de sélection (« Pet Supplies > Pet Toys »),
    puis sa catégorie de premier niveau"""
    if details.get('category_id'):
        category = Category.query.filter_by(cj_category_id=details['category_id']).first()
        if category:
            return category
    for name in reversed([n.strip() for n in item.get('categorie_cj', '').split('>')]):
        category = Category.query.filter_by(name=name).first()
        if category:
            return category
    return Category.query.filter_by(level=1).first()


def publish(item, details, usd_eur):
    product = Product.query.filter_by(cj_pid=item['pid']).first()
    name = item.get('nom_fr') or details.get('name_en') or item['nom_en']
    images = details.get('images') or []
    category = category_for(item, details)
    if not product:
        product = Product(cj_pid=item['pid'], slug=unique_slug(name),
                          sku=(details.get('sku') or f"CJ-{item['pid'][:10]}")[:50])
        db.session.add(product)
    product.name = name[:255]
    product.description = details.get('description') or product.description
    product.cost_price = item['cout_eur']
    product.price = item['prix_vente_eur']
    product.compare_price = None
    product.suggested_price = details.get('suggested_price')
    product.stock = item['stock']
    product.image_url = (images[0] if images else item.get('image') or '')[:1000] or None
    product.set_images_list(images[1:])
    product.product_weight = str(details.get('weight') or '')[:50] or None
    product.material = str(details.get('material') or '')[:255] or None
    product.category_id = category.id
    product.is_active = True
    product.published = True
    product.published_at = product.published_at or datetime.utcnow()
    product.synced_at = product.cj_last_sync = datetime.utcnow()
    product.cj_raw_data = json.dumps(details.get('raw_data') or {}, ensure_ascii=False)
    db.session.flush()

    ProductVariant.query.filter_by(product_id=product.id).delete()
    for v in details.get('variants') or []:
        if not v.get('vid'):
            continue
        key = v.get('key') or ''
        parts = key.split('-')
        cost_eur = round((v.get('price') or 0) * usd_eur, 2)
        db.session.add(ProductVariant(
            product_id=product.id, cj_vid=v['vid'], variant_key=key,
            color=parts[0] if parts and parts[0] else None, size=parts[1] if len(parts) > 1 else None,
            # Prix de vente de la variante, calculé sur son coût ; à défaut celui du produit
            price=selling_price(cost_eur, COEFFICIENTS) if cost_eur > 0 else None,
            stock=0,  # stock inconnu : la fiche et le panier prennent celui du produit
            image_url=v.get('image'), weight=int(float(v['weight'])) if v.get('weight') else None,
            sku=v.get('sku'), active=True, cj_raw_data=json.dumps(v, ensure_ascii=False, default=str),
        ))
    return product


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', help='liste JSON produite par select_cj_products.py')
    parser.add_argument('--dry-run', action='store_true', help='affiche ce qui serait publié, sans appel CJ ni écriture')
    parser.add_argument('--limit', type=int, help='nombre maximum de produits à publier')
    parser.add_argument('--usd-eur', type=float, default=0.92)
    parser.add_argument('--unpublish', action='store_true', help='dépublie les produits publiés depuis ce fichier')
    args = parser.parse_args()

    log_path = os.path.splitext(args.file)[0] + '.publies.json'
    with open(args.file, encoding='utf-8') as f:
        items = json.load(f)
    seen, unique = set(), []
    for item in items:  # un produit peut sortir dans deux passages de sélection
        if item['pid'] not in seen:
            seen.add(item['pid'])
            unique.append(item)
    items = unique[:args.limit] if args.limit else unique

    with app.app_context():
        if args.unpublish:
            ids = json.load(open(log_path, encoding='utf-8'))
            n = Product.query.filter(Product.id.in_(ids)).update(
                {Product.is_active: False, Product.published: False}, synchronize_session=False)
            db.session.commit()
            print(f'{n} produits dépubliés')
            return

        if args.dry_run:
            for item in items:
                state = 'mise à jour' if Product.query.filter_by(cj_pid=item['pid']).first() else 'création'
                print(f"{state:11} | {item['famille']:18} | {item['prix_vente_eur']:6.2f} € | {item.get('nom_fr') or item['nom_en']}")
            print(f'\n{len(items)} produits')
            return

        api = CJDropshippingApiOptimized(email=os.getenv('CJ_EMAIL'), password=os.getenv('CJ_PASSWORD'),
                                         dev_key=os.getenv('CJ_DEV_KEY'))
        published = json.load(open(log_path, encoding='utf-8')) if os.path.exists(log_path) else []
        done = 0
        try:
            for item in items:
                response = cj_call(api, 'product/query', {'pid': item['pid']})
                if not response or response.get('result') is False or not response.get('data'):
                    print(f"  ignoré (fiche CJ indisponible) : {item['nom_en']}")
                    continue
                try:
                    product = publish(item, api._format_product(response['data']), args.usd_eur)
                    db.session.commit()
                except Exception as e:  # noqa: BLE001 — un produit en échec ne bloque pas le lot
                    db.session.rollback()
                    print(f"  échec : {item['nom_en']} ({e})")
                    continue
                if product.id not in published:
                    published.append(product.id)
                done += 1
                if done % 20 == 0:
                    print(f'  {done} publiés')
        except QuotaExhausted as e:
            print(f'\nArrêt : {e}. Relancer plus tard : les produits déjà publiés seront mis à jour.')
        finally:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(published, f)
        print(f'\n{done} produits publiés → identifiants dans {log_path}')


if __name__ == '__main__':
    main()
