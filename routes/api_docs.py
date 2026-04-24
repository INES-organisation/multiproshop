"""
Documentation API avec Flask-RESTX (Swagger)
Phase 4 - Documentation API
"""
from flask import Blueprint
from flask_restx import Api, Resource, fields, Namespace

# Créer le blueprint
api_docs_bp = Blueprint('api_docs', __name__, url_prefix='/api/v1')

# Configurer Flask-RESTX
api = Api(
    api_docs_bp,
    version='1.0',
    title='MultiProShop API',
    description='API REST pour la plateforme e-commerce MultiProShop avec intégration CJ Dropshipping',
    doc='/docs',
    prefix='/api/v1'
)

# Namespaces
products_ns = Namespace('products', description='Opérations sur les produits')
search_ns = Namespace('search', description='Recherche et suggestions')
categories_ns = Namespace('categories', description='Gestion des catégories')
metrics_ns = Namespace('metrics', description='Métriques et monitoring')

api.add_namespace(products_ns)
api.add_namespace(search_ns)
api.add_namespace(categories_ns)
api.add_namespace(metrics_ns)

# Modèles de données
product_model = api.model('Product', {
    'id': fields.Integer(required=True, description='ID du produit'),
    'name': fields.String(required=True, description='Nom du produit'),
    'description': fields.String(description='Description du produit'),
    'price': fields.Float(required=True, description='Prix du produit'),
    'compare_price': fields.Float(description='Prix barré'),
    'stock_quantity': fields.Integer(description='Quantité en stock'),
    'sku': fields.String(description='SKU du produit'),
    'image_url': fields.String(description='URL de l\'image'),
    'is_active': fields.Boolean(description='Produit actif'),
    'category_id': fields.Integer(description='ID de la catégorie')
})

product_list_model = api.model('ProductList', {
    'products': fields.List(fields.Nested(product_model)),
    'total': fields.Integer(description='Nombre total de produits'),
    'page': fields.Integer(description='Page actuelle'),
    'per_page': fields.Integer(description='Produits par page'),
    'pages': fields.Integer(description='Nombre total de pages')
})

search_result_model = api.model('SearchResult', {
    'success': fields.Boolean(description='Succès de la recherche'),
    'products': fields.List(fields.Nested(product_model)),
    'total': fields.Integer(description='Nombre de résultats'),
    'query': fields.String(description='Terme de recherche'),
    'page': fields.Integer(description='Page actuelle'),
    'per_page': fields.Integer(description='Résultats par page')
})

suggestion_model = api.model('Suggestion', {
    'suggestions': fields.List(fields.String, description='Liste de suggestions')
})

category_model = api.model('Category', {
    'id': fields.Integer(required=True, description='ID de la catégorie'),
    'name': fields.String(required=True, description='Nom de la catégorie'),
    'description': fields.String(description='Description'),
    'parent_id': fields.Integer(description='ID catégorie parente'),
    'product_count': fields.Integer(description='Nombre de produits')
})

metrics_model = api.model('Metrics', {
    'timestamp': fields.String(description='Timestamp ISO'),
    'database': fields.Raw(description='Métriques base de données'),
    'products': fields.Raw(description='Métriques produits'),
    'orders': fields.Raw(description='Métriques commandes'),
    'users': fields.Raw(description='Métriques utilisateurs')
})

health_model = api.model('Health', {
    'status': fields.String(description='État de santé (healthy/degraded/unhealthy)'),
    'timestamp': fields.String(description='Timestamp ISO'),
    'checks': fields.Raw(description='Résultats des checks')
})


# Routes Products
@products_ns.route('/')
class ProductList(Resource):
    @products_ns.doc('list_products')
    @products_ns.marshal_with(product_list_model)
    @products_ns.param('page', 'Numéro de page', type=int, default=1)
    @products_ns.param('per_page', 'Produits par page', type=int, default=20)
    @products_ns.param('category_id', 'Filtrer par catégorie', type=int)
    def get(self):
        """Liste tous les produits"""
        from flask import request
        from models.product import Product
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category_id = request.args.get('category_id', type=int)
        
        query = Product.query.filter(Product.is_active == True)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'products': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }


@products_ns.route('/<int:id>')
@products_ns.param('id', 'ID du produit')
class ProductDetail(Resource):
    @products_ns.doc('get_product')
    @products_ns.marshal_with(product_model)
    @products_ns.response(404, 'Produit non trouvé')
    def get(self, id):
        """Obtenir un produit par son ID"""
        from models.product import Product
        
        product = Product.query.get_or_404(id)
        return product.to_dict()


# Routes Search
@search_ns.route('/')
class Search(Resource):
    @search_ns.doc('search_products')
    @search_ns.marshal_with(search_result_model)
    @search_ns.param('q', 'Terme de recherche', required=True)
    @search_ns.param('page', 'Numéro de page', type=int, default=1)
    @search_ns.param('per_page', 'Résultats par page', type=int, default=20)
    @search_ns.param('min_price', 'Prix minimum', type=float)
    @search_ns.param('max_price', 'Prix maximum', type=float)
    @search_ns.param('sort_by', 'Tri (price_asc, price_desc, name, newest)')
    def get(self):
        """Rechercher des produits"""
        from flask import request
        from services.search_service import get_search_service
        
        query = request.args.get('q', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        sort_by = request.args.get('sort_by', 'relevance')
        
        search_service = get_search_service()
        result = search_service.search_products(
            query=query,
            page=page,
            per_page=per_page,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by
        )
        
        return {
            'success': result['success'],
            'products': [p.to_dict() for p in result['products']],
            'total': result['total'],
            'query': query,
            'page': page,
            'per_page': per_page
        }


@search_ns.route('/suggestions')
class SearchSuggestions(Resource):
    @search_ns.doc('get_suggestions')
    @search_ns.marshal_with(suggestion_model)
    @search_ns.param('q', 'Terme de recherche', required=True)
    @search_ns.param('limit', 'Nombre de suggestions', type=int, default=5)
    def get(self):
        """Obtenir des suggestions de recherche"""
        from flask import request
        from services.search_service import get_search_service
        
        query = request.args.get('q', '')
        limit = request.args.get('limit', 5, type=int)
        
        search_service = get_search_service()
        suggestions = search_service.get_search_suggestions(query, limit=limit)
        
        return {'suggestions': suggestions}


# Routes Categories
@categories_ns.route('/')
class CategoryList(Resource):
    @categories_ns.doc('list_categories')
    @categories_ns.marshal_list_with(category_model)
    def get(self):
        """Liste toutes les catégories"""
        from models.category import Category
        
        categories = Category.query.all()
        return [c.to_dict() for c in categories]


@categories_ns.route('/<int:id>')
@categories_ns.param('id', 'ID de la catégorie')
class CategoryDetail(Resource):
    @categories_ns.doc('get_category')
    @categories_ns.marshal_with(category_model)
    @categories_ns.response(404, 'Catégorie non trouvée')
    def get(self, id):
        """Obtenir une catégorie par son ID"""
        from models.category import Category
        
        category = Category.query.get_or_404(id)
        return category.to_dict()


# Routes Metrics
@metrics_ns.route('/system')
class SystemMetrics(Resource):
    @metrics_ns.doc('get_system_metrics')
    @metrics_ns.marshal_with(metrics_model)
    def get(self):
        """Obtenir les métriques système"""
        from services.metrics_service import get_metrics_service
        
        metrics_service = get_metrics_service()
        return metrics_service.get_system_metrics()


@metrics_ns.route('/health')
class HealthCheck(Resource):
    @metrics_ns.doc('health_check')
    @metrics_ns.marshal_with(health_model)
    def get(self):
        """Vérifier l'état de santé du système"""
        from services.metrics_service import get_metrics_service
        
        metrics_service = get_metrics_service()
        return metrics_service.get_health_status()
