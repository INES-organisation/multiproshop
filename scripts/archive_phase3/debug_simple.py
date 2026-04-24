from app import create_app
from models.user import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(email='admin@multiproshop.com').first()
    if admin:
        print("Admin trouve:", admin.username)
        print("Email:", admin.email)
        print("Role:", admin.role.name if admin.role else "Aucun")
        print("Test password:", admin.check_password('admin123'))
    else:
        print("Admin non trouve")
        users = User.query.all()
        print("Utilisateurs existants:")
        for u in users:
            print(f"  - {u.username} ({u.email})")
