"""
Script pour exécuter les tests de performance et générer un rapport
"""
import subprocess
import sys
import time
from pathlib import Path

def run_tests():
    """Exécuter les tests de performance"""
    print("\n" + "="*70)
    print("TESTS DE PERFORMANCE AUTOMATISÉS")
    print("="*70 + "\n")
    
    # Vérifier si pytest est installé
    try:
        import pytest
    except ImportError:
        print("❌ pytest n'est pas installé")
        print("📦 Installez-le avec: pip install pytest")
        return False
    
    # Exécuter les tests
    print("🧪 Exécution des tests...\n")
    
    test_file = Path(__file__).parent.parent / 'tests' / 'test_performance.py'
    
    if not test_file.exists():
        print(f"❌ Fichier de test introuvable: {test_file}")
        return False
    
    # Exécuter pytest avec options
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', str(test_file), '-v', '--tb=short'],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if result.returncode == 0:
        print("\n" + "="*70)
        print("✅ TOUS LES TESTS SONT PASSÉS")
        print("="*70)
        print("\n✅ Les optimisations sont maintenues")
        print("✅ Les performances sont conformes aux attentes\n")
        return True
    else:
        print("\n" + "="*70)
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("="*70)
        print("\n⚠️  Des problèmes de performance ont été détectés")
        print("📋 Consultez les détails ci-dessus\n")
        return False

def run_load_test():
    """Exécuter un test de charge simple"""
    print("\n" + "="*70)
    print("TEST DE CHARGE SIMPLE")
    print("="*70 + "\n")
    
    try:
        import requests
    except ImportError:
        print("❌ requests n'est pas installé")
        print("📦 Installez-le avec: pip install requests")
        return
    
    url = 'http://localhost:5000'
    num_requests = 100
    
    print(f"🔄 Envoi de {num_requests} requêtes à {url}...\n")
    
    times = []
    errors = 0
    
    for i in range(num_requests):
        try:
            start = time.time()
            response = requests.get(url, timeout=5)
            duration = time.time() - start
            
            if response.status_code == 200:
                times.append(duration)
            else:
                errors += 1
            
            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{num_requests} requêtes...")
        
        except Exception as e:
            errors += 1
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print("\n" + "="*70)
        print("RÉSULTATS DU TEST DE CHARGE")
        print("="*70)
        print(f"\n📊 Statistiques:")
        print(f"   - Requêtes réussies: {len(times)}/{num_requests}")
        print(f"   - Erreurs: {errors}")
        print(f"   - Temps moyen: {avg_time*1000:.2f}ms")
        print(f"   - Temps min: {min_time*1000:.2f}ms")
        print(f"   - Temps max: {max_time*1000:.2f}ms")
        
        if avg_time < 0.5:
            print("\n✅ Performances excellentes !")
        elif avg_time < 1.0:
            print("\n✅ Performances bonnes")
        else:
            print("\n⚠️  Performances à améliorer")
        
        print()

def main():
    """Fonction principale"""
    print("\n🚀 Lancement des tests de performance...\n")
    
    # Tests unitaires
    tests_passed = run_tests()
    
    # Test de charge (optionnel)
    print("\n💡 Voulez-vous exécuter un test de charge ? (y/n)")
    print("   Note: Le serveur doit être en cours d'exécution sur localhost:5000")
    
    # Pour l'automatisation, on skip le test de charge
    # Décommentez pour l'activer:
    # run_load_test()
    
    if tests_passed:
        print("\n🎉 Tous les tests sont passés avec succès !")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué")
        return 1

if __name__ == '__main__':
    sys.exit(main())
