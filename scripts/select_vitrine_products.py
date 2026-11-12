"""
Sélection de produits pour une vitrine ou une boutique, à partir d'une fiche de mots-clés.

Lecture seule : rien n'est importé ni publié. Pour chaque recherche de la fiche
(scripts/vitrines/<projet>.json) :
  1. les produits déjà dans MPS qui y répondent (nom en français, motifs « db »), pour les
     rattacher à la vitrine sans rien réimporter ;
  2. sur CJ, les produits les plus listés par les boutiques CJ pour ces mots (product/listV2,
     keyWord, tri listedNum), dans la fourchette de prix d'achat ;
  3. le détail des premiers (photos, poids, stock) avec les mêmes filtres et le même prix de
     vente que select_cj_products.py (coefficient selon le coût, arrondi à x,90 €).

Le résultat (<sortie>.json et .csv) se relit, puis s'importe en brouillon rattaché à la vitrine :
  python scripts/import_selection.py <sortie>.json --project <projet> --draft

Usage (dans le conteneur web, qui a les clés CJ) :
  python scripts/select_vitrine_products.py scripts/vitrines/tonyalpha.json --out instance/vitrine_tonyalpha
  python scripts/select_vitrine_products.py scripts/vitrines/digita.json --db-only

Budget CJ : 1 liste par recherche, puis 1 détail et 1 à 3 stocks par produit examiné.
"""
import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.select_cj_products import (  # noqa: E402
    EXCLUDED, QuotaExhausted, cj_call, parse_weight_g, selling_price)

COEFFICIENTS = [(10, 2.5), (30, 2.0), (float('inf'), 1.6)]


def existing_products(patterns, limit=5):
    """Produits MPS (actifs) dont le nom répond à un des motifs SQL LIKE, sans tenir compte de la casse"""
    from extensions import db
    from models.product import Product
    if not patterns:
        return []
    query = Product.query.filter(Product.is_active.is_(True), db.or_(
        *[Product.name.ilike(f'%{p}%') for p in patterns]))
    return [{'id': p.id, 'nom': p.name, 'prix': p.price, 'publie': bool(p.published),
             'vitrines': p.projects or ''} for p in query.order_by(Product.published.desc(), Product.id).limit(limit)]


def search_cj(api, keyword, args):
    params = {'page': 1, 'size': args.candidates, 'keyWord': keyword, 'orderBy': 1, 'sort': 'desc',
              'startSellPrice': args.min_cost, 'endSellPrice': args.max_cost}
    response = cj_call(api, 'product/listV2', params)
    if not response or response.get('result') is False:
        return []
    found = []
    for item in (response.get('data') or {}).get('content', []):
        for p in item.get('productList', []):
            if not EXCLUDED.search(p.get('nameEn', '')):
                found.append({'pid': p.get('id'), 'name_en': p.get('nameEn', ''), 'image': p.get('bigImage', ''),
                              'listed': int(p.get('listedNum') or 0)})
    return sorted(found, key=lambda p: p['listed'], reverse=True)


def examine(api, p, args):
    """Fiche retenue, ou None avec la raison du rejet"""
    response = cj_call(api, 'product/query', {'pid': p['pid']})
    if not response or response.get('result') is False or not response.get('data'):
        return None, 'fiche'
    d = api._format_product(response['data'])
    weight = parse_weight_g(d.get('weight'))
    if len(d.get('images') or []) < args.min_images:
        return None, 'photos'
    if weight > args.max_weight:
        return None, 'poids'
    cost_usd = max([v['price'] for v in d['variants'] if v.get('price')] or [d['price']])
    if cost_usd <= 0:
        return None, 'prix'
    stock = api.get_stock(d['variants'], enough=args.min_stock, max_variants=3)
    if stock is None:
        return None, 'stock inconnu'
    if stock['total'] < args.min_stock:
        return None, 'stock'
    cost_eur = round(cost_usd * args.usd_eur, 2)
    price = selling_price(cost_eur, COEFFICIENTS)
    return {'d': d, 'weight': weight, 'stock': stock, 'cost_usd': cost_usd, 'cost_eur': cost_eur, 'price': price}, None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('brief', help='fiche de la vitrine (scripts/vitrines/<projet>.json)')
    parser.add_argument('--out', help='préfixe des fichiers produits (défaut : instance/vitrine_<projet>)')
    parser.add_argument('--per-query', type=int, default=2, help='produits CJ retenus par recherche')
    parser.add_argument('--candidates', type=int, default=20, help='produits CJ lus par recherche')
    parser.add_argument('--max-examined', type=int, default=6, help='fiches CJ détaillées au plus par recherche')
    parser.add_argument('--min-cost', type=float, default=1.5, help="prix d'achat CJ minimum (USD)")
    parser.add_argument('--max-cost', type=float, default=45.0, help="prix d'achat CJ maximum (USD)")
    parser.add_argument('--min-images', type=int, default=4)
    parser.add_argument('--max-weight', type=float, default=2500, help='poids maximum (g)')
    parser.add_argument('--min-stock', type=int, default=50)
    parser.add_argument('--usd-eur', type=float, default=0.92)
    parser.add_argument('--db-only', action='store_true', help='seulement les produits déjà dans MPS, sans appel CJ')
    args = parser.parse_args()

    with open(args.brief, encoding='utf-8') as f:
        brief = json.load(f)
    project = brief['project']
    out = args.out or f'instance/vitrine_{project}'

    from app import app
    from services.api_providers import cj_dropshipping_optimized as cj
    from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized

    selected, report, started = [], [], time.time()
    with app.app_context():
        api = None
        if not args.db_only:
            cj._memory_cache['min_interval'] = max(cj._memory_cache['min_interval'], 2.0)
            api = CJDropshippingApiOptimized(email=os.getenv('CJ_EMAIL'), password=os.getenv('CJ_PASSWORD'),
                                             dev_key=os.getenv('CJ_DEV_KEY'))
        try:
            for group in brief['groups']:
                for query in group['queries']:
                    line = {'groupe': group['name'], 'recherche': query['fr'],
                            'deja_dans_mps': existing_products(query.get('db', [])), 'cj': []}
                    report.append(line)
                    if api is None:
                        continue
                    rejected = {}
                    for p in search_cj(api, query['q'], args)[:args.max_examined]:
                        if len(line['cj']) >= args.per_query:
                            break
                        if any(s['pid'] == p['pid'] for s in selected):
                            continue
                        kept, reason = examine(api, p, args)
                        if not kept:
                            rejected[reason] = rejected.get(reason, 0) + 1
                            continue
                        d = kept['d']
                        item = {
                            'projet': project, 'famille': group['name'], 'groupe': group['name'],
                            'recherche': query['q'], 'categorie_cj': d.get('category_name') or '',
                            'pid': p['pid'], 'nom_en': d['name_en'] or p['name_en'], 'nom_fr': query['fr'],
                            'image': d['image'] or p['image'], 'photos': len(d['images']),
                            'variantes': len(d['variants']), 'poids_g': round(kept['weight']),
                            'stock': kept['stock']['total'],
                            'stock_france': 'oui' if kept['stock']['france'] else 'non',
                            'boutiques_cj': p['listed'], 'cout_usd': kept['cost_usd'], 'cout_eur': kept['cost_eur'],
                            'prix_vente_eur': kept['price'], 'marge_eur': round(kept['price'] - kept['cost_eur'], 2),
                        }
                        selected.append(item)
                        line['cj'].append({k: item[k] for k in ('pid', 'nom_en', 'prix_vente_eur', 'cout_eur',
                                                                'boutiques_cj', 'stock_france')})
                    line['ecartes'] = rejected
                    print(f"  {group['name'][:22]:22} | {query['fr'][:45]:45} | MPS {len(line['deja_dans_mps'])}"
                          f" | CJ {len(line['cj'])}" + (f" | écartés {rejected}" if rejected else ''))
        except QuotaExhausted as e:
            print(f'\nArrêt : {e}. Ce qui est déjà retenu est enregistré.')

    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    with open(out + '.json', 'w', encoding='utf-8') as f:
        json.dump(selected, f, ensure_ascii=False, indent=1)
    with open(out + '.rapport.json', 'w', encoding='utf-8') as f:
        json.dump({'projet': project, 'nom': brief.get('nom'), 'recherches': report}, f, ensure_ascii=False, indent=1)
    if selected:
        with open(out + '.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(selected[0]), delimiter=';')
            writer.writeheader()
            writer.writerows(selected)
    existing = sum(len(r['deja_dans_mps']) for r in report)
    print(f"\n{len(selected)} produits CJ retenus, {existing} produits MPS déjà proches, en "
          f"{(time.time() - started) / 60:.0f} min → {out}.json / .rapport.json")


if __name__ == '__main__':
    main()
