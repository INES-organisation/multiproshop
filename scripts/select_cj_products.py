"""
Sélection des meilleurs produits CJ par famille, pour remplacer le catalogue de test.

Lecture seule : interroge l'API CJ et écrit une liste à valider (CSV + JSON). Rien n'est
importé ni publié, la base n'est pas touchée.

Pour chaque sous-catégorie CJ (niveau 2) des familles retenues :
  1. les produits les plus listés par les boutiques CJ (product/listV2, tri listedNum), dans
     une fourchette de prix d'achat, au niveau mondial puis avec du stock en France ;
  2. le détail des mieux classés (photos, poids, stock, variantes) ;
  3. un filtre (photos, poids, stock, mots exclus) et un prix de vente proposé.

Usage (sur le VPS, dans un conteneur qui a les clés CJ) :
  docker compose -f deploy/docker-compose.yml --env-file deploy/.env exec multiproshop-web \\
    python scripts/select_cj_products.py --list-categories
  ... python scripts/select_cj_products.py --per-category 20 --out instance/selection_cj

Budget API : CJ limite à 1 000 requêtes par jour. Compter 2 requêtes par sous-catégorie et
1 par produit détaillé ; --max-details plafonne le total.
"""
import argparse
import csv
import json
import math
import os
import re
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config  # noqa: E402,F401 — charge les clés CJ depuis INES dans l'environnement
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized  # noqa: E402

# Familles du futur catalogue → mots qui repèrent leurs catégories CJ de niveau 1
FAMILIES = {
    'Maison & déco': ['home, garden', 'home & garden', 'furniture', 'home improvement'],
    'Cuisine': ['kitchen'],
    'High-tech': ['consumer electronics', 'phones', 'computer', 'electronic'],
    'Beauté & bien-être': ['health, beauty', 'beauty', 'hair'],
    'Sport & plein air': ['sports', 'outdoor'],
    'Animaux': ['pet'],
    'Enfants & jouets': ['toys', 'kids', 'baby', 'babies'],
    'Auto & moto': ['automobile', 'motorcycle'],
    'Bijoux & montres': ['jewelry', 'watches'],
    'Sacs & accessoires': ['bags', 'luggage'],
}

# Produits écartés d'office : marques, réglementés ou risqués à vendre sans fiche française
EXCLUDED_WORDS = [
    'apple', 'iphone case for apple', 'samsung', 'nike', 'adidas', 'disney', 'marvel', 'pokemon', 'lego',
    'gucci', 'chanel', 'louis vuitton', 'rolex', 'dyson', 'airpods', 'xiaomi', 'huawei',
    'knife', 'dagger', 'sword', 'gun', 'pistol', 'airsoft', 'crossbow', 'taser', 'stun gun',
    'e-cigarette', 'vape', 'tobacco', 'hookah', 'cbd', 'sex', 'adult', 'lingerie', 'erotic',
    'medicine', 'supplement', 'capsule', 'pill', 'food', 'snack', 'coffee bean',
    'lithium battery', '18650', 'power bank 20000', 'drone',
]


EXCLUDED = re.compile(r'\b(' + '|'.join(re.escape(w) for w in EXCLUDED_WORDS) + r')\b', re.I)


def selling_price(cost_eur, coefficients):
    """Prix de vente : coefficient selon le coût, arrondi à x,90 €, plancher 9,90 €"""
    coef = next(c for limit, c in coefficients if cost_eur < limit)
    return max(9.90, math.ceil(cost_eur * coef) - 0.10)


def parse_weight_g(value):
    nums = re.findall(r'[\d.]+', str(value or ''))
    return max(float(n) for n in nums) if nums else 0.0


def family_of(level1_name):
    name = level1_name.lower()
    for family, words in FAMILIES.items():
        if any(w in name for w in words):
            return family
    return None


def list_products(api, category_id, args, country=None):
    """Produits d'une sous-catégorie, les plus listés d'abord (product/listV2)"""
    params = {
        'page': 1, 'size': args.candidates, 'categoryId': category_id,
        'orderBy': 1, 'sort': 'desc',
        'startSellPrice': args.min_cost, 'endSellPrice': args.max_cost,
    }
    if country:
        params['countryCode'] = country
    response = api._make_request('GET', 'product/listV2', params=params)
    if not response or response.get('result') is False:
        return []
    products = []
    for item in (response.get('data') or {}).get('content', []):
        for p in item.get('productList', []):
            products.append({
                'pid': p.get('id'),
                'name_en': p.get('nameEn', ''),
                'image': p.get('bigImage', ''),
                'listed': int(p.get('listedNum') or 0),
                'stock_fr': country == 'FR',
            })
    return products


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--list-categories', action='store_true', help='affiche les catégories CJ et leur famille, puis s\'arrête')
    parser.add_argument('--families', help='familles à traiter, séparées par des virgules (défaut : toutes)')
    parser.add_argument('--per-category', type=int, default=20, help='produits retenus par sous-catégorie')
    parser.add_argument('--candidates', type=int, default=50, help='produits examinés par sous-catégorie et par requête')
    parser.add_argument('--min-cost', type=float, default=2.0, help='prix d\'achat CJ minimum (USD)')
    parser.add_argument('--max-cost', type=float, default=40.0, help='prix d\'achat CJ maximum (USD)')
    parser.add_argument('--min-images', type=int, default=4)
    parser.add_argument('--max-weight', type=float, default=2000, help='poids maximum (g)')
    parser.add_argument('--min-stock', type=int, default=50)
    parser.add_argument('--usd-eur', type=float, default=0.92, help='taux de conversion du coût CJ')
    parser.add_argument('--max-details', type=int, default=600, help='plafond de requêtes de détail')
    parser.add_argument('--out', default='instance/selection_cj', help='préfixe des fichiers produits (.csv, .json)')
    args = parser.parse_args()

    coefficients = [(10, 2.5), (30, 2.0), (float('inf'), 1.6)]
    api = CJDropshippingApiOptimized(email=os.getenv('CJ_EMAIL'), password=os.getenv('CJ_PASSWORD'),
                                     dev_key=os.getenv('CJ_DEV_KEY'))
    categories = api.get_categories()
    if not categories:
        sys.exit('Catégories CJ non récupérées (clés CJ ou limite de requêtes) : rien à faire.')

    level1 = {c['id']: c for c in categories if c['level'] == 1}
    wanted = {f.strip() for f in args.families.split(',')} if args.families else set(FAMILIES)
    targets = []
    for c in categories:
        if c['level'] != 2:
            continue
        family = family_of(level1.get(c['parent_id'], {}).get('name', ''))
        if family in wanted:
            targets.append((family, c))

    if args.list_categories:
        for c in level1.values():
            print(f"{family_of(c['name']) or '— hors familles —':22} | {c['name']}")
        print(f"\n{len(targets)} sous-catégories retenues, environ {2 * len(targets)} requêtes de liste")
        return

    print(f"{len(targets)} sous-catégories, jusqu'à {args.max_details} détails ; compter ~{(2 * len(targets) + args.max_details) * 1.5 / 60:.0f} min")
    selected, details_used, started = [], 0, time.time()
    for family, cat in targets:
        candidates = {}
        for country in (None, 'FR'):
            for p in list_products(api, cat['id'], args, country):
                if EXCLUDED.search(p['name_en']):
                    continue
                known = candidates.setdefault(p['pid'], p)
                known['stock_fr'] = known['stock_fr'] or p['stock_fr']
        # Stock en France d'abord, puis popularité
        ranked = sorted(candidates.values(), key=lambda p: (p['stock_fr'], p['listed']), reverse=True)
        kept = 0
        for p in ranked:
            if kept >= args.per_category or details_used >= args.max_details:
                break
            details_used += 1
            d = api.get_product_details(p['pid'])
            if not d:
                continue
            weight = parse_weight_g(d.get('weight'))
            reasons = []
            if len(d.get('images') or []) < args.min_images:
                reasons.append('photos')
            if weight > args.max_weight:
                reasons.append('poids')
            if d.get('stock', 0) < args.min_stock:
                reasons.append('stock')
            if reasons:
                continue
            cost_eur = round(d['price'] * args.usd_eur, 2)
            price = selling_price(cost_eur, coefficients)
            selected.append({
                'famille': family,
                'categorie_cj': cat['path'],
                'pid': p['pid'],
                'nom_en': d['name_en'] or p['name_en'],
                'image': d['image'] or p['image'],
                'photos': len(d['images']),
                'variantes': len(d['variants']),
                'poids_g': round(weight),
                'stock': d['stock'],
                'stock_france': 'oui' if p['stock_fr'] else 'non',
                'boutiques_cj': p['listed'],
                'cout_usd': d['price'],
                'cout_eur': cost_eur,
                'prix_vente_eur': price,
                'marge_eur': round(price - cost_eur, 2),
            })
            kept += 1
        print(f"  {family:20} | {cat['path'][:60]:60} | {kept} retenus ({len(candidates)} candidats)")
        if details_used >= args.max_details:
            print(f"Plafond de {args.max_details} détails atteint : arrêt (relancer avec --families pour la suite)")
            break

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out + '.json', 'w', encoding='utf-8') as f:
        json.dump(selected, f, ensure_ascii=False, indent=1)
    if selected:
        with open(args.out + '.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(selected[0]), delimiter=';')
            writer.writeheader()
            writer.writerows(selected)
    print(f"\n{len(selected)} produits retenus en {(time.time() - started) / 60:.0f} min → {args.out}.csv / .json")


if __name__ == '__main__':
    main()
