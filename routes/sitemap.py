"""
Routes pour sitemap.xml et robots.txt
Phase 4 - SEO
"""
from flask import Blueprint, Response, render_template_string
from datetime import datetime
from models.product import Product
from models.category import Category

sitemap_bp = Blueprint('sitemap', __name__)


@sitemap_bp.route('/sitemap.xml')
def sitemap():
    """Générer sitemap.xml"""
    
    # URLs statiques
    urls = [
        {
            'loc': '/',
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'daily',
            'priority': '1.0'
        },
        {
            'loc': '/products/',
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'daily',
            'priority': '0.9'
        },
        {
            'loc': '/search',
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'weekly',
            'priority': '0.8'
        }
    ]
    
    # Ajouter les catégories (exclure les catégories CJ)
    categories = Category.query.filter_by(is_active=True, visible=True).all()
    for category in categories:
        urls.append({
            'loc': f'/products/category/{category.id}',
            'lastmod': category.updated_at.strftime('%Y-%m-%d') if category.updated_at else datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'weekly',
            'priority': '0.8'
        })
    
    # Ajouter les produits actifs
    products = Product.query.filter(Product.is_active == True).all()
    for product in products:
        urls.append({
            'loc': f'/products/{product.id}',
            'lastmod': product.updated_at.strftime('%Y-%m-%d') if product.updated_at else datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'weekly',
            'priority': '0.7'
        })
    
    # Générer XML
    sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{% for url in urls %}
    <url>
        <loc>{{ base_url }}{{ url.loc }}</loc>
        <lastmod>{{ url.lastmod }}</lastmod>
        <changefreq>{{ url.changefreq }}</changefreq>
        <priority>{{ url.priority }}</priority>
    </url>
{% endfor %}
</urlset>'''
    
    xml = render_template_string(
        sitemap_xml,
        urls=urls,
        base_url='https://multiproshop.local'
    )
    
    return Response(xml, mimetype='application/xml')


@sitemap_bp.route('/robots.txt')
def robots():
    """Générer robots.txt"""
    
    robots_txt = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /user/
Disallow: /cart/
Disallow: /api/

Sitemap: https://multiproshop.local/sitemap.xml
"""
    
    return Response(robots_txt, mimetype='text/plain')
