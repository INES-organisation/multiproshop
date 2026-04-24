"""
Vérifier les données des produits existants
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import app
from models.product import Product
from models.product_variant import ProductVariant

def check_products():
    """Vérifier les produits et leurs données"""
    print("\n" + "="*70)
    print("VÉRIFICATION DONNÉES PRODUITS")
    print("="*70 + "\n")
    
    with app.app_context():
        # Compter les produits
        total_products = Product.query.count()
        print(f"Total produits en BDD: {total_products}\n")
        
        if total_products == 0:
            print("❌ Aucun produit en base de données")
            print("\nIl faut d'abord synchroniser les produits depuis CJ.")
            return
        
        # Afficher quelques exemples
        print("Exemples de produits:\n")
        products = Product.query.limit(5).all()
        
        for i, product in enumerate(products, 1):
            print(f"{i}. {product.name}")
            print(f"   SKU: {product.sku}")
            print(f"   Prix: ${product.price}")
            print(f"   Stock: {product.stock}")
            print(f"   Description: {product.description[:50] if product.description else 'Aucune'}...")
            
            # Vérifier les champs CJ
            print(f"   CJ PID: {product.cj_pid or 'Non défini'}")
            print(f"   Poids: {product.product_weight or 'Non défini'}")
            print(f"   Matériau: {product.material or 'Non défini'}")
            print(f"   Publié: {'Oui' if product.published else 'Non'}")
            
            # Vérifier les variantes
            variants = ProductVariant.query.filter_by(product_id=product.id).all()
            print(f"   Variantes: {len(variants)}")
            
            if variants:
                for v in variants[:2]:
                    print(f"      - {v.color or 'N/A'} / {v.size or 'N/A'} - Stock: {v.stock}")
            
            print()
        
        # Statistiques
        print("="*70)
        print("STATISTIQUES")
        print("="*70)
        
        products_with_description = Product.query.filter(Product.description != None).filter(Product.description != '').count()
        products_with_cj_pid = Product.query.filter(Product.cj_pid != None).count()
        products_published = Product.query.filter_by(published=True).count()
        total_variants = ProductVariant.query.count()
        
        print(f"Produits avec description: {products_with_description}/{total_products}")
        print(f"Produits avec CJ PID: {products_with_cj_pid}/{total_products}")
        print(f"Produits publiés: {products_published}/{total_products}")
        print(f"Total variantes: {total_variants}")
        
        # Problèmes détectés
        print("\n" + "="*70)
        print("PROBLÈMES DÉTECTÉS")
        print("="*70)
        
        issues = []
        
        if products_with_description < total_products * 0.5:
            issues.append(f"⚠️  {total_products - products_with_description} produits sans description")
        
        if products_with_cj_pid < total_products * 0.5:
            issues.append(f"⚠️  {total_products - products_with_cj_pid} produits sans CJ PID")
        
        if total_variants == 0:
            issues.append("⚠️  Aucune variante - Les produits n'ont pas de couleurs/tailles")
        
        # Vérifier si tous les produits ont le même stock
        stocks = [p.stock for p in Product.query.all()]
        if len(set(stocks)) == 1:
            issues.append(f"⚠️  TOUS les produits ont le même stock ({stocks[0]}) - Problème de synchronisation")
        
        if issues:
            for issue in issues:
                print(issue)
        else:
            print("✅ Aucun problème majeur détecté")
        
        print("\n" + "="*70)
        print("RECOMMANDATIONS")
        print("="*70)
        
        if products_with_cj_pid < total_products:
            print("1. Synchroniser les produits depuis CJ pour obtenir les données complètes")
        
        if total_variants == 0:
            print("2. Synchroniser les variantes pour chaque produit")
        
        if products_with_description < total_products * 0.5:
            print("3. Enrichir les produits avec l'API CJ pour obtenir descriptions et avis")
        
        print()

if __name__ == '__main__':
    check_products()
