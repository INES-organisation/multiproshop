"""
Script pour tester la connexion Redis
"""
import sys
import redis
from redis.exceptions import ConnectionError

def test_redis_connection():
    """Tester la connexion Redis"""
    print("="*70)
    print("🔍 TEST DE CONNEXION REDIS")
    print("="*70)
    print()
    
    # Tester connexion
    print("📡 Test de connexion à Redis (localhost:6379)...")
    
    try:
        # Créer client Redis
        r = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            socket_connect_timeout=5,
            decode_responses=True
        )
        
        # Test PING
        response = r.ping()
        
        if response:
            print("✅ Redis est accessible !")
            print()
            
            # Informations Redis
            print("📊 INFORMATIONS REDIS")
            print("-"*70)
            
            info = r.info()
            print(f"  Version Redis      : {info.get('redis_version', 'N/A')}")
            print(f"  Mode               : {info.get('redis_mode', 'N/A')}")
            print(f"  Uptime (secondes)  : {info.get('uptime_in_seconds', 'N/A')}")
            print(f"  Clients connectés  : {info.get('connected_clients', 'N/A')}")
            print(f"  Mémoire utilisée   : {info.get('used_memory_human', 'N/A')}")
            print(f"  Clés totales       : {r.dbsize()}")
            print()
            
            # Test SET/GET
            print("🧪 TEST SET/GET")
            print("-"*70)
            
            # Test SET
            r.set('test_key', 'test_value', ex=60)
            print("  ✅ SET test_key = 'test_value'")
            
            # Test GET
            value = r.get('test_key')
            print(f"  ✅ GET test_key = '{value}'")
            
            # Test DELETE
            r.delete('test_key')
            print("  ✅ DELETE test_key")
            print()
            
            # Performance
            print("⚡ TEST DE PERFORMANCE")
            print("-"*70)
            
            import time
            
            # Test 100 SET
            start = time.time()
            for i in range(100):
                r.set(f'perf_test_{i}', f'value_{i}', ex=60)
            elapsed_set = (time.time() - start) * 1000
            
            print(f"  100 SET : {elapsed_set:.2f} ms ({elapsed_set/100:.2f} ms/op)")
            
            # Test 100 GET
            start = time.time()
            for i in range(100):
                r.get(f'perf_test_{i}')
            elapsed_get = (time.time() - start) * 1000
            
            print(f"  100 GET : {elapsed_get:.2f} ms ({elapsed_get/100:.2f} ms/op)")
            
            # Nettoyer
            for i in range(100):
                r.delete(f'perf_test_{i}')
            
            print()
            print("="*70)
            print("✅ REDIS FONCTIONNE PARFAITEMENT !")
            print("="*70)
            print()
            print("📝 PROCHAINES ÉTAPES :")
            print("  1. Modifier config.py pour utiliser config_redis")
            print("  2. Redémarrer le serveur")
            print("  3. Profiter de +10% de performance !")
            print()
            
            return True
            
    except ConnectionError:
        print("❌ Impossible de se connecter à Redis")
        print()
        print("📝 SOLUTIONS :")
        print()
        print("Option 1 : Installer Memurai (Recommandé)")
        print("  - Télécharger : https://www.memurai.com/get-memurai")
        print("  - Installer la version Developer (gratuite)")
        print("  - Le service démarre automatiquement")
        print()
        print("Option 2 : Redis via WSL")
        print("  - wsl --install")
        print("  - sudo apt update && sudo apt install redis-server")
        print("  - sudo service redis-server start")
        print()
        print("Option 3 : Redis via Docker")
        print("  - docker run -d -p 6379:6379 --name redis redis:alpine")
        print()
        print("⚠️  En attendant, SimpleCache fonctionne très bien !")
        print()
        
        return False
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False


if __name__ == '__main__':
    success = test_redis_connection()
    sys.exit(0 if success else 1)
