"""
Modèle pour gérer les fournisseurs d'API (CJ Dropshipping, Printify, Amazon, etc.)
"""
from extensions import db
from datetime import datetime
import json

class ApiProvider(db.Model):
    """Modèle pour les fournisseurs d'API"""
    __tablename__ = 'api_provider'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations de base
    name = db.Column(db.String(100), nullable=False, unique=True)  # CJ Dropshipping, Printify, etc.
    slug = db.Column(db.String(50), nullable=False, unique=True)  # cj-dropshipping, printify
    description = db.Column(db.Text, nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    website_url = db.Column(db.String(255), nullable=True)
    
    # Type de provider
    provider_type = db.Column(db.String(50), nullable=False)  # dropshipping, print-on-demand, marketplace, affiliate
    
    # Configuration API
    api_endpoint = db.Column(db.String(255), nullable=True)  # URL de base de l'API
    api_version = db.Column(db.String(20), nullable=True)  # v1, v2, etc.
    auth_type = db.Column(db.String(50), nullable=True)  # api_key, oauth, basic, bearer
    
    # Credentials (stockées de manière sécurisée)
    api_key = db.Column(db.String(255), nullable=True)
    api_secret = db.Column(db.String(255), nullable=True)
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    
    # Configuration supplémentaire (JSON)
    config_json = db.Column(db.Text, nullable=True)  # Autres paramètres spécifiques
    
    # Statut
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_connected = db.Column(db.Boolean, default=False, nullable=False)  # Connexion testée
    last_sync_at = db.Column(db.DateTime, nullable=True)
    
    # Limites et quotas
    rate_limit = db.Column(db.Integer, nullable=True)  # Requêtes par minute
    daily_quota = db.Column(db.Integer, nullable=True)
    requests_today = db.Column(db.Integer, default=0)
    
    # Statistiques
    total_products_imported = db.Column(db.Integer, default=0)
    total_orders_placed = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Float, default=0.0)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    category_mappings = db.relationship('CategoryMapping', backref='api_provider', lazy='dynamic', cascade='all, delete-orphan')
    product_sources = db.relationship('ProductSource', backref='api_provider', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ApiProvider {self.name}>'
    
    def get_config(self):
        """Récupérer la configuration JSON"""
        if self.config_json:
            return json.loads(self.config_json)
        return {}
    
    def set_config(self, config_dict):
        """Définir la configuration JSON"""
        self.config_json = json.dumps(config_dict)
    
    def test_connection(self):
        """Tester la connexion à l'API"""
        # À implémenter selon chaque provider
        return False
    
    def increment_requests(self):
        """Incrémenter le compteur de requêtes"""
        self.requests_today += 1
        db.session.commit()
    
    def reset_daily_quota(self):
        """Réinitialiser le quota journalier"""
        self.requests_today = 0
        db.session.commit()


class CategoryMapping(db.Model):
    """Mapping entre catégories du provider et catégories MPS"""
    __tablename__ = 'category_mapping'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Provider
    provider_id = db.Column(db.Integer, db.ForeignKey('api_provider.id'), nullable=False)
    
    # Catégorie externe (du provider)
    external_category_id = db.Column(db.String(100), nullable=False)
    external_category_name = db.Column(db.String(200), nullable=False)
    external_category_path = db.Column(db.String(500), nullable=True)  # Electronics > Phones > Smartphones
    
    # Catégorie MPS (locale)
    mps_category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # Configuration
    auto_import = db.Column(db.Boolean, default=True)  # Importer automatiquement les produits
    apply_markup = db.Column(db.Float, default=1.3)  # Marge (1.3 = +30%)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    mps_category = db.relationship('Category', backref='mappings')
    
    def __repr__(self):
        return f'<CategoryMapping {self.external_category_name} → {self.mps_category.name}>'


class ProductSource(db.Model):
    """Lien entre un produit MPS et sa source externe"""
    __tablename__ = 'product_source'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Produit MPS
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    # Provider
    provider_id = db.Column(db.Integer, db.ForeignKey('api_provider.id'), nullable=False)
    
    # Identifiants externes
    external_product_id = db.Column(db.String(100), nullable=False)
    external_variant_id = db.Column(db.String(100), nullable=True)
    external_sku = db.Column(db.String(100), nullable=True)
    
    # Prix et stock externes
    external_price = db.Column(db.Float, nullable=False)
    external_stock = db.Column(db.Integer, default=0)
    external_currency = db.Column(db.String(3), default='USD')
    
    # Données brutes (JSON)
    raw_data = db.Column(db.Text, nullable=True)  # Données complètes du provider
    
    # Synchronisation
    last_synced_at = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(20), default='pending')  # pending, synced, error
    sync_error = db.Column(db.Text, nullable=True)
    
    # Statut
    is_active = db.Column(db.Boolean, default=True)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    product = db.relationship('Product', backref='sources')
    
    def __repr__(self):
        return f'<ProductSource {self.external_product_id} from {self.api_provider.name}>'
    
    def get_raw_data(self):
        """Récupérer les données brutes"""
        if self.raw_data:
            return json.loads(self.raw_data)
        return {}
    
    def set_raw_data(self, data_dict):
        """Définir les données brutes"""
        try:
            self.raw_data = json.dumps(data_dict, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            print(f"Erreur sérialisation JSON: {e}")
            self.raw_data = json.dumps({'error': 'Serialization failed', 'message': str(e)})


class ApiSyncLog(db.Model):
    """Journal des synchronisations API"""
    __tablename__ = 'api_sync_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Provider
    provider_id = db.Column(db.Integer, db.ForeignKey('api_provider.id'), nullable=False)
    
    # Type de sync
    sync_type = db.Column(db.String(50), nullable=False)  # products, categories, stock, orders
    
    # Résultats
    status = db.Column(db.String(20), nullable=False)  # success, error, partial
    items_processed = db.Column(db.Integer, default=0)
    items_created = db.Column(db.Integer, default=0)
    items_updated = db.Column(db.Integer, default=0)
    items_failed = db.Column(db.Integer, default=0)
    
    # Détails
    message = db.Column(db.Text, nullable=True)
    error_details = db.Column(db.Text, nullable=True)
    
    # Durée
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    
    # Relation
    provider = db.relationship('ApiProvider', backref='sync_logs')
    
    def __repr__(self):
        return f'<ApiSyncLog {self.sync_type} - {self.status}>'
