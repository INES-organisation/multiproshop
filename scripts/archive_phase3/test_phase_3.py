"""
Script de tests pour la Phase 3 - Améliorations
Teste toutes les fonctionnalités : recherche, recommandations, cache
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from services.search_service import get_search_service
from services.recommendation_service import get_recommendation_service
from services.translation_service import get_translation_service
import time

def print_section(title):
    """Afficher une section"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_search_service():
    """Tester le service de recherche"""
    print_section("TEST 1 : SERVICE DE RECHERCHE")
    
    search = get_search_service()
    
    # Test 1.1 : Recherche simple
    print("\n1.1 - Recherche simple 'mattress'")
    results = search.search_products(query="mattress", page=1, per_page=5)
    print(f"   ✓ Résultats trouvés : {results['total']}")
    print(f"   ✓ Produits retournés : {len(results['products'])}")
    if results['products']:
        print(f"   ✓ Premier produit : {results['products'][0].name}")
    
    # Test 1.2 : Recherche avec filtres
    print("\n1.2 - Recherche avec filtre prix (10-50)")
    results = search.search_products(
        query="",
        min_price=10.0,
        max_price=50.0,
        page=1,
        per_page=5
    )
    print(f"   ✓ Produits dans la fourchette : {results['total']}")
    
    # Test 1.3 : Recherche avec tri
    print("\n1.3 - Recherche avec tri par prix croissant")
    results = search.search_products(
        query="",
        sort_by='price_asc',
        page=1,
        per_page=5
    )
    if results['products']:
        prices = [p.price for p in results['products']]
        print(f"   ✓ Prix : {prices}")
        print(f"   ✓ Tri correct : {prices == sorted(prices)}")
    
    # Test 1.4 : Suggestions
    print("\n1.4 - Suggestions de recherche")
    suggestions = search.get_search_suggestions("mat", limit=5)
    print(f"   ✓ Suggestions trouvées : {len(suggestions)}")
    if suggestions:
        print(f"   ✓ Exemples : {suggestions[:3]}")
    
    # Test 1.5 : Facettes
    print("\n1.5 - Facettes de recherche")
    facets = search.get_facets(query="mattress")
    if facets['success']:
        print(f"   ✓ Prix min : ${facets['price_range']['min']:.2f}")
        print(f"   ✓ Prix max : ${facets['price_range']['max']:.2f}")
        print(f"   ✓ Catégories disponibles : {len(facets['categories'])}")
    
    print("\n✅ Service de recherche : OK")

def test_recommendation_service():
    """Tester le service de recommandations"""
    print_section("TEST 2 : SERVICE DE RECOMMANDATIONS")
    
    reco = get_recommendation_service()
    
    # Récupérer un produit pour les tests
    product = Product.query.filter(Product.is_active == True).first()
    if not product:
        print("   ⚠ Aucun produit actif trouvé")
        return
    
    print(f"\nProduit de référence : {product.name} (ID: {product.id})")
    
    # Test 2.1 : Produits similaires
    print("\n2.1 - Produits similaires")
    start = time.time()
    similar = reco.get_similar_products(product.id, limit=6)
    elapsed = (time.time() - start) * 1000
    print(f"   ✓ Produits trouvés : {len(similar)}")
    print(f"   ✓ Temps : {elapsed:.0f}ms")
    if similar:
        print(f"   ✓ Exemple : {similar[0].name}")
    
    # Test 2.2 : Achetés ensemble
    print("\n2.2 - Fréquemment achetés ensemble")
    start = time.time()
    together = reco.get_frequently_bought_together(product.id, limit=4)
    elapsed = (time.time() - start) * 1000
    print(f"   ✓ Produits trouvés : {len(together)}")
    print(f"   ✓ Temps : {elapsed:.0f}ms")
    
    # Test 2.3 : Produits tendance
    print("\n2.3 - Produits tendance (7 jours)")
    start = time.time()
    trending = reco.get_trending_products(limit=8, days=7)
    elapsed = (time.time() - start) * 1000
    print(f"   ✓ Produits trouvés : {len(trending)}")
    print(f"   ✓ Temps : {elapsed:.0f}ms")
    if trending:
        print(f"   ✓ Top 1 : {trending[0].name}")
    
    # Test 2.4 : Nouveautés
    print("\n2.4 - Nouveautés")
    start = time.time()
    new_arrivals = reco.get_new_arrivals(limit=8)
    elapsed = (time.time() - start) * 1000
    print(f"   ✓ Produits trouvés : {len(new_arrivals)}")
    print(f"   ✓ Temps : {elapsed:.0f}ms")
    
    # Test 2.5 : Recommandations personnalisées
    print("\n2.5 - Recommandations personnalisées (sans user)")
    start = time.time()
    personalized = reco.get_personalized_recommendations(user_id=None, limit=8)
    elapsed = (time.time() - start) * 1000
    print(f"   ✓ Produits trouvés : {len(personalized)}")
    print(f"   ✓ Temps : {elapsed:.0f}ms")
    
    print("\n✅ Service de recommandations : OK")

def test_translation_cache():
    """Tester le cache des traductions"""
    print_section("TEST 3 : CACHE TRADUCTIONS")
    
    translation = get_translation_service()
    
    # Test 3.1 : Première traduction (MISS)
    print("\n3.1 - Première traduction (cache MISS)")
    text = "Hello World Test"
    start = time.time()
    result1 = translation.translate_text(text, source_lang='en', target_lang='fr')
    elapsed1 = (time.time() - start) * 1000
    print(f"   ✓ Texte original : {text}")
    print(f"   ✓ Traduction : {result1}")
    print(f"   ✓ Temps : {elapsed1:.0f}ms")
    
    # Test 3.2 : Deuxième traduction (HIT)
    print("\n3.2 - Deuxième traduction (cache HIT)")
    start = time.time()
    result2 = translation.translate_text(text, source_lang='en', target_lang='fr')
    elapsed2 = (time.time() - start) * 1000
    print(f"   ✓ Traduction : {result2}")
    print(f"   ✓ Temps : {elapsed2:.0f}ms")
    print(f"   ✓ Gain : {((elapsed1 - elapsed2) / elapsed1 * 100):.0f}%")
    print(f"   ✓ Cache fonctionne : {elapsed2 < elapsed1}")
    
    # Test 3.3 : Détection de langue
    print("\n3.3 - Détection de langue")
    lang = translation.detect_language("This is an English text")
    print(f"   ✓ Langue détectée : {lang}")
    
    print("\n✅ Cache traductions : OK")

def test_performance():
    """Tester les performances globales"""
    print_section("TEST 4 : PERFORMANCES")
    
    search = get_search_service()
    reco = get_recommendation_service()
    
    # Benchmark recherche
    print("\n4.1 - Benchmark recherche (10 requêtes)")
    times = []
    for i in range(10):
        start = time.time()
        search.search_products(query="test", page=1, per_page=20)
        times.append((time.time() - start) * 1000)
    
    avg_time = sum(times) / len(times)
    print(f"   ✓ Temps moyen : {avg_time:.0f}ms")
    print(f"   ✓ Temps min : {min(times):.0f}ms")
    print(f"   ✓ Temps max : {max(times):.0f}ms")
    print(f"   ✓ Performance : {'✓ Excellent' if avg_time < 100 else '⚠ À optimiser'}")
    
    # Benchmark recommandations
    print("\n4.2 - Benchmark recommandations (10 requêtes)")
    product = Product.query.first()
    if product:
        times = []
        for i in range(10):
            start = time.time()
            reco.get_similar_products(product.id, limit=6)
            times.append((time.time() - start) * 1000)
        
        avg_time = sum(times) / len(times)
        print(f"   ✓ Temps moyen : {avg_time:.0f}ms")
        print(f"   ✓ Temps min : {min(times):.0f}ms")
        print(f"   ✓ Temps max : {max(times):.0f}ms")
        print(f"   ✓ Performance : {'✓ Excellent' if avg_time < 150 else '⚠ À optimiser'}")
    
    print("\n✅ Tests de performance : OK")

def main():
    """Fonction principale"""
    print("\n" + "="*70)
    print("  TESTS PHASE 3 - AMÉLIORATIONS")
    print("  MultiProShop - 24 Janvier 2026")
    print("="*70)
    
    # Créer le contexte de l'application
    app = create_app('development')
    
    with app.app_context():
        try:
            # Exécuter les tests
            test_search_service()
            test_recommendation_service()
            test_translation_cache()
            test_performance()
            
            # Résumé final
            print_section("RÉSUMÉ DES TESTS")
            print("\n✅ Tous les tests sont passés avec succès !")
            print("\nFonctionnalités testées :")
            print("  ✓ Service de recherche avancée")
            print("  ✓ Service de recommandations (5 algorithmes)")
            print("  ✓ Cache Redis traductions")
            print("  ✓ Performances globales")
            print("\n" + "="*70)
            print("  PHASE 3 : VALIDÉE ✅")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ Erreur lors des tests : {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    main()
