"""
Test simple de l'authentification CJ
"""
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

email = os.getenv('CJ_EMAIL')
password = os.getenv('CJ_PASSWORD')
dev_key = os.getenv('CJ_DEV_KEY')

print(f"Email: {email}")
print(f"Password: {'*' * len(password) if password else 'VIDE'}")
print(f"Dev Key: {'*' * len(dev_key) if dev_key else 'VIDE'}")

url = 'https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken'

headers = {
    'Content-Type': 'application/json'
}

if dev_key:
    headers['CJ-DEV-KEY'] = dev_key

auth_data = {
    'email': email,
    'password': password
}

print(f"\nURL: {url}")
print(f"Headers: {headers}")
print(f"Data: {json.dumps(auth_data, indent=2)}")

response = requests.post(
    url,
    json=auth_data,
    headers=headers,
    verify=False,
    timeout=30
)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")

try:
    data = response.json()
    print(f"\nJSON: {json.dumps(data, indent=2)}")
except:
    print("\nErreur parsing JSON")
