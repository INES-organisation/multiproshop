"""Création des notifications de l'admin. Une notification ratée ne doit jamais casser l'action qui
la déclenche (paiement, synchro, webhook) : toutes les erreurs sont absorbées."""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

KINDS = {
    'order': 'Commande payée', 'cj_order_error': 'Commande CJ en échec', 'stock': 'Rupture',
    'margin': 'Marge', 'dispute': 'Litige CJ', 'cj_status': 'Suivi CJ', 'publication': 'Publication',
    'error': 'Erreur du site', 'backup': 'Sauvegarde',
}


def notify(kind, title, message=None, url=None, level='info', dedupe=None, commit=True):
    """Ajoute une notification. dedupe : clé qui évite un doublon tant que la précédente n'est pas lue."""
    from extensions import db
    from models.admin_notification import AdminNotification
    try:
        if dedupe and AdminNotification.query.filter_by(dedupe_key=dedupe, read_at=None).first():
            return None
        n = AdminNotification(kind=kind, title=title[:200], message=message, url=url, level=level, dedupe_key=dedupe)
        db.session.add(n)
        if commit:
            db.session.commit()
        if level == 'danger':
            _email_admins(n)
        return n
    except Exception as e:  # noqa: BLE001
        logger.error("Notification non enregistrée (%s) : %s", title, e)
        try:
            db.session.rollback()
        except Exception:  # noqa: BLE001
            pass
        return None


def _email_admins(n):
    """Une alerte « danger » (paiement, commande CJ, erreur au panier, sauvegarde) part aussi par e-mail
    aux administrateurs : la cloche de l'admin ne suffit pas si personne ne s'y connecte."""
    try:
        from flask import current_app
        if current_app.testing:
            return
        from models.role import Role
        from models.user import User
        from markupsafe import escape
        from utils.email import send_email
        emails = [u.email for u in User.query.join(Role).filter(Role.name == 'admin').all() if u.email]
        link = f'<p><a href="https://multiproshop.com{n.url}">Ouvrir dans l\'admin</a></p>' if n.url else ''
        for email in emails:
            send_email(subject=f'[MultiProShop] {n.title}', to=email,
                       html=f'<p><strong>{escape(n.title)}</strong></p><p>{escape(n.message or "")}</p>{link}')
    except Exception as e:  # noqa: BLE001
        logger.error("Alerte e-mail non envoyée (%s) : %s", n.title, e)


def unread_count():
    from models.admin_notification import AdminNotification
    try:
        return AdminNotification.query.filter_by(read_at=None).count()
    except Exception:  # noqa: BLE001
        return 0


def check_margin(product, commit=True):
    """Alerte si un produit en ligne a une variante active vendue à perte (après un changement de coût CJ)"""
    if not product.is_active:
        return
    mi = product.margin_info()
    if mi and mi['margin'][0] <= 0:
        notify('margin', f'Marge négative : {product.name}',
               f"Une variante active est vendue {mi['margin'][0]:.2f} € sous son coût CJ. Ajustez le prix ou désactivez-la.",
               url=f'/admin/products/edit/{product.id}', level='danger', dedupe=f'margin:{product.id}', commit=commit)


def mark_read(ids=None):
    from extensions import db
    from models.admin_notification import AdminNotification
    q = AdminNotification.query.filter_by(read_at=None)
    if ids:
        q = q.filter(AdminNotification.id.in_(ids))
    q.update({'read_at': datetime.utcnow()}, synchronize_session=False)
    db.session.commit()
