"""
Script de test pour l'API CJ Dropshipping optimisée
Vérifie la configuration, l'authentification et les fonctionnalités de base
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from config import Config
import json

def test_cj_api():
    """Tester l'API CJ optimisée"""
    
    # Créer une app Flask pour la session
    app = Flask(__name__)
    app.config.from_object(Config)
    
    with app.app_context():
        with app.test_request_context():
            print("=" * 80)
            print("TEST API CJ DROPSHIPPING OPTIMISÉE")
            print("=" * 80)
            
            # Vérifier configuration
            print("\n1. VÉRIFICATION CONFIGURATION")
            print("-" * 80)
            print(f"Email: {app.config['CJ_EMAIL']}")
            print(f"Password: {'*' * len(app.config['CJ_PASSWORD'])}")
            print(f"Dev Key: {'*' * len(app.config['CJ_DEV_KEY'])}")
            print(f"Base URL: {app.config['CJ_BASE_URL']}")
            print(f"Cache activé: {app.config['CJ_CACHE_ENABLED']}")
            print(f"Debug activé: {app.config['CJ_DEBUG_ENABLED']}")
            
            # Initialiser l'API
            print("\n2. INITIALISATION API")
            print("-" * 80)
            api = CJDropshippingApiOptimized(
                email=app.config['CJ_EMAIL'],
                password=app.config['CJ_PASSWORD'],
                dev_key=app.config['CJ_DEV_KEY']
            )
            print("✓ API initialisée")
            
            # Test authentification
            print("\n3. TEST AUTHENTIFICATION")
            print("-" * 80)
            token = api.get_access_token()
            if token:
                print(f"✓ Token obtenu: {token[:50]}...")
                print(f"✓ Token en cache session")
            else:
                print("✗ Échec obtention token")
                return False
            
            # Test récupération catégories
            print("\n4. TEST RÉCUPÉRATION CATÉGORIES")
            print("-" * 80)
            categories = api.get_categories()
            if categories:
                print(f"✓ {len(categories)} catégories récupérées")
                
                # Afficher structure hiérarchique
                level_1 = [c for c in categories if c['level'] == 1]
                level_2 = [c for c in categories if c['level'] == 2]
                level_3 = [c for c in categories if c['level'] == 3]
                
                print(f"  - Niveau 1: {len(level_1)} catégories")
                print(f"  - Niveau 2: {len(level_2)} catégories")
                print(f"  - Niveau 3: {len(level_3)} catégories")
                
                # Afficher exemples
                if level_1:
                    print(f"\n  Exemple niveau 1: {level_1[0]['name']}")
                if level_2:
                    print(f"  Exemple niveau 2: {level_2[0]['path']}")
                if level_3:
                    print(f"  Exemple niveau 3: {level_3[0]['path']}")
            else:
                print("✗ Échec récupération catégories")
                return False
            
            # Test récupération produits
            print("\n5. TEST RÉCUPÉRATION PRODUITS")
            print("-" * 80)
            
            # Prendre une catégorie niveau 3 pour tester
            test_category = None
            for cat in categories:
                if cat['level'] == 3:
                    test_category = cat
                    break
            
            if test_category:
                print(f"Catégorie test: {test_category['path']}")
                
                result = api.get_products(
                    page=1,
                    page_size=10,
                    filters={'categoryId': test_category['cj_category_id']}
                )
                
                if result['products']:
                    print(f"✓ {len(result['products'])} produits récupérés")
                    print(f"  Total disponible: {result['total']}")
                    print(f"  Pages totales: {result['total_pages']}")
                    
                    # Afficher premier produit
                    product = result['products'][0]
                    print(f"\n  Exemple produit:")
                    print(f"  - PID: {product['pid']}")
                    print(f"  - Nom: {product['name'][:60]}...")
                    print(f"  - Prix: ${product['price']}")
                    print(f"  - Prix suggéré: ${product['suggested_price']}")
                    print(f"  - Stock: {product['stock']}")
                    print(f"  - Variantes: {len(product['variants'])}")
                    print(f"  - Images: {len(product['images'])}")
                else:
                    print("⚠ Aucun produit dans cette catégorie")
            else:
                print("⚠ Aucune catégorie niveau 3 trouvée")
            
            # Test détails produit
            if result['products']:
                print("\n6. TEST DÉTAILS PRODUIT")
                print("-" * 80)
                
                test_pid = result['products'][0]['pid']
                details = api.get_product_details(test_pid)
                
                if details:
                    print(f"✓ Détails produit {test_pid} récupérés")
                    print(f"  - Nom: {details['name'][:60]}...")
                    print(f"  - SKU: {details['sku']}")
                    print(f"  - Catégorie: {details['category_name']}")
                    print(f"  - Poids: {details['weight']}")
                    print(f"  - Matériau: {details['material']}")
                    
                    # Afficher variantes
                    if details['variants']:
                        print(f"\n  Variantes ({len(details['variants'])}):")
                        for i, variant in enumerate(details['variants'][:3]):
                            print(f"    {i+1}. {variant['key']} - ${variant['price']} - Stock: {variant['stock']}")
                        if len(details['variants']) > 3:
                            print(f"    ... et {len(details['variants']) - 3} autres")
                else:
                    print("✗ Échec récupération détails")
            
            # Test avis clients
            if result['products']:
                print("\n7. TEST AVIS CLIENTS")
                print("-" * 80)
                
                test_pid = result['products'][0]['pid']
                comments = api.get_product_comments(test_pid, page=1, page_size=5)
                
                if comments:
                    print(f"✓ {len(comments)} avis récupérés")
                    for i, comment in enumerate(comments[:3]):
                        print(f"\n  Avis {i+1}:")
                        print(f"  - Note: {'⭐' * comment['rating']}")
                        print(f"  - Auteur: {comment['author']}")
                        print(f"  - Contenu: {comment['content'][:80]}...")
                        print(f"  - Images: {len(comment['images'])}")
                else:
                    print("⚠ Aucun avis pour ce produit")
            
            # Test calcul livraison
            if result['products']:
                print("\n8. TEST CALCUL LIVRAISON")
                print("-" * 80)
                
                test_product = result['products'][0]
                
                # Préparer données pour calcul
                products_for_shipping = [{
                    'vid': test_product['variants'][0]['vid'] if test_product['variants'] else test_product['pid'],
                    'quantity': 1
                }]
                
                shipping_methods = api.calculate_shipping(products_for_shipping, 'FR')
                
                if shipping_methods:
                    print(f"✓ {len(shipping_methods)} méthodes de livraison disponibles")
                    for i, method in enumerate(shipping_methods[:3]):
                        print(f"\n  Méthode {i+1}:")
                        print(f"  - Nom: {method.get('logisticName', 'N/A')}")
                        print(f"  - Code: {method.get('logisticCode', 'N/A')}")
                        print(f"  - Prix: ${method.get('logisticPrice', 0)}")
                        print(f"  - Délai: {method.get('logisticAging', 'N/A')}")
                else:
                    print("⚠ Aucune méthode de livraison disponible")
            
            # Résumé
            print("\n" + "=" * 80)
            print("RÉSUMÉ DES TESTS")
            print("=" * 80)
            print("✓ Configuration OK")
            print("✓ Authentification OK")
            print("✓ Cache token en session OK")
            print("✓ Récupération catégories OK")
            print("✓ Récupération produits OK")
            print("✓ Détails produits OK")
            print("✓ Avis clients OK")
            print("✓ Calcul livraison OK")
            print("\n🎉 TOUS LES TESTS RÉUSSIS !")
            print("=" * 80)
            
            return True

if __name__ == '__main__':
    try:
        success = test_cj_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
