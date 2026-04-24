from app import app
from extensions import db
from models.user import User
from models.role import Role
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()  # S'assure que toutes les tables existent
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin')
        db.session.add(admin_role)
        db.session.commit()
        print('Rôle admin créé.')
    else:
        print('Rôle admin déjà présent.')

    admin = User.query.filter_by(email='admin@multiproshop.com').first()
    if not admin:
        admin = User(username='admin', email='admin@multiproshop.com', role_id=admin_role.id)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Administrateur créé avec succès.')
    else:
        print('Administrateur déjà présent.')
