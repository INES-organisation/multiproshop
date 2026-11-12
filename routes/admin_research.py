"""
Admin MPS › Recherche de produits (/admin/recherche-produits) : trouver les meilleurs produits pour un
site, par critères, et les comparer à la demande sur le web.

- Une veille = un site, des recherches (titre en français, mots du web, recherche CJ en anglais, mots
  obligatoires) et des critères CJ (prix d'achat, photos, poids, stock, stock en France). Elle se crée à
  la main, depuis la fiche d'une vitrine (scripts/vitrines/<code>.json), ou avec l'aide de Claude.
- « Lancer » fait un passage en tâche de fond ; les veilles actives repassent chaque lundi.
- Chaque résultat s'importe en brouillon dans le site (CJ), part au sourcing CJ (web) ou s'écarte.
Le calcul est dans services/product_research.py.
"""
import json

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensions import db
from routes.admin import admin_bp, admin_required

FILTERS = ('dispo', 'a_sourcer', 'info', 'importe', 'sourcing', 'ecarte')


def _form_criteria(f):
    from models.product_research import DEFAULT_CRITERIA
    out = {}
    for k, default in DEFAULT_CRITERIA.items():
        if isinstance(default, bool):
            out[k] = bool(f.get(k))
            continue
        raw = (f.get(k) or '').replace(',', '.').strip()
        try:
            value = float(raw) if raw else default
        except ValueError:
            value = default
        out[k] = int(value) if isinstance(default, int) else value
    out['per_query'] = max(1, min(out['per_query'], 10))
    out['max_examined'] = max(out['per_query'], min(out['max_examined'], 20))  # 1 fiche CJ + stocks par examen
    out['candidates'] = max(10, min(out['candidates'], 100))
    return out


def _storefronts():
    from models.storefront import Storefront
    return Storefront.query.order_by(Storefront.kind, Storefront.name).all()


def _queries(f):
    from services.product_research import parse_lines, suggest_queries
    queries = parse_lines(f.get('lines'))
    if f.get('claude'):
        todo = [q['fr'] for q in queries if not q['q']]
        if todo:
            try:
                done = {q['fr']: q for q in suggest_queries(todo)}
                queries = [done.get(q['fr'], q) if not q['q'] else q for q in queries]
                flash(f'Claude a complété {len(done)} recherche(s) : relisez-les.', 'success')
            except Exception as e:  # noqa: BLE001
                flash(f'Claude indisponible ({e}) : complétez la recherche CJ à la main.', 'error')
    return queries


@admin_bp.route('/recherche-produits', methods=['GET', 'POST'])
@login_required
@admin_required
def research():
    from models.product_research import DEFAULT_CRITERIA, ResearchResult, ResearchWatch
    from services.dataforseo import configured
    from services.product_research import queries_from_brief
    if request.method == 'POST':
        f = request.form
        storefront = (f.get('storefront') or '').strip() or None
        queries = queries_from_brief(storefront) if f.get('from_brief') and storefront else []
        queries = queries or _queries(f)
        name = (f.get('name') or '').strip()[:80]
        if not name or not queries:
            flash('Un nom et au moins une recherche (une par ligne, ou la fiche de la vitrine).', 'error')
            return redirect(url_for('admin.research'))
        watch = ResearchWatch(name=name, storefront=storefront, queries=json.dumps(queries, ensure_ascii=False),
                              criteria=json.dumps(_form_criteria(f)), web=bool(f.get('web')), active=bool(f.get('active')))
        db.session.add(watch)
        db.session.commit()
        flash(f'Veille « {name} » créée avec {len(queries)} recherche(s). Relisez-la, puis « Lancer ».', 'success')
        return redirect(url_for('admin.research_watch', watch_id=watch.id))
    watches = ResearchWatch.query.order_by(ResearchWatch.created_at.desc()).all()
    counts = dict(db.session.query(ResearchResult.watch_id, db.func.count()).filter(
        ResearchResult.verdict.in_(['dispo', 'a_sourcer'])).group_by(ResearchResult.watch_id).all())
    return render_template('admin/research.html', watches=watches, counts=counts, storefronts=_storefronts(),
                           criteria=DEFAULT_CRITERIA, web_ready=configured())


@admin_bp.route('/recherche-produits/<int:watch_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def research_watch(watch_id):
    from models.product_research import VERDICTS, ResearchResult, ResearchWatch
    from services.dataforseo import configured
    from services.product_research import format_lines
    watch = db.session.get(ResearchWatch, watch_id) or _404()
    if request.method == 'POST':
        f = request.form
        if f.get('action') == 'delete':
            db.session.delete(watch)
            db.session.commit()
            flash('Veille supprimée (les produits importés restent dans MPS).', 'success')
            return redirect(url_for('admin.research'))
        queries = _queries(f)
        if not queries:
            flash('Au moins une recherche.', 'error')
            return redirect(url_for('admin.research_watch', watch_id=watch.id))
        watch.name = (f.get('name') or watch.name).strip()[:80]
        watch.storefront = (f.get('storefront') or '').strip() or None
        watch.queries = json.dumps(queries, ensure_ascii=False)
        watch.criteria = json.dumps(_form_criteria(f))
        watch.web, watch.active = bool(f.get('web')), bool(f.get('active'))
        db.session.commit()
        flash('Veille enregistrée.', 'success')
        return redirect(url_for('admin.research_watch', watch_id=watch.id))
    show = request.args.get('voir', 'a_traiter')
    results = watch.results
    if show in FILTERS:
        results = results.filter(ResearchResult.verdict == show)
    elif show == 'a_traiter':
        results = results.filter(ResearchResult.verdict.in_(['dispo', 'a_sourcer']))
    results = results.order_by(ResearchResult.search, ResearchResult.kind, ResearchResult.listed.desc(),
                               ResearchResult.bought_month.desc(), ResearchResult.votes.desc()).all()
    groups = {}
    for r in results:
        groups.setdefault(r.search, []).append(r)
    tally = dict(db.session.query(ResearchResult.verdict, db.func.count()).filter(
        ResearchResult.watch_id == watch.id).group_by(ResearchResult.verdict).all())
    tabs = ([('a_traiter', 'À traiter', tally.get('dispo', 0) + tally.get('a_sourcer', 0))]
            + [(k, VERDICTS[k], tally.get(k, 0)) for k in FILTERS] + [('tout', 'Tout', sum(tally.values()))])
    return render_template('admin/research_watch.html', watch=watch, groups=groups, show=show, tabs=tabs,
                           storefronts=_storefronts(),
                           lines=format_lines(watch.get_queries()), criteria=watch.get_criteria(),
                           web_ready=configured())


def _404():
    from flask import abort
    abort(404)


@admin_bp.route('/recherche-produits/<int:watch_id>/lancer', methods=['POST'])
@login_required
@admin_required
def research_run(watch_id):
    from models.product_research import ResearchWatch
    watch = db.session.get(ResearchWatch, watch_id) or _404()
    if current_app.config.get('TESTING'):
        from services.product_research import run_watch
        flash(f'Passage terminé : {run_watch(watch)}', 'success')
    else:
        try:
            from tasks.research_tasks import run_watch as task
            task.delay(watch.id)
            n = len(watch.get_queries())
            flash(f'Recherche lancée en tâche de fond ({n} recherche(s), quelques minutes : environ 15 s par '
                  'recherche côté CJ, plus le web). Rechargez la page pour voir les résultats.', 'success')
        except Exception as e:  # noqa: BLE001 — file Celery indisponible
            flash(f'Impossible de lancer la tâche ({e}).', 'error')
    return redirect(url_for('admin.research_watch', watch_id=watch.id))


@admin_bp.route('/recherche-produits/resultat/<int:result_id>', methods=['POST'])
@login_required
@admin_required
def research_result(result_id):
    from models.product_research import ResearchResult
    from services.product_research import import_result, send_to_sourcing
    r = db.session.get(ResearchResult, result_id) or _404()
    action = request.form.get('action')
    back = redirect(url_for('admin.research_watch', watch_id=r.watch_id, voir=request.form.get('voir') or None))
    try:
        if action == 'import':
            product = import_result(r)
            where = f' dans {r.watch.storefront}' if r.watch.storefront else ''
            flash(f'« {product.name} » est dans MPS{where} (#{product.id}), en brouillon s\'il est nouveau : '
                  'activez-le depuis Boutiques et vitrines (contrôles CJ, marge, fiche en français).', 'success')
        elif action == 'sourcing':
            send_to_sourcing(r)
            flash('Demande envoyée à CJ (Sourcing CJ) : réponse en général sous 1 à 3 jours.', 'success')
        elif action == 'ecarter':
            r.verdict = 'ecarte'
            db.session.commit()
        elif action == 'restore':
            r.verdict = 'dispo' if r.kind == 'cj' else 'a_sourcer'
            db.session.commit()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        flash(f'Impossible : {e}', 'error')
    return back
