"""
Admin MPS › Boutiques et vitrines (/admin/vitrines) : créer, régler et publier les sites qui vendent
le catalogue MPS (Sérénis, ALIAS, DIGITA, et les suivants).

- La liste montre pour chacun son type, son état, ses produits (en ligne et en brouillon), ses ventes
  des 30 derniers jours et ce qui manque pour qu'il soit branché (jeton, produits, INES).
- La fiche règle le site (nom, adresse, slogan, couleur, produit mis en avant, lots, délai, seuil de
  livraison offerte) et gère ses produits : ajouter, retirer, publier les brouillons d'un coup.
Les produits restent ceux du catalogue MPS : une vitrine n'en est qu'une sélection (champ « Vitrines »).
"""
import json
import re
from datetime import datetime, timedelta

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensions import db
from routes.admin import admin_bp, admin_required

SLUG = re.compile(r'^[a-z0-9-]{2,30}$')
COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')
DELIVERY = re.compile(r'^\d{1,2}-\d{1,2}$')
RESERVED = {'ines', 'multiproshop', 'mps'}  # jetons et chiffres déjà pris par INES et MPS


def _in(slug):
    from sqlalchemy import literal
    from models.product import Product
    return (literal(',') + Product.projects + literal(',')).like(f'%,{slug},%')


def _summary(sf):
    from models.order import Order
    from models.product import Product
    attached = Product.query.filter(_in(sf.slug), Product.is_active.is_(True))
    online = attached.filter(Product.published.is_(True)).count()
    drafts = attached.filter(Product.published.isnot(True)).count()
    month = datetime.utcnow() - timedelta(days=30)
    orders = Order.query.filter(Order.admin_notes == f'Commande passée sur {sf.order_label}',
                                Order.payment_status == 'paid', Order.paid_at >= month).all()
    return {'online': online, 'drafts': drafts, 'orders_30d': len(orders),
            'revenue_30d': round(sum(o.total_price or 0 for o in orders), 2)}


def _threshold(sf):
    from routes.partner_api import _free_shipping_threshold
    return _free_shipping_threshold(sf.slug)


def checklist(sf, summary):
    """Étapes de mise en ligne : (fait ?, intitulé, comment faire). None = à vérifier à la main."""
    key, prefix = sf.env_key, sf.ines_prefix or f'{sf.env_key}_'
    steps = [
        (bool(summary['online']), 'Au moins un produit en ligne',
         'Ajoutez des produits ci-dessous, puis « Publier les brouillons ».'),
        (sf.token_configured, f'Jeton de la {sf.kind_label.lower()} : PARTNER_TOKEN_{key}',
         f'Sur le VPS : python3 -c "import secrets;print(secrets.token_urlsafe(32))", à mettre dans '
         f'/opt/multiproshop/deploy/.env (PARTNER_TOKEN_{key}=…), puis deploy.sh. '
         'Le même jeton va dans le site lui-même (voir l\'étape suivante).'),
    ]
    if sf.kind == 'boutique':
        steps += [
            (None, 'Service de la boutique sur le VPS',
             f'Copier le bloc serenis-web de deploy/docker-compose.yml en {sf.slug}-web, avec '
             f'VITRINE_PROJECT={sf.slug}, VITRINE_TOKEN=${{PARTNER_TOKEN_{key}}} et '
             f'SECRET_KEY=${{{key}_SECRET_KEY}} (nouvelle valeur dans deploy/.env). Les autres réglages '
             'viennent de cette fiche.'),
            (None, 'Adresse, nginx et certificat',
             'Enregistrement DNS A vers le VPS, bloc server dans le nginx.conf d\'INES (sur le modèle de '
             'serenis.multiproshop.com), puis certbot --webroot -w /opt/ines/certbot-webroot.'),
        ]
    else:
        steps += [
            (None, 'Le site appelle le catalogue de sa vitrine',
             f'Le site lit /api/partner/catalogue?project={sf.slug} (et non tout le catalogue) et envoie le '
             'jeton en « Authorization: Bearer » pour le port et les commandes. Jeton rangé dans INES › '
             f'/admin/integrations : {prefix}MPS_PARTNER_TOKEN.'),
        ]
    steps += [
        (sf.token_configured, 'Chiffres dans INES (/ecommerce › Boutiques connectées)',
         'Automatique dès que le jeton existe : /api/partner/stats compte les ventes de ce site à part, '
         f'sous le nom « {sf.slug} ».'),
        (None, 'Paiement, e-mails et remboursements',
         'Rien à faire : MPS encaisse avec le Stripe d\'INES, envoie les e-mails et reçoit les '
         'remboursements et contestations (POST /api/partner/payment-events).'),
    ]
    return steps


@admin_bp.route('/vitrines')
@login_required
@admin_required
def storefronts():
    from models.storefront import Storefront, ensure_defaults
    ensure_defaults()
    rows = []
    for sf in Storefront.query.order_by(Storefront.kind, Storefront.name).all():
        summary = _summary(sf)
        steps = checklist(sf, summary)
        rows.append({'sf': sf, 's': summary, 'threshold': _threshold(sf),
                     'todo': sum(1 for done, *_ in steps if done is False)})
    return render_template('admin/storefronts.html', rows=rows)


@admin_bp.route('/vitrines/nouvelle', methods=['GET', 'POST'])
@login_required
@admin_required
def storefront_new():
    from models.storefront import KINDS, Storefront
    if request.method == 'POST':
        f = request.form
        slug = (f.get('slug') or '').strip().lower()
        name = (f.get('name') or '').strip()[:80]
        kind = f.get('kind') if f.get('kind') in KINDS else 'vitrine'
        url = (f.get('url') or '').strip().rstrip('/')[:200]
        if not SLUG.match(slug) or slug in RESERVED:
            flash('Code : 2 à 30 caractères, minuscules, chiffres et tirets (ines, mps et multiproshop sont réservés).', 'error')
        elif Storefront.query.filter_by(slug=slug).first():
            flash(f'Le code « {slug} » existe déjà.', 'error')
        elif not name or not url.startswith('https://'):
            flash("Nom et adresse (https://…) obligatoires.", 'error')
        else:
            label = re.sub(r'^https://', '', url)[:80]
            sf = Storefront(slug=slug, name=name, kind=kind, url=url, status='preparation', order_label=label,
                            ines_prefix=slug.upper().replace('-', '_') + '_', delivery_days='12-20')
            db.session.add(sf)
            db.session.commit()
            flash(f'{sf.kind_label} « {name} » créée, en préparation. Ajoutez ses produits, puis suivez les étapes de mise en ligne.', 'success')
            return redirect(url_for('admin.storefront_edit', slug=slug))
    return render_template('admin/storefront_new.html', kinds=KINDS, form=request.form)


@admin_bp.route('/vitrines/<slug>', methods=['GET', 'POST'])
@login_required
@admin_required
def storefront_edit(slug):
    from models.product import Product
    from models.storefront import STATUSES, Storefront
    sf = Storefront.query.filter_by(slug=slug).first_or_404()
    if request.method == 'POST':
        f = request.form
        errors = []
        sf.name = (f.get('name') or sf.name).strip()[:80]
        url = (f.get('url') or '').strip().rstrip('/')
        if url and not url.startswith('https://'):
            errors.append("L'adresse doit commencer par https://")
        else:
            sf.url = url[:200] or None
        if f.get('status') in STATUSES:
            sf.status = f['status']
        sf.tagline = (f.get('tagline') or '').strip()[:200] or None
        color = (f.get('color') or '').strip()
        if color and not COLOR.match(color):
            errors.append('Couleur au format #rrggbb')
        else:
            sf.color = color or None
        sf.hero_product_id = f.get('hero_product_id', type=int) or None
        delivery = (f.get('delivery_days') or '').replace(' ', '')
        if delivery and not DELIVERY.match(delivery):
            errors.append('Délai au format 12-20')
        else:
            sf.delivery_days = delivery or None
        raw = (f.get('free_shipping_threshold') or '').replace(',', '.').strip()
        try:
            sf.free_shipping_threshold = round(float(raw), 2) if raw else None
        except ValueError:
            errors.append('Seuil de livraison offerte : un montant en euros, ou vide')
        lots = (f.get('lots') or '').strip()
        if lots:
            try:
                parsed = json.loads(lots)
                assert isinstance(parsed, list) and all(isinstance(x, dict) and isinstance(x.get('ids'), list) for x in parsed)
                sf.lots = json.dumps(parsed, ensure_ascii=False)
            except (ValueError, AssertionError):
                errors.append('Lots : une liste JSON [{"name": …, "text": …, "ids": [id, …]}]')
        else:
            sf.lots = None
        sf.ines_prefix = (f.get('ines_prefix') or '').strip().upper()[:30] or None
        sf.notes = (f.get('notes') or '').strip() or None
        if errors:
            db.session.rollback()
            for e in errors:
                flash(e, 'error')
        else:
            db.session.commit()
            flash('Réglages enregistrés. Les sites les relisent sous 5 minutes.', 'success')
        return redirect(url_for('admin.storefront_edit', slug=slug))

    products = Product.query.filter(_in(sf.slug)).order_by(Product.published.desc(), Product.name).all()
    q = (request.args.get('q') or '').strip()[:100]
    found = []
    if q:
        query = Product.query.filter(Product.is_active.is_(True), ~_in(sf.slug) | Product.projects.is_(None))
        query = query.filter(Product.id == int(q)) if q.isdigit() else query.filter(Product.name.ilike(f'%{q}%'))
        found = query.order_by(Product.published.desc(), Product.name).limit(40).all()
    summary = _summary(sf)
    return render_template('admin/storefront_edit.html', sf=sf, statuses=STATUSES, products=products, q=q,
                           found=found, s=summary, steps=checklist(sf, summary), threshold=_threshold(sf),
                           lots=json.dumps(sf.get_lots(), ensure_ascii=False, indent=1) if sf.lots else '')


@admin_bp.route('/vitrines/<slug>/produits', methods=['POST'])
@login_required
@admin_required
def storefront_products(slug):
    """add : rattacher les produits cochés (ou les ids saisis) ; remove : les retirer de la vitrine ;
    publish : publier les produits cochés, ou tous les brouillons si rien n'est coché ; unpublish."""
    from models.product import Product
    from models.storefront import Storefront
    from routes.api_products import clean_projects
    sf = Storefront.query.filter_by(slug=slug).first_or_404()
    action = request.form.get('action')
    ids = {int(i) for i in request.form.getlist('ids') if i.isdigit()}
    ids |= {int(i) for i in re.findall(r'\d+', request.form.get('id_list', ''))}
    back = redirect(url_for('admin.storefront_edit', slug=slug))
    if action == 'publish' and not ids:
        targets = Product.query.filter(_in(sf.slug), Product.is_active.is_(True), Product.published.isnot(True)).all()
    elif ids:
        targets = Product.query.filter(Product.id.in_(ids)).all()
    else:
        flash('Cochez au moins un produit.', 'error')
        return back
    now = datetime.utcnow()
    for p in targets:
        projects = set((p.projects or '').split(',')) - {''}
        if action == 'add':
            p.projects = clean_projects(','.join(projects | {sf.slug})) or None
        elif action == 'remove':
            p.projects = clean_projects(','.join(projects - {sf.slug})) or None
        elif action == 'publish':
            p.is_active, p.published = True, True
            p.published_at = p.published_at or now
        elif action == 'unpublish':
            p.published = False
        else:
            flash('Action inconnue.', 'error')
            return back
    db.session.commit()
    done = {'add': 'ajouté(s) à', 'remove': 'retiré(s) de', 'publish': 'publié(s) sur',
            'unpublish': 'dépublié(s) (MPS et toutes les vitrines) :'}[action]
    flash(f'{len(targets)} produit(s) {done} {sf.name}.', 'success')
    return back
