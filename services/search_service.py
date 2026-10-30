"""
Service de recherche avancée pour les produits
Phase 3.2 - Recherche full-text avec scoring
"""
from typing import Dict, List, Optional
from sqlalchemy import or_, and_, func
from models.product import Product
from models.category import Category
from extensions import db, cache
import logging

logger = logging.getLogger(__name__)

# Les titres des produits CJ sont en anglais tant qu'ils ne sont pas traduits : un mot français
# cherché est aussi cherché sous ses équivalents anglais courants.
FR_EN_TERMS = {
    'accessoire': ['accessory', 'accessories'], 'adaptateur': ['adapter'], 'aimant': ['magnet', 'magnetic'],
    'aspirateur': ['vacuum'], 'assiette': ['plate'], 'bague': ['ring'], 'balai': ['broom', 'mop'],
    'ballon': ['ball', 'balloon'], 'batterie': ['battery', 'power bank'], 'bebe': ['baby'], 'bijou': ['jewelry'],
    'blanc': ['white'], 'bleu': ['blue'], 'boite': ['box'], 'bol': ['bowl'], 'bonnet': ['beanie', 'hat'],
    'bottes': ['boots'], 'botte': ['boot'], 'boucle': ['earring', 'buckle'], 'bouteille': ['bottle'],
    'bracelet': ['bracelet'], 'brosse': ['brush'], 'cable': ['cable'], 'cadre': ['frame'], 'camera': ['camera'],
    'casque': ['headphone', 'headset', 'helmet'], 'casquette': ['cap'], 'ceinture': ['belt'], 'chaise': ['chair'],
    'chargeur': ['charger'], 'chat': ['cat'], 'chaussette': ['sock'], 'chaussure': ['shoe', 'sneaker'],
    'chemise': ['shirt'], 'chien': ['dog', 'pet'], 'clavier': ['keyboard'], 'coque': ['case', 'cover'],
    'collier': ['necklace', 'collar'], 'coussin': ['pillow', 'cushion'], 'couteau': ['knife'], 'couverture': ['blanket'],
    'cuisine': ['kitchen'], 'cuillere': ['spoon'], 'decoration': ['decor', 'decoration'], 'ecouteur': ['earphone', 'earbud'],
    'enceinte': ['speaker'], 'enfant': ['kid', 'children', 'child'], 'eponge': ['sponge'], 'etui': ['case', 'pouch'],
    'femme': ['women', 'woman', 'ladies'], 'fille': ['girl'], 'fleur': ['flower'], 'garcon': ['boy'], 'gant': ['glove'],
    'gourde': ['bottle', 'flask'], 'homme': ['men', 'man'], 'horloge': ['clock'], 'jardin': ['garden'],
    'jeu': ['game'], 'jouet': ['toy'], 'jupe': ['skirt'], 'lampe': ['lamp', 'light'], 'lit': ['bed'],
    'lumiere': ['light', 'lamp'], 'lunettes': ['glasses', 'sunglasses'], 'maillot': ['swimsuit', 'jersey'],
    'maison': ['home', 'house'], 'maquillage': ['makeup', 'cosmetic'], 'miroir': ['mirror'], 'montre': ['watch'],
    'moto': ['motorcycle'], 'noir': ['black'], 'ordinateur': ['computer', 'laptop'], 'oreiller': ['pillow'],
    'pantalon': ['pants', 'trousers'], 'parapluie': ['umbrella'], 'peigne': ['comb'], 'pochette': ['pouch', 'bag'],
    'poele': ['pan'], 'porte': ['holder', 'door'], 'portefeuille': ['wallet'], 'puzzle': ['puzzle'],
    'rangement': ['storage', 'organizer'], 'robe': ['dress'], 'rose': ['pink', 'rose'], 'rouge': ['red'],
    'sac': ['bag', 'backpack'], 'serviette': ['towel'], 'souris': ['mouse'], 'sport': ['sport', 'fitness'],
    'stylo': ['pen'], 'support': ['holder', 'stand', 'mount'], 'table': ['table'], 'tablette': ['tablet'],
    'tapis': ['rug', 'mat', 'carpet'], 'tasse': ['mug', 'cup'], 'telephone': ['phone'], 'tente': ['tent'],
    'tondeuse': ['trimmer', 'clipper'], 'velo': ['bike', 'bicycle'], 'verre': ['glass'], 'vert': ['green'],
    'veste': ['jacket', 'coat'], 'voiture': ['car'], 'yoga': ['yoga'],
}
STOP_WORDS = {'de', 'des', 'du', 'la', 'le', 'les', 'un', 'une', 'pour', 'et', 'en', 'a', 'au', 'aux', 'avec', 'sans', 'the', 'for', 'and', 'with'}


def _plain(word: str) -> str:
    """Minuscules sans accents, pour retrouver le mot dans FR_EN_TERMS"""
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', word.lower()) if unicodedata.category(c) != 'Mn')


def search_terms(query: Optional[str]) -> List[List[str]]:
    """Un groupe par mot cherché : le mot lui-même et ses équivalents anglais"""
    groups = []
    for word in (query or '').replace(',', ' ').split():
        plain = _plain(word)
        if len(plain) < 2 or plain in STOP_WORDS:
            continue
        singular = plain[:-1] if len(plain) > 3 and plain[-1] in 'sx' else plain
        groups.append(list(dict.fromkeys([word, *FR_EN_TERMS.get(plain, FR_EN_TERMS.get(singular, []))])))
    return groups


def text_filter(query: Optional[str], with_sku: bool = True):
    """Chaque mot (ou un de ses équivalents) doit apparaître dans le nom, la description ou la référence"""
    columns = [Product.name, Product.description] + ([Product.sku] if with_sku else [])
    return and_(*(or_(*(col.ilike(f'%{term}%') for term in group for col in columns))
                  for group in search_terms(query)))



class SearchService:
    """Service de recherche de produits"""
    
    def __init__(self):
        """Initialiser le service de recherche"""
        pass
    
    def search_products(
        self,
        query: str,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        sort_by: str = 'relevance',
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """
        Rechercher des produits avec filtres
        
        Args:
            query: Terme de recherche
            category_id: Filtrer par catégorie
            min_price: Prix minimum
            max_price: Prix maximum
            in_stock_only: Uniquement produits en stock
            sort_by: Tri (relevance, price_asc, price_desc, name, newest)
            page: Numéro de page
            per_page: Résultats par page
            
        Returns:
            dict: Résultats avec pagination
        """
        try:
            # Base query
            base_query = Product.query.filter(Product.is_active == True)
            
            # Recherche full-text
            groups = search_terms(query)
            if groups:
                base_query = base_query.filter(text_filter(query))
            
            # Filtre catégorie
            if category_id:
                base_query = base_query.filter(Product.category_id == category_id)
            
            # Filtre prix
            if min_price is not None:
                base_query = base_query.filter(Product.price >= min_price)
            if max_price is not None:
                base_query = base_query.filter(Product.price <= max_price)
            
            # Filtre stock
            if in_stock_only:
                base_query = base_query.filter(Product.stock > 0)
            
            # Tri
            if sort_by == 'price_asc':
                base_query = base_query.order_by(Product.price.asc())
            elif sort_by == 'price_desc':
                base_query = base_query.order_by(Product.price.desc())
            elif sort_by == 'name':
                base_query = base_query.order_by(Product.name.asc())
            elif sort_by == 'newest':
                base_query = base_query.order_by(Product.created_at.desc())
            else:  # relevance (par défaut)
                # Priorité aux produits dont le nom contient le premier mot, puis aux meilleures ventes
                if groups:
                    base_query = base_query.order_by(
                        Product.published_at.is_(None),  # produits choisis et traduits d'abord
                        or_(*(Product.name.ilike(f'%{term}%') for term in groups[0])).desc(),
                        Product.sales_count.desc(),
                        Product.id.desc()
                    )
                else:
                    base_query = base_query.order_by(Product.published_at.is_(None), Product.sales_count.desc(), Product.id.desc())
            
            # Pagination
            pagination = base_query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'success': True,
                'products': pagination.items,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
            
        except Exception as e:
            logger.error(f"Erreur recherche produits: {e}")
            return {
                'success': False,
                'error': str(e),
                'products': [],
                'total': 0
            }
    
    def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Obtenir des suggestions de recherche
        
        Args:
            query: Début de la recherche
            limit: Nombre de suggestions
            
        Returns:
            Liste de suggestions
        """
        try:
            return [p.name for p in self.get_product_suggestions(query, limit)]
            
        except Exception as e:
            logger.error(f"Erreur suggestions recherche: {e}")
            return []
    
    def get_product_suggestions(self, query: str, limit: int = 5) -> List[Product]:
        """Produits proposés pendant la frappe : noms qui contiennent tous les mots, en stock d'abord"""
        if not query or len(query.strip()) < 2 or not search_terms(query):
            return []
        name_filter = and_(*(or_(*(Product.name.ilike(f'%{term}%') for term in group)) for group in search_terms(query)))
        return Product.query.filter(Product.is_active == True, name_filter) \
            .order_by((Product.stock > 0).desc(), Product.published_at.is_(None), Product.sales_count.desc(), Product.id.desc()) \
            .limit(limit).all()
    
    def get_popular_searches(self, limit: int = 10) -> List[str]:
        """
        Obtenir les recherches populaires (à implémenter avec tracking)
        
        Args:
            limit: Nombre de résultats
            
        Returns:
            Liste de termes populaires
        """
        # TODO: Implémenter tracking des recherches
        # Pour l'instant, retourner les catégories populaires
        try:
            categories = Category.query.limit(limit).all()
            return [cat.name for cat in categories]
        except:
            return []
    
    def get_facets(self, query: Optional[str] = None, category_id: Optional[int] = None) -> Dict:
        """
        Obtenir les facettes de recherche (filtres disponibles)
        
        Args:
            query: Terme de recherche
            category_id: Catégorie
            
        Returns:
            dict: Facettes (prix, catégories, etc.)
        """
        try:
            base_query = Product.query.filter(Product.is_active == True)
            if search_terms(query):
                base_query = base_query.filter(text_filter(query, with_sku=False))
            if category_id:
                base_query = base_query.filter(Product.category_id == category_id)
            
            # Agrégats calculés par la base, sans charger les produits
            price_stats = base_query.with_entities(
                func.min(Product.price).label('min_price'),
                func.max(Product.price).label('max_price')
            ).first()
            category_counts = base_query.join(Category, Product.category_id == Category.id).with_entities(
                Category.id, Category.name, func.count(Product.id)
            ).group_by(Category.id, Category.name).all()
            categories = [{'id': cat_id, 'name': name, 'count': count} for cat_id, name, count in category_counts]
            
            return {
                'success': True,
                'price_range': {
                    'min': float(price_stats.min_price or 0),
                    'max': float(price_stats.max_price or 0)
                },
                'categories': categories
            }
            
        except Exception as e:
            logger.error(f"Erreur facettes recherche: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Instance globale
_search_service = None

def get_search_service() -> SearchService:
    """Obtenir l'instance du service de recherche"""
    global _search_service
    
    if _search_service is None:
        _search_service = SearchService()
    
    return _search_service
