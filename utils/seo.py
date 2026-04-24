"""
Utilitaires SEO
"""
import re
from urllib.parse import urljoin
from flask import request, url_for

def generate_meta_tags(title=None, description=None, image=None, url=None, type='website'):
    """
    Générer les meta tags pour SEO et réseaux sociaux
    
    Args:
        title: Titre de la page
        description: Description
        image: URL de l'image
        url: URL de la page
        type: Type de contenu (website, product, article)
    
    Returns:
        Dict avec les meta tags
    """
    # Valeurs par défaut
    default_title = "MultiProShop - Votre marketplace multi-vendeurs"
    default_description = "Découvrez des milliers de produits de qualité sur MultiProShop. Dropshipping, Print on Demand et plus encore."
    default_image = url_for('static', filename='images/og-image.jpg', _external=True) if url_for else None
    
    meta = {
        'title': title or default_title,
        'description': description or default_description,
        'image': image or default_image,
        'url': url or request.url if request else None,
        'type': type,
        'site_name': 'MultiProShop'
    }
    
    return meta


def generate_product_schema(product):
    """
    Générer le schema.org JSON-LD pour un produit
    
    Args:
        product: Objet Product
    
    Returns:
        Dict schema.org
    """
    schema = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": product.name,
        "description": product.description or "",
        "image": product.image_url if hasattr(product, 'image_url') else "",
        "sku": product.sku if hasattr(product, 'sku') else str(product.id),
        "offers": {
            "@type": "Offer",
            "url": url_for('products.product_detail', product_id=product.id, _external=True),
            "priceCurrency": "EUR",
            "price": float(product.price),
            "availability": "https://schema.org/InStock" if product.stock > 0 else "https://schema.org/OutOfStock",
            "seller": {
                "@type": "Organization",
                "name": "MultiProShop"
            }
        }
    }
    
    if hasattr(product, 'category') and product.category:
        schema["category"] = product.category.name
    
    return schema


def generate_breadcrumb_schema(breadcrumbs):
    """
    Générer le schema.org JSON-LD pour le fil d'Ariane
    
    Args:
        breadcrumbs: Liste de tuples (nom, url)
    
    Returns:
        Dict schema.org
    """
    items = []
    for position, (name, url) in enumerate(breadcrumbs, start=1):
        items.append({
            "@type": "ListItem",
            "position": position,
            "name": name,
            "item": url
        })
    
    schema = {
        "@context": "https://schema.org/",
        "@type": "BreadcrumbList",
        "itemListElement": items
    }
    
    return schema


def slugify(text):
    """
    Convertir un texte en slug URL-friendly
    
    Args:
        text: Texte à convertir
    
    Returns:
        Slug
    """
    # Convertir en minuscules
    text = text.lower()
    
    # Remplacer les accents
    replacements = {
        'à': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c',
        'œ': 'oe', 'æ': 'ae'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Garder seulement lettres, chiffres et espaces
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    
    # Remplacer espaces par tirets
    text = re.sub(r'[\s-]+', '-', text)
    
    # Supprimer tirets en début/fin
    text = text.strip('-')
    
    return text


def generate_sitemap_entry(url, lastmod=None, changefreq='weekly', priority=0.5):
    """
    Générer une entrée de sitemap
    
    Args:
        url: URL de la page
        lastmod: Date de dernière modification
        changefreq: Fréquence de changement
        priority: Priorité (0.0 à 1.0)
    
    Returns:
        Dict avec les infos de l'entrée
    """
    entry = {
        'loc': url,
        'changefreq': changefreq,
        'priority': priority
    }
    
    if lastmod:
        entry['lastmod'] = lastmod.strftime('%Y-%m-%d')
    
    return entry


def truncate_description(text, max_length=160):
    """
    Tronquer une description pour les meta tags
    
    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
    
    Returns:
        Texte tronqué
    """
    if not text:
        return ""
    
    # Supprimer les balises HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # Supprimer les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(text) <= max_length:
        return text
    
    # Tronquer au dernier espace avant max_length
    text = text[:max_length]
    last_space = text.rfind(' ')
    
    if last_space > 0:
        text = text[:last_space]
    
    return text + '...'


def generate_canonical_url(path=None):
    """
    Générer l'URL canonique
    
    Args:
        path: Chemin optionnel
    
    Returns:
        URL canonique
    """
    if path:
        return urljoin(request.url_root, path)
    return request.url.split('?')[0]  # Supprimer les query params


def get_robots_meta(index=True, follow=True):
    """
    Générer le meta robots
    
    Args:
        index: Autoriser l'indexation
        follow: Autoriser le suivi des liens
    
    Returns:
        Contenu du meta robots
    """
    parts = []
    parts.append('index' if index else 'noindex')
    parts.append('follow' if follow else 'nofollow')
    return ', '.join(parts)
