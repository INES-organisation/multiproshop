"""
Recherche de produits : un passage de veille (admin MPS › Recherche de produits).

Pour chaque recherche de la veille :
  1. CJ : les produits les plus listés par les boutiques CJ pour ces mots, dont le nom contient les mots
     obligatoires, puis leur fiche (photos, poids, prix d'achat, stock) avec les critères de la veille,
     et le prix de vente de la grille (scripts/select_vitrine_products.py, mêmes règles) ;
  2. le web, si DataForSEO est branché : Google Trends (intérêt sur 12 mois), Amazon.fr et Google
     Shopping (prix, avis, « acheté le mois dernier ») ;
  3. un verdict par produit : « dispo chez CJ » (avec le prix médian du web pour comparer), « à sourcer »
     (demandé sur le web, rien de convenable chez CJ), « repère du marché » sinon.
Les verdicts posés à la main (importé, envoyé au sourcing, écarté) ne sont jamais écrasés.
Rien n'est importé ici : l'admin importe en brouillon, produit par produit.
"""
import json
import logging
import statistics
from datetime import datetime
from types import SimpleNamespace

from extensions import db
from models.product_research import ResearchResult, ResearchWatch

logger = logging.getLogger(__name__)

USD_EUR = 0.92
WEB_PER_QUERY = 3  # produits web gardés par source et par recherche
MANUAL = {'importe', 'sourcing', 'ecarte'}


def _cj():
    from routes.admin import _cj_api
    from services.api_providers import cj_dropshipping_optimized as cj
    cj._memory_cache['min_interval'] = max(cj._memory_cache['min_interval'], 1.1)  # 1 requête/s chez CJ
    return _cj_api()


def _web():
    from services.dataforseo import DataForSEO, configured
    return DataForSEO() if configured() else None


def _upsert(watch, query, kind, ref, **fields):
    r = ResearchResult.query.filter_by(watch_id=watch.id, kind=kind, ref=str(ref)[:80]).first()
    if r is None:
        r = ResearchResult(watch_id=watch.id, kind=kind, ref=str(ref)[:80], verdict='info')
        db.session.add(r)
    verdict = fields.pop('verdict', None)
    r.search = query[:120]
    for k, v in fields.items():
        if k in ('title', 'image', 'url'):
            v = (v or '')[:{'title': 300, 'image': 500, 'url': 500}[k]] or None
        if k == 'note':
            v = (v or '')[:200] or None
        setattr(r, k, v)
    if verdict and r.verdict not in MANUAL:
        r.verdict = verdict
    r.updated_at = datetime.utcnow()
    return r


def _web_rank(item):
    return (item.get('bought_month') or 0, item.get('votes') or 0)


def run_watch(watch, cj_api=None, web=None):
    """Un passage complet ; renvoie la note du passage (aussi gardée sur la veille)"""
    from models.product import Product
    from scripts.select_cj_products import QuotaExhausted
    from scripts.select_vitrine_products import examine, search_cj
    from services.publication import grid_price

    c = watch.get_criteria()
    args = SimpleNamespace(candidates=int(c['candidates']), min_cost=float(c['min_cost']),
                           max_cost=float(c['max_cost']), min_images=int(c['min_images']),
                           max_weight=float(c['max_weight']), min_stock=int(c['min_stock']), usd_eur=USD_EUR)
    queries = watch.get_queries()
    api = cj_api or _cj()
    notes, counts, web_error = [], {'dispo': 0, 'a_sourcer': 0}, None
    if watch.web and web is None:
        try:
            web = _web()
        except Exception as e:  # noqa: BLE001
            web_error = str(e)
    trends = {}
    if web is not None:
        try:
            trends = web.trends([q.get('web') or q['fr'] for q in queries])
        except Exception as e:  # noqa: BLE001 — le web en panne n'empêche pas la recherche CJ
            web_error = str(e)

    seen_pids = set()
    try:
        for q in queries:
            label, web_kw = q['fr'], q.get('web') or q['fr']
            trend = trends.get(web_kw)
            web_items = []
            if web is not None and not web_error:
                for source in (web.amazon, web.shopping):
                    try:
                        web_items += source(web_kw)
                    except Exception as e:  # noqa: BLE001
                        web_error = str(e)
                        break
            prices = [i['price'] for i in web_items if i.get('price')]
            market = round(statistics.median(prices), 2) if prices else None

            kept, rejected = 0, {}
            if q.get('q'):
                must = q.get('must') or q['q'].split()[:2]
                for p in search_cj(api, q['q'], args, must)[:int(c['max_examined'])]:
                    if kept >= int(c['per_query']):
                        break
                    if p['pid'] in seen_pids:
                        continue
                    found, reason = examine(api, p, args)
                    if found and c.get('france_only') and not found['stock']['france']:
                        found, reason = None, 'pas en France'
                    if not found:
                        rejected[reason] = rejected.get(reason, 0) + 1
                        continue
                    seen_pids.add(p['pid'])
                    kept += 1
                    d = found['d']
                    price = grid_price(found['cost_eur']) or found['price']
                    existing = Product.query.filter_by(cj_pid=p['pid']).first()
                    note = []
                    if existing:
                        note.append(f'déjà dans MPS (#{existing.id})')
                    if market:
                        gap = round((price / market - 1) * 100)
                        note.append(f'web {market:.2f} € ({gap:+d} %)' if gap else f'web {market:.2f} €')
                    if found['stock']['france']:
                        note.append('stock en France')
                    item = {'projet': watch.storefront, 'famille': label, 'groupe': label, 'recherche': q['q'],
                            'categorie_cj': d.get('category_name') or '', 'pid': p['pid'],
                            'nom_en': d.get('name_en') or p['name_en'], 'nom_fr': label,
                            'image': d.get('image') or p['image'], 'stock': found['stock']['total'],
                            'cout_usd': found['cost_usd'], 'cout_eur': found['cost_eur'], 'prix_vente_eur': price,
                            'photos': len(d.get('images') or []), 'variantes': len(d.get('variants') or []),
                            'poids_g': round(found['weight'])}
                    _upsert(watch, label, 'cj', p['pid'], title=item['nom_en'], image=item['image'],
                            url=f"https://cjdropshipping.com/product/-p-{p['pid']}.html", price_eur=price,
                            cost_eur=found['cost_eur'], listed=p['listed'], market_price=market, trend=trend,
                            verdict='dispo', note=', '.join(note), data=json.dumps(item, ensure_ascii=False),
                            product_id=existing.id if existing else None)
                    counts['dispo'] += 1

            for kind in ('amazon', 'shopping'):
                best = sorted([i for i in web_items if i['kind'] == kind and (i.get('rating') or 5) >= 4],
                              key=_web_rank, reverse=True)[:WEB_PER_QUERY]
                for i in best:
                    note = 'best-seller Amazon' if i.get('best_seller') else (i.get('seller') or '')
                    _upsert(watch, label, kind, i['ref'], title=i['title'], image=i.get('image'), url=i.get('url'),
                            price_eur=i.get('price'), rating=i.get('rating'), votes=i.get('votes'),
                            bought_month=i.get('bought_month'), market_price=market, trend=trend,
                            verdict='info' if kept else 'a_sourcer', note=note)
                    counts['a_sourcer'] += 0 if kept else 1
            if rejected:
                notes.append(f"{label[:30]} : écartés {', '.join(f'{k} {v}' for k, v in rejected.items())}")
            db.session.commit()
    except QuotaExhausted as e:
        db.session.rollback()
        notes.insert(0, f'arrêt : {e}')

    head = f"{counts['dispo']} dispo chez CJ, {counts['a_sourcer']} à sourcer"
    if web is None and not web_error:
        head += ' ; web non comparé (' + ('DataForSEO non branché' if watch.web else 'désactivé') + ')'
    elif web_error:
        head += f' ; web : {web_error}'
    elif getattr(web, 'cost', 0):
        head += f' ; DataForSEO {web.cost:.3f} $'
    watch.last_run_at = datetime.utcnow()
    watch.last_run_note = ' | '.join([head] + notes)[:500]
    db.session.commit()
    return watch.last_run_note


def run_active():
    """Passage hebdomadaire de toutes les veilles actives"""
    out = {}
    for watch in ResearchWatch.query.filter_by(active=True).order_by(ResearchWatch.id).all():
        try:
            out[watch.id] = run_watch(watch)
        except Exception as e:  # noqa: BLE001 — une veille en échec ne bloque pas les autres
            db.session.rollback()
            logger.exception('[Recherche] veille %s en échec', watch.id)
            watch.last_run_at, watch.last_run_note = datetime.utcnow(), f'échec : {e}'[:500]
            db.session.commit()
            out[watch.id] = str(e)
    return out


def import_result(result):
    """Importe un produit CJ « dispo » en brouillon, rattaché au site de la veille. Un produit déjà en ligne
    (ou déjà publié une fois) dans MPS reçoit seulement le site : sa fiche n'est pas réécrite."""
    from models.product import Product
    from routes.admin import _cj_details
    from scripts.import_selection import add_project, publish
    if result.kind != 'cj':
        raise ValueError('seuls les produits CJ s\'importent')
    item = result.get_data()
    project = result.watch.storefront
    existing = Product.query.filter_by(cj_pid=result.ref).first()
    if existing and (existing.is_active or existing.published_at is not None):
        if project:
            add_project(existing, project)
        product = existing
    else:
        details = _cj_details(result.ref)
        if not details or not item:
            raise ValueError('fiche CJ indisponible')
        product = publish(item, details, USD_EUR, project=project, draft=True)
    result.verdict, result.product_id = 'importe', product.id
    db.session.commit()
    return product


def send_to_sourcing(result):
    """Demande à CJ de trouver un produit vu sur le web (Amazon, Google Shopping)"""
    from models.cj_sourcing import CjSourcing
    from routes.admin import _cj_api
    if not (result.image or '').startswith(('http://', 'https://')):
        raise ValueError('il faut une image pour demander un sourcing à CJ')
    remark = f'Recherche MPS « {result.search} »' + (f', prix constaté {result.price_eur:.2f} €' if result.price_eur else '')
    res = _cj_api().create_sourcing(result.title[:200], result.image[:200], (result.url or '')[:200] or None,
                                    None, remark)
    if 'error' in res:
        raise ValueError(f"CJ a refusé la demande : {res['error']}")
    db.session.add(CjSourcing(cj_sourcing_id=res['id'], product_name=result.title[:200],
                              product_url=(result.url or '')[:200] or None, product_image=result.image[:200],
                              remark=remark[:200]))
    result.verdict = 'sourcing'
    db.session.commit()
    return res['id']


SUGGEST_SYSTEM = (
    "Tu prépares des recherches de produits pour une boutique en ligne française qui se fournit chez CJ "
    "Dropshipping. Pour chaque produit décrit en français, donne : web = 2 à 4 mots qu'un client français "
    "taperait sur Amazon ou Google ; q = la recherche en anglais pour le catalogue CJ (2 à 5 mots) ; must = 1 "
    "à 3 groupes de mots anglais dont le nom CJ doit contenir chacun au moins un, variantes séparées par "
    "« | » (ex. \"lavalier|lapel\"), en minuscules. Réponds seulement en JSON : une liste d'objets "
    "{\"fr\", \"web\", \"q\", \"must\"} dans l'ordre reçu.")


def suggest_queries(titles):
    """Claude (via INES) complète les recherches à partir de titres en français"""
    from services.ai_copy import _generate
    text = _generate(SUGGEST_SYSTEM, '\n'.join(f'- {t}' for t in titles), max_tokens=1500)
    start, end = text.find('['), text.rfind(']')
    try:
        data = json.loads(text[start:end + 1])
    except ValueError as e:
        raise ValueError('réponse de Claude illisible') from e
    out = []
    for t, d in zip(titles, data):
        if isinstance(d, dict):
            must = [str(m).lower()[:40] for m in (d.get('must') or []) if str(m).strip()][:3]
            out.append({'fr': t, 'web': str(d.get('web') or t)[:80], 'q': str(d.get('q') or '')[:80], 'must': must})
    return out


def queries_from_brief(code):
    """Recherches d'une fiche de vitrine (scripts/vitrines/<code>.json)"""
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts', 'vitrines',
                        f'{code}.json')
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        brief = json.load(f)
    return [{'fr': q['fr'], 'web': q.get('web') or q['fr'], 'q': q['q'], 'must': q.get('must') or []}
            for g in brief.get('groups', []) for q in g.get('queries', [])]


def parse_lines(text):
    """« Titre en français | recherche web | recherche CJ (anglais) | mot1|variante, mot2 » par ligne ;
    seul le titre est obligatoire (Claude peut compléter le reste)"""
    out = []
    for line in (text or '').splitlines():
        parts = [p.strip() for p in line.split(' | ')]
        if not parts or not parts[0]:
            continue
        must = [m.strip().lower() for m in (parts[3] if len(parts) > 3 else '').split(',') if m.strip()]
        out.append({'fr': parts[0][:120], 'web': (parts[1] if len(parts) > 1 else '')[:80] or parts[0][:80],
                    'q': (parts[2] if len(parts) > 2 else '')[:80], 'must': must[:3]})
    return out


def format_lines(queries):
    return '\n'.join(' | '.join([q['fr'], q.get('web') or q['fr'], q.get('q') or '', ', '.join(q.get('must') or [])])
                     for q in queries)
