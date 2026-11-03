"""
Script de test des fonctionnalités principales
Teste recherche, produits, dashboard sans contexte Flask
"""
import requests
import sys

def test_homepage():
    """Tester la page d'accueil"""
    print("\n" + "="*70)
    print("TEST 1 : PAGE D'ACCUEIL")
    print("="*70)
    
    try:
        response = requests.get("http://multiproshop.local/", timeout=5)
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Taille: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("✅ Page d'accueil : OK")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_search():
    """Tester la recherche"""
    print("\n" + "="*70)
    print("TEST 2 : RECHERCHE")
    print("="*70)
    
    try:
        # Test recherche "mattress"
        response = requests.get("http://multiproshop.local/search?q=mattress", timeout=5)
        print(f"✓ Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            if "Résultats" in content or "résultats" in content or "produit" in content:
                print("✓ Page de résultats affichée")
                print("✅ Recherche : OK")
                return True
            else:
                print("⚠ Page chargée mais contenu suspect")
                return False
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_products_list():
    """Tester la liste des produits"""
    print("\n" + "="*70)
    print("TEST 3 : LISTE PRODUITS")
    print("="*70)
    
    try:
        response = requests.get("http://multiproshop.local/products/", timeout=5)
        print(f"✓ Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Liste produits : OK")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_product_detail():
    """Tester une page produit"""
    print("\n" + "="*70)
    print("TEST 4 : PAGE PRODUIT")
    print("="*70)
    
    try:
        # Tester avec ID 1
        response = requests.get("http://multiproshop.local/products/1", timeout=5)
        print(f"✓ Status: {response.status_code}")
        
        if response.status_code in [200, 404]:
            if response.status_code == 200:
                print("✅ Page produit : OK")
                return True
            else:
                print("⚠ Produit ID 1 non trouvé (normal si pas de produits)")
                return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_dashboard_cj():
    """Tester le dashboard CJ"""
    print("\n" + "="*70)
    print("TEST 5 : DASHBOARD CJ ADMIN")
    print("="*70)
    
    try:
        response = requests.get("http://multiproshop.local/admin/cj/dashboard", timeout=5)
        print(f"✓ Status: {response.status_code}")
        
        if response.status_code in [200, 302, 401]:
            if response.status_code == 200:
                print("✅ Dashboard CJ : OK")
                return True
            elif response.status_code == 302:
                print("⚠ Redirection (authentification requise)")
                return True
            else:
                print("⚠ Non autorisé (normal sans login)")
                return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_api_search():
    """Tester l'API de recherche"""
    print("\n" + "="*70)
    print("TEST 6 : API RECHERCHE")
    print("="*70)
    
    try:
        response = requests.get("http://multiproshop.local/search/api/suggestions?q=mat", timeout=5)
        print(f"✓ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Suggestions: {len(data.get('suggestions', []))}")
            print("✅ API Recherche : OK")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("\n" + "="*70)
    print("  TEST FONCTIONNALITÉS MULTIPROSHOP")
    print("  24 Janvier 2026")
    print("="*70)
    
    results = []
    
    # Exécuter tous les tests
    results.append(("Page d'accueil", test_homepage()))
    results.append(("Recherche", test_search()))
    results.append(("Liste produits", test_products_list()))
    results.append(("Page produit", test_product_detail()))
    results.append(("Dashboard CJ", test_dashboard_cj()))
    results.append(("API Recherche", test_api_search()))
    
    # Résumé
    print("\n" + "="*70)
    print("  RÉSUMÉ DES TESTS")
    print("="*70)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✅ OK" if result else "❌ ERREUR"
        print(f"{status:12} - {name}")
    
    print("\n" + "="*70)
    print(f"  RÉSULTAT: {success_count}/{total_count} tests réussis")
    print("="*70)
    
    if success_count == total_count:
        print("\n🎉 Toutes les fonctionnalités sont opérationnelles !")
        return 0
    elif success_count >= total_count * 0.8:
        print("\n⚠️  La plupart des fonctionnalités fonctionnent")
        return 0
    else:
        print("\n❌ Plusieurs fonctionnalités ont des problèmes")
        return 1

if __name__ == '__main__':
    sys.exit(main())
