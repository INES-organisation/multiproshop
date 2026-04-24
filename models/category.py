from extensions import db
from datetime import datetime

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # Icône FontAwesome
    
    # Hiérarchie (self-referential)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    level = db.Column(db.Integer, default=1)  # 1=principale, 2=sous-cat, 3=sous-sous-cat
    
    # Champs CJ Dropshipping
    cj_category_id = db.Column(db.String(255), unique=True, nullable=True)  # ID CJ unique
    name_fr = db.Column(db.String(255), nullable=True)  # Nom traduit en français
    product_count = db.Column(db.Integer, default=0)  # Nombre de produits
    visible = db.Column(db.Boolean, default=True)  # Visibilité dans l'admin
    last_sync = db.Column(db.DateTime, nullable=True)  # Dernière synchronisation
    
    # Relations
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy='subquery')
    products = db.relationship('Product', backref='category', lazy=True)
    
    # Ordre d'affichage
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Category {self.name} (Level {self.level})>'
    
    @property
    def full_path(self):
        """Retourne le chemin complet de la catégorie"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name
