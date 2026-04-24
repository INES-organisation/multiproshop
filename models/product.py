from extensions import db
from datetime import datetime
from .video import Video
import json

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations de base
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=True)  # Référence unique
    description = db.Column(db.Text, nullable=True)
    short_description = db.Column(db.String(500), nullable=True)
    
    # Prix et stock
    price = db.Column(db.Float, nullable=False)
    compare_price = db.Column(db.Float, nullable=True)  # Prix barré
    cost_price = db.Column(db.Float, nullable=True)  # Prix de revient
    stock = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)  # Alerte stock bas
    
    # Images (stockage JSON des URLs)
    image_url = db.Column(db.String(255), nullable=True)  # Image principale
    images = db.Column(db.Text, nullable=True)  # JSON array des images supplémentaires
    
    # Catégorisation
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.Text, nullable=True)  # JSON array des tags
    
    # Caractéristiques physiques
    weight = db.Column(db.Float, nullable=True)  # Poids en kg
    length = db.Column(db.Float, nullable=True)  # Longueur en cm
    width = db.Column(db.Float, nullable=True)   # Largeur en cm
    height = db.Column(db.Float, nullable=True)  # Hauteur en cm
    
    # Caractéristiques techniques (JSON)
    specifications = db.Column(db.Text, nullable=True)  # JSON des specs
    
    # SEO
    meta_title = db.Column(db.String(200), nullable=True)
    meta_description = db.Column(db.String(500), nullable=True)
    meta_keywords = db.Column(db.String(500), nullable=True)
    
    # Statut et visibilité
    is_active = db.Column(db.Boolean, default=True)  # Publié/Brouillon
    is_featured = db.Column(db.Boolean, default=False)  # Produit mis en avant
    is_new = db.Column(db.Boolean, default=False)  # Nouveau produit
    is_on_sale = db.Column(db.Boolean, default=False)  # En promotion
    
    # Statistiques
    views_count = db.Column(db.Integer, default=0)  # Nombre de vues
    sales_count = db.Column(db.Integer, default=0)  # Nombre de ventes
    rating_average = db.Column(db.Float, default=0.0)  # Note moyenne
    rating_count = db.Column(db.Integer, default=0)  # Nombre d'avis
    
    # Champs CJ Dropshipping
    cj_pid = db.Column(db.String(255), unique=True, nullable=True)  # Product ID CJ
    suggested_price = db.Column(db.Float, nullable=True)  # Prix suggéré par CJ
    product_weight = db.Column(db.String(50), nullable=True)  # Poids produit CJ
    material = db.Column(db.String(255), nullable=True)  # Matériau
    published = db.Column(db.Boolean, default=False)  # Publié sur le magasin
    synced_at = db.Column(db.DateTime, nullable=True)  # Dernière synchronisation CJ
    cj_raw_data = db.Column(db.Text, nullable=True)  # Données brutes CJ (JSON) pour audit
    cj_last_sync = db.Column(db.DateTime, nullable=True)  # Dernière sync complète CJ
    stock_checked = db.Column(db.Boolean, default=False)  # True si stock vérifié par API CJ
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    
    # Relations marketplace
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    marketplace_id = db.Column(db.Integer, db.ForeignKey('marketplace.id'))
    
    # Relations
    videos = db.relationship('Video', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    # Méthodes utiles
    def get_images_list(self):
        """Retourne la liste des images supplémentaires"""
        if self.images:
            try:
                return json.loads(self.images)
            except:
                return []
        return []
    
    def set_images_list(self, images_list):
        """Définit la liste des images supplémentaires"""
        self.images = json.dumps(images_list)
    
    def get_tags_list(self):
        """Retourne la liste des tags"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []
    
    def set_tags_list(self, tags_list):
        """Définit la liste des tags"""
        self.tags = json.dumps(tags_list)
    
    def get_specifications_dict(self):
        """Retourne le dictionnaire des spécifications"""
        if self.specifications:
            try:
                return json.loads(self.specifications)
            except:
                return {}
        return {}
    
    def get_specifications(self):
        """Alias pour get_specifications_dict() - compatibilité template"""
        return self.get_specifications_dict()
    
    def set_specifications_dict(self, specs_dict):
        """Définit le dictionnaire des spécifications"""
        self.specifications = json.dumps(specs_dict)
    
    def get_discount_percentage(self):
        """Calcule le pourcentage de réduction"""
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0
    
    def is_in_stock(self):
        """Vérifie si le produit est en stock"""
        return self.stock > 0
    
    def is_low_stock(self):
        """Vérifie si le stock est bas"""
        return 0 < self.stock <= self.low_stock_threshold
    
    def get_final_price(self):
        """Retourne le prix final (avec réduction si applicable)"""
        return self.price
    
    def increment_views(self):
        """Incrémente le compteur de vues"""
        self.views_count += 1
        db.session.commit()
    
    def increment_sales(self, quantity=1):
        """Incrémente le compteur de ventes"""
        self.sales_count += quantity
        db.session.commit()
    
    def reduce_stock(self, quantity):
        """Réduit le stock"""
        if self.stock >= quantity:
            self.stock -= quantity
            return True
        return False
    
    def increase_stock(self, quantity):
        """Augmente le stock"""
        self.stock += quantity
    
    def calculate_total_stock_from_variants(self):
        """Calcule le stock total depuis les variantes"""
        from models.product_variant import ProductVariant
        variants = ProductVariant.query.filter_by(product_id=self.id).all()
        
        if variants:
            total = sum(v.stock for v in variants if v.stock)
            return total
        return self.stock
    
    def update_stock_from_variants(self):
        """Met à jour le stock principal depuis les variantes"""
        new_stock = self.calculate_total_stock_from_variants()
        if new_stock != self.stock:
            self.stock = new_stock
            return True
        return False
    
    @property
    def average_rating(self):
        """Calcule la note moyenne des avis approuvés"""
        from models.product_review import ProductReview
        reviews = ProductReview.query.filter_by(
            product_id=self.id,
            is_approved=True
        ).all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)
    
    @property
    def reviews_count(self):
        """Compte le nombre d'avis approuvés"""
        from models.product_review import ProductReview
        return ProductReview.query.filter_by(
            product_id=self.id,
            is_approved=True
        ).count()
