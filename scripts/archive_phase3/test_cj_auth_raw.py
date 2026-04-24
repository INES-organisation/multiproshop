"""
Test authentification CJ avec requête brute
"""
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

print("\n" + "="*70)
print("TEST AUTHENTIFICATION CJ - REQUETE BRUTE")
print("="*70 + "\n")

email = os.getenv('CJ_EMAIL')
password = os.getenv('CJ_PASSWORD')

print(f"Email: {email}")
print(f"Password: {'*' * len(password)}\n")

# Test 1: Sans dev_key
print("Test 1: Authentification SANS dev_key")
url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"

payload = {
    "email": email,
    "password": password
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers, verify=False)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}\n")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('result'):
            print("[OK] Authentification reussie !")
            token = data['data']['accessToken']
            print(f"Token: {token[:50]}...")
        else:
            print(f"[ERREUR] {data.get('message')}")
    else:
        print(f"[ERREUR] HTTP {response.status_code}")
        
except Exception as e:
    print(f"[EXCEPTION] {e}")

print("\n" + "="*70)
