"""
Modèle ProductReview pour les avis clients des produits
"""
from extensions import db
from datetime import datetime


class ProductReview(db.Model):
    """
    Avis clients sur les produits
    Synchronisé depuis l'API CJ Dropshipping
    """
    __tablename__ = 'product_review'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relation avec le produit
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    # Identifiant CJ (si disponible)
    cj_review_id = db.Column(db.String(255), unique=True, nullable=True)
    
    # Informations de l'avis
    author_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Note sur 5
    title = db.Column(db.String(200), nullable=True)  # Titre de l'avis
    comment = db.Column(db.Text, nullable=False)  # Commentaire
    
    # Images de l'avis (JSON array)
    images = db.Column(db.Text, nullable=True)
    
    # Métadonnées
    verified_purchase = db.Column(db.Boolean, default=False)  # Achat vérifié
    helpful_count = db.Column(db.Integer, default=0)  # Nombre de "utile"
    
    # Statut
    is_approved = db.Column(db.Boolean, default=True)  # Approuvé pour affichage
    is_featured = db.Column(db.Boolean, default=False)  # Mis en avant
    
    # Dates
    review_date = db.Column(db.DateTime, nullable=True)  # Date de l'avis original
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation inverse
    product = db.relationship('Product', backref=db.backref('reviews', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ProductReview {self.id} for Product {self.product_id} - {self.rating}/5>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        import json
        return {
            'id': self.id,
            'author_name': self.author_name,
            'rating': self.rating,
            'title': self.title,
            'comment': self.comment,
            'images': json.loads(self.images) if self.images else [],
            'verified_purchase': self.verified_purchase,
            'helpful_count': self.helpful_count,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def stars_html(self):
        """Retourne le HTML des étoiles"""
        stars = ''
        for i in range(5):
            if i < self.rating:
                stars += '<i class="fas fa-star"></i>'
            else:
                stars += '<i class="far fa-star"></i>'
        return stars
    
    def get_images_list(self):
        """Retourne la liste des images"""
        if self.images:
            try:
                import json
                return json.loads(self.images)
            except:
                return []
        return []
    
    def set_images_list(self, images_list):
        """Définit la liste des images"""
        import json
        self.images = json.dumps(images_list)
