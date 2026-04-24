"""
Script de test pour les webhooks CJ Dropshipping
Permet de simuler l'envoi de webhooks depuis CJ
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
WEBHOOK_URL = f"{BASE_URL}/webhooks/cj/message"


def test_webhook_endpoint():
    """Tester que l'endpoint webhook est accessible"""
    print("\n" + "="*70)
    print("TEST 1: Vérification endpoint webhook")
    print("="*70)
    
    try:
        response = requests.get(f"{WEBHOOK_URL}/test")
        
        if response.status_code == 200:
            print("✅ Endpoint accessible")
            print(f"   Réponse: {response.json()}")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False


def test_order_shipped_webhook():
    """Tester le webhook de mise à jour commande (format CJ réel)"""
    print("\n" + "="*70)
    print("TEST 2: Webhook ORDER (SHIPPED)")
    print("="*70)
    
    payload = {
        "messageId": "test_msg_001",
        "type": "ORDER",
        "messageType": "UPDATE",
        "params": {
            "orderNumber": "api_test_123",
            "cjOrderId": 123456789,
            "orderStatus": "SHIPPED",
            "logisticName": "DHL Express",
            "trackNumber": "TRACK-TEST-123",
            "createDate": "2026-01-24 00:00:00",
            "updateDate": "2026-01-24 00:00:00"
        }
    }
    
    try:
        response = requests.post(
            f"{WEBHOOK_URL}/order",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Réponse: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Webhook traité avec succès")
            return True
        else:
            print("⚠️ Webhook traité avec erreur")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_order_delivered_webhook():
    """Tester le webhook de livraison (format CJ réel)"""
    print("\n" + "="*70)
    print("TEST 3: Webhook ORDER (DELIVERED)")
    print("="*70)
    
    payload = {
        "messageId": "test_msg_002",
        "type": "ORDER",
        "messageType": "UPDATE",
        "params": {
            "orderNumber": "api_test_123",
            "cjOrderId": 123456789,
            "orderStatus": "DELIVERED",
            "deliveryDate": "2026-01-24 12:00:00"
        }
    }
    
    try:
        response = requests.post(
            f"{WEBHOOK_URL}/order",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Réponse: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Webhook traité avec succès")
            return True
        else:
            print("⚠️ Webhook traité avec erreur")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_order_cancelled_webhook():
    """Tester le webhook d'annulation (format CJ réel)"""
    print("\n" + "="*70)
    print("TEST 4: Webhook ORDER (CANCELLED)")
    print("="*70)
    
    payload = {
        "messageId": "test_msg_003",
        "type": "ORDER",
        "messageType": "UPDATE",
        "params": {
            "orderNumber": "api_test_123",
            "cjOrderId": 123456789,
            "orderStatus": "CANCELLED"
        }
    }
    
    try:
        response = requests.post(
            f"{WEBHOOK_URL}/order",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Réponse: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Webhook traité avec succès")
            return True
        else:
            print("⚠️ Webhook traité avec erreur")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_stock_updated_webhook():
    """Tester le webhook de mise à jour de stock (format CJ réel)"""
    print("\n" + "="*70)
    print("TEST 5: Webhook STOCK")
    print("="*70)
    
    payload = {
        "messageId": "test_msg_004",
        "type": "STOCK",
        "messageType": "UPDATE",
        "params": {
            "CJ-VAR-TEST-456": [
                {
                    "vid": "CJ-VAR-TEST-456",
                    "areaId": "2",
                    "areaEn": "US Warehouse",
                    "countryCode": "US",
                    "storageNum": 50
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Réponse: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Webhook traité avec succès")
            return True
        else:
            print("⚠️ Webhook traité avec erreur")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_webhook_logs():
    """Tester l'accès aux logs des webhooks"""
    print("\n" + "="*70)
    print("TEST 6: Accès aux logs webhooks")
    print("="*70)
    
    try:
        # Note: Nécessite authentification admin
        response = requests.get(f"{WEBHOOK_URL}/logs?limit=5")
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data.get('count', 0)} logs récupérés")
            return True
        elif response.status_code == 403:
            print("⚠️ Authentification admin requise (normal)")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_webhook_stats():
    """Tester l'accès aux statistiques des webhooks"""
    print("\n" + "="*70)
    print("TEST 7: Statistiques webhooks")
    print("="*70)
    
    try:
        # Note: Nécessite authentification admin
        response = requests.get(f"{WEBHOOK_URL}/stats")
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            print(f"✅ Statistiques récupérées:")
            print(f"   Total: {stats.get('total', 0)}")
            print(f"   Succès: {stats.get('success', 0)}")
            print(f"   Erreurs: {stats.get('errors', 0)}")
            return True
        elif response.status_code == 403:
            print("⚠️ Authentification admin requise (normal)")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def run_all_tests():
    """Exécuter tous les tests"""
    print("\n" + "="*70)
    print("🧪 TESTS WEBHOOKS CJ DROPSHIPPING")
    print("="*70)
    print(f"URL: {BASE_URL}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Exécuter les tests
    results.append(("Endpoint accessible", test_webhook_endpoint()))
    results.append(("Webhook order.shipped", test_order_shipped_webhook()))
    results.append(("Webhook order.delivered", test_order_delivered_webhook()))
    results.append(("Webhook order.cancelled", test_order_cancelled_webhook()))
    results.append(("Webhook stock.updated", test_stock_updated_webhook()))
    results.append(("Logs webhooks", test_webhook_logs()))
    results.append(("Statistiques webhooks", test_webhook_stats()))
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "-"*70)
    print(f"Résultat: {passed}/{total} tests réussis ({passed/total*100:.1f}%)")
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
