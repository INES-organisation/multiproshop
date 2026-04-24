"""
Service SEO pour optimisation moteurs de recherche
Phase 4 - SEO optimisation
"""
from typing import Dict, List, Optional
from models.product import Product
from models.category import Category


class SEOService:
    """Service pour gérer le SEO"""
    
    @staticmethod
    def generate_meta_tags(page_type: str, data: Dict = None) -> Dict[str, str]:
        """
        Générer les meta tags pour une page
        
        Args:
            page_type: Type de page (home, product, category, search)
            data: Données de la page
            
        Returns:
            dict: Meta tags
        """
        meta_tags = {
            'title': '',
            'description': '',
            'keywords': '',
            'og_title': '',
            'og_description': '',
            'og_image': '',
            'og_type': 'website',
            'twitter_card': 'summary_large_image'
        }
        
        if page_type == 'home':
            meta_tags.update({
                'title': 'MultiProShop - Votre boutique en ligne',
                'description': 'Découvrez notre large sélection de produits de qualité à prix compétitifs. Livraison rapide et service client exceptionnel.',
                'keywords': 'boutique en ligne, e-commerce, produits, shopping',
                'og_title': 'MultiProShop - Votre boutique en ligne',
                'og_description': 'Découvrez notre large sélection de produits de qualité'
            })
        
        elif page_type == 'product' and data:
            product = data.get('product')
            if product:
                description = SEOService._generate_product_description(product)
                
                meta_tags.update({
                    'title': f'{product.name} | MultiProShop',
                    'description': description,
                    'keywords': SEOService._generate_product_keywords(product),
                    'og_title': product.name,
                    'og_description': description,
                    'og_image': product.image_url or '',
                    'og_type': 'product'
                })
        
        elif page_type == 'category' and data:
            category = data.get('category')
            if category:
                meta_tags.update({
                    'title': f'{category.name} | MultiProShop',
                    'description': f'Découvrez notre sélection de {category.name.lower()}. Produits de qualité à prix compétitifs.',
                    'keywords': f'{category.name}, produits, boutique en ligne',
                    'og_title': f'{category.name} | MultiProShop',
                    'og_description': f'Découvrez notre sélection de {category.name.lower()}'
                })
        
        elif page_type == 'search' and data:
            query = data.get('query', '')
            meta_tags.update({
                'title': f'Recherche: {query} | MultiProShop',
                'description': f'Résultats de recherche pour "{query}". Trouvez les meilleurs produits.',
                'keywords': f'{query}, recherche, produits',
                'og_title': f'Recherche: {query}',
                'og_description': f'Résultats de recherche pour "{query}"'
            })
        
        return meta_tags
    
    @staticmethod
    def _generate_product_description(product: Product) -> str:
        """Générer description SEO pour un produit"""
        description = product.name
        
        if product.description:
            # Prendre les 150 premiers caractères
            desc_text = product.description[:150].strip()
            if len(product.description) > 150:
                desc_text += '...'
            description = desc_text
        
        # Ajouter le prix
        if product.price:
            description += f' - À partir de {product.price}€'
        
        return description
    
    @staticmethod
    def _generate_product_keywords(product: Product) -> str:
        """Générer keywords pour un produit"""
        keywords = [product.name]
        
        if product.category:
            keywords.append(product.category.name)
        
        if product.sku:
            keywords.append(product.sku)
        
        keywords.extend(['boutique en ligne', 'acheter', 'prix'])
        
        return ', '.join(keywords)
    
    @staticmethod
    def generate_schema_org(page_type: str, data: Dict = None) -> Dict:
        """
        Générer le markup Schema.org
        
        Args:
            page_type: Type de page
            data: Données de la page
            
        Returns:
            dict: Schema.org JSON-LD
        """
        if page_type == 'product' and data:
            product = data.get('product')
            if product:
                return {
                    "@context": "https://schema.org/",
                    "@type": "Product",
                    "name": product.name,
                    "image": product.image_url or '',
                    "description": product.description or product.name,
                    "sku": product.sku or '',
                    "offers": {
                        "@type": "Offer",
                        "url": f"/products/{product.id}",
                        "priceCurrency": "EUR",
                        "price": str(product.price) if product.price else "0",
                        "availability": "https://schema.org/InStock" if product.stock_quantity > 0 else "https://schema.org/OutOfStock"
                    }
                }
        
        elif page_type == 'organization':
            return {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "MultiProShop",
                "url": "https://multiproshop.local",
                "logo": "/static/images/logo.png",
                "contactPoint": {
                    "@type": "ContactPoint",
                    "contactType": "customer service",
                    "email": "contact@multiproshop.com"
                }
            }
        
        return {}
    
    @staticmethod
    def generate_breadcrumbs(items: List[Dict]) -> Dict:
        """
        Générer breadcrumbs Schema.org
        
        Args:
            items: Liste de {name, url}
            
        Returns:
            dict: Breadcrumbs JSON-LD
        """
        breadcrumbs = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": []
        }
        
        for i, item in enumerate(items, 1):
            breadcrumbs["itemListElement"].append({
                "@type": "ListItem",
                "position": i,
                "name": item.get('name', ''),
                "item": item.get('url', '')
            })
        
        return breadcrumbs
    
    @staticmethod
    def generate_canonical_url(path: str, base_url: str = 'https://multiproshop.local') -> str:
        """Générer URL canonique"""
        return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def get_seo_service() -> SEOService:
    """Obtenir instance du service SEO"""
    return SEOService()
