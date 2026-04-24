"""
Vérifier le statut de l'API CJ et du cache token
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_providers.cj_dropshipping_optimized import _memory_cache
import time
from datetime import datetime

def check_status():
    """Vérifier le statut du cache CJ"""
    print("\n" + "="*70)
    print("STATUT API CJ DROPSHIPPING")
    print("="*70 + "\n")
    
    # Vérifier rate limit
    if _memory_cache['rate_limit_until'] > time.time():
        remaining = int(_memory_cache['rate_limit_until'] - time.time())
        minutes = remaining // 60
        seconds = remaining % 60
        print(f"⏳ RATE LIMIT ACTIF")
        print(f"   Attendre encore : {minutes}m {seconds}s")
        print(f"   Disponible à : {datetime.fromtimestamp(_memory_cache['rate_limit_until']).strftime('%H:%M:%S')}")
    else:
        print("✓ Pas de rate limit - API disponible")
    
    print()
    
    # Vérifier token
    if _memory_cache['access_token']:
        if _memory_cache['token_expires_at'] > time.time():
            remaining = int(_memory_cache['token_expires_at'] - time.time())
            hours = remaining // 3600
            print(f"✓ Token valide")
            print(f"   Expire dans : {hours}h")
        else:
            print("⚠ Token expiré - sera rafraîchi")
    else:
        print("ℹ Aucun token en cache")
    
    print("\n" + "="*70)
    
    # Conseil
    if _memory_cache['rate_limit_until'] > time.time():
        print("\n💡 CONSEIL :")
        print("   Le rate limiting CJ est de 1 requête toutes les 5 minutes.")
        print("   C'est normal. Attends quelques minutes et réessaie.")
        print("\n   Ou utilise le bouton 'Synchroniser depuis CJ' dans l'interface")
        print("   web qui gère automatiquement l'attente.")
    
    print()

if __name__ == '__main__':
    check_status()
