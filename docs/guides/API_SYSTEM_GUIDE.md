# 🔌 SYSTÈME DE GESTION D'API MULTI-PARTENAIRES

## 📋 VUE D'ENSEMBLE

Le système permet d'intégrer plusieurs plateformes partenaires (CJ Dropshipping, Printify, Amazon, eBay, etc.) pour :
- ✅ Importer automatiquement leurs produits
- ✅ Mapper les catégories externes vers vos catégories MPS
- ✅ Synchroniser les stocks en temps réel
- ✅ Gérer les commandes affiliées
- ✅ Appliquer des marges personnalisées

---

## 🏗️ ARCHITECTURE

### **Modèles Créés**

1. **ApiProvider** - Fournisseur d'API
   - Informations (nom, slug, type, logo)
   - Configuration API (endpoint, version, auth)
   - Credentials (api_key, api_secret, tokens)
   - Statistiques (produits importés, revenus)

2. **CategoryMapping** - Mapping de catégories
   - Catégorie externe → Catégorie MPS
   - Configuration (auto_import, marge)

3. **ProductSource** - Lien produit MPS ↔ Produit externe
   - IDs externes (product_id, variant_id, SKU)
   - Prix et stock externes
   - Données brutes (JSON)
   - Statut de synchronisation

4. **ApiSyncLog** - Journal des synchronisations
   - Type de sync (products, categories, stock, orders)
   - Résultats (créés, mis à jour, échecs)
   - Durée et erreurs

### **Services Créés**

1. **BaseApiProvider** - Classe abstraite de base
   - Gestion des requêtes HTTP
   - Rate limiting
   - Méthodes abstraites à implémenter

2. **CJDropshippingProvider** - Intégration CJ Dropshipping
   - Authentification par signature MD5
   - Récupération produits/catégories
   - Création de commandes
   - Suivi de stock

3. **PrintifyProvider** - Intégration Printify (POD)
   - Authentification Bearer token
   - Gestion blueprints
   - Stock illimité (Print on Demand)
   - Création de commandes POD

---

## 🚀 UTILISATION

### **1. Ajouter un Provider**

#### Via l'interface Admin

1. Allez sur : `http://multiproshop.local/admin/api/providers`
2. Cliquez sur "Ajouter un Provider"
3. Choisissez un template (CJ Dropshipping, Printify, etc.)
4. Remplissez les informations :
   - **Nom** : CJ Dropshipping
   - **Slug** : cj-dropshipping
   - **Type** : dropshipping
   - **API Key** : Votre clé API
   - **API Secret** : Votre clé secrète

#### Providers Supportés

| Provider | Type | Documentation |
|----------|------|---------------|
| **CJ Dropshipping** | Dropshipping | https://developers.cjdropshipping.com/ |
| **Printify** | Print on Demand | https://developers.printify.com/ |
| **Amazon** | Marketplace | À implémenter |
| **eBay** | Marketplace | À implémenter |

### **2. Tester la Connexion**

1. Dans la liste des providers, cliquez sur l'icône 🔌
2. Le système teste l'API
3. Statut mis à jour : ✅ Connecté ou ❌ Erreur

### **3. Mapper les Catégories**

1. Cliquez sur l'icône 🗺️ (Sitemap)
2. Le système récupère les catégories du provider
3. Associez chaque catégorie externe à une catégorie MPS :
   - **Catégorie externe** : Electronics > Phones
   - **Catégorie MPS** : Électronique
   - **Auto-import** : ✅ Oui
   - **Marge** : 1.3 (= +30%)

### **4. Synchroniser les Produits**

1. Cliquez sur l'icône 🔄 (Sync)
2. Le système :
   - Récupère les produits des catégories mappées
   - Applique la marge configurée
   - Crée/met à jour les produits MPS
   - Enregistre la source externe

**Exemple** :
```
Produit CJ : iPhone Case - 5.00 USD
Marge : 1.3 (30%)
Prix MPS : 6.50 EUR
```

---

## 💻 UTILISATION PROGRAMMATIQUE

### **Créer un Provider via Code**

```python
from models.api_provider import ApiProvider
from extensions import db

# Créer CJ Dropshipping
cj = ApiProvider(
    name='CJ Dropshipping',
    slug='cj-dropshipping',
    provider_type='dropshipping',
    api_endpoint='https://developers.cjdropshipping.com/api2.0/v1',
    api_version='v1',
    auth_type='signature',
    api_key='votre_email@example.com',
    api_secret='votre_cle_secrete',
    is_active=True
)

db.session.add(cj)
db.session.commit()
```

### **Tester la Connexion**

```python
from services.api_providers import CJDropshippingProvider

provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
service = CJDropshippingProvider(provider)

if service.test_connection():
    print("✅ Connexion réussie !")
    provider.is_connected = True
    db.session.commit()
```

### **Récupérer les Produits**

```python
# Récupérer les produits d'une catégorie
result = service.get_products(category_id='12345', page=1, limit=50)

for product in result['products']:
    print(f"{product['name']} - {product['price']} {product['currency']}")
```

### **Synchroniser un Produit**

```python
from routes.api_management import create_product_from_source

# Récupérer un mapping
mapping = CategoryMapping.query.filter_by(
    provider_id=provider.id,
    external_category_id='12345'
).first()

# Récupérer les détails du produit
product_data = service.get_product_details('PROD-123')

# Créer le produit MPS
mps_product = create_product_from_source(provider, product_data, mapping)
```

---

## 🔧 AJOUTER UN NOUVEAU PROVIDER

### **Étape 1 : Créer le Service**

Créez `services/api_providers/mon_provider.py` :

```python
from .base_provider import BaseApiProvider

class MonProviderService(BaseApiProvider):
    
    def test_connection(self) -> bool:
        # Tester l'API
        try:
            response = self._make_request('GET', 'test')
            return response.get('status') == 'ok'
        except:
            return False
    
    def get_categories(self) -> List[Dict]:
        # Récupérer les catégories
        response = self._make_request('GET', 'categories')
        return response.get('data', [])
    
    def get_products(self, category_id=None, page=1, limit=50) -> Dict:
        # Récupérer les produits
        params = {'page': page, 'limit': limit}
        if category_id:
            params['category'] = category_id
        
        response = self._make_request('GET', 'products', params=params)
        
        return {
            'products': [self._format_product(p) for p in response['data']],
            'pagination': response['pagination']
        }
    
    def get_product_details(self, product_id: str) -> Dict:
        # Détails d'un produit
        response = self._make_request('GET', f'products/{product_id}')
        return self._format_product(response['data'])
    
    def get_product_stock(self, product_id: str, variant_id=None) -> int:
        # Stock du produit
        response = self._make_request('GET', f'products/{product_id}/stock')
        return response.get('stock', 0)
    
    def create_order(self, order_data: Dict) -> Dict:
        # Créer une commande
        response = self._make_request('POST', 'orders', json=order_data)
        return {
            'success': True,
            'order_id': response['id']
        }
    
    def get_order_status(self, order_id: str) -> Dict:
        # Statut de la commande
        response = self._make_request('GET', f'orders/{order_id}')
        return response['data']
    
    def _format_product(self, raw_data: Dict) -> Dict:
        # Formater en format MPS
        return {
            'external_id': raw_data['id'],
            'name': raw_data['title'],
            'description': raw_data['description'],
            'price': float(raw_data['price']),
            'stock': raw_data['quantity'],
            'images': raw_data['images'],
            'raw_data': raw_data
        }
```

### **Étape 2 : Enregistrer le Service**

Dans `services/api_providers/__init__.py` :

```python
from .mon_provider import MonProviderService

__all__ = [
    'BaseApiProvider',
    'CJDropshippingProvider',
    'PrintifyProvider',
    'MonProviderService'  # Ajouter ici
]
```

### **Étape 3 : Ajouter dans get_provider_service**

Dans `routes/api_management.py` :

```python
def get_provider_service(provider):
    if provider.slug == 'cj-dropshipping':
        return CJDropshippingProvider(provider)
    elif provider.slug == 'printify':
        return PrintifyProvider(provider)
    elif provider.slug == 'mon-provider':  # Ajouter ici
        return MonProviderService(provider)
    else:
        raise Exception(f"Provider {provider.slug} non supporté")
```

---

## 📊 FONCTIONNALITÉS AVANCÉES

### **1. Synchronisation Automatique**

Créez un cron job pour synchroniser régulièrement :

```python
# sync_cron.py
from app import create_app
from models.api_provider import ApiProvider, CategoryMapping
from routes.api_management import get_provider_service, update_product_from_source

app = create_app()

with app.app_context():
    providers = ApiProvider.query.filter_by(is_active=True).all()
    
    for provider in providers:
        service = get_provider_service(provider)
        
        # Synchroniser les stocks
        sources = ProductSource.query.filter_by(provider_id=provider.id).all()
        for source in sources:
            service.sync_product_stock(source)
```

### **2. Webhooks**

Recevez les mises à jour en temps réel :

```python
@api_mgmt_bp.route('/webhook/<provider_slug>', methods=['POST'])
def webhook(provider_slug):
    provider = ApiProvider.query.filter_by(slug=provider_slug).first_or_404()
    data = request.json
    
    # Traiter selon le type d'événement
    if data['event'] == 'product.updated':
        # Mettre à jour le produit
        pass
    elif data['event'] == 'stock.changed':
        # Mettre à jour le stock
        pass
    
    return jsonify({'status': 'ok'})
```

### **3. Traduction Automatique**

Intégrez Google Translate ou DeepL :

```python
from googletrans import Translator

def translate_product_data(product_data, target_lang='fr'):
    translator = Translator()
    
    product_data['name'] = translator.translate(
        product_data['name'],
        dest=target_lang
    ).text
    
    product_data['description'] = translator.translate(
        product_data['description'],
        dest=target_lang
    ).text
    
    return product_data
```

---

## 🎯 EXEMPLES D'UTILISATION

### **Scénario 1 : Dropshipping avec CJ**

1. Configurez CJ Dropshipping
2. Mappez "Electronics" → "Électronique"
3. Synchronisez les produits
4. Un client commande un iPhone Case
5. Le système crée automatiquement la commande chez CJ
6. CJ expédie directement au client

### **Scénario 2 : Print on Demand avec Printify**

1. Configurez Printify
2. Mappez "T-Shirts" → "Vêtements"
3. Synchronisez les designs
4. Un client commande un T-shirt personnalisé
5. Printify imprime et expédie

### **Scénario 3 : Affiliation Amazon**

1. Configurez Amazon Product Advertising API
2. Mappez les catégories
3. Importez les produits avec liens affiliés
4. Gagnez des commissions sur les ventes

---

## 📝 TODO / AMÉLIORATIONS

- [ ] Ajouter Amazon Product Advertising API
- [ ] Ajouter eBay API
- [ ] Ajouter AliExpress Dropshipping
- [ ] Traduction automatique (Google Translate/DeepL)
- [ ] Synchronisation automatique par cron
- [ ] Webhooks pour mises à jour temps réel
- [ ] Gestion des variantes produits
- [ ] Import d'images multiples
- [ ] Gestion des devises (conversion automatique)
- [ ] Dashboard analytics par provider

---

## 🆘 DÉPANNAGE

### Erreur : "Provider non supporté"

Vérifiez que le slug correspond exactement dans `get_provider_service()`.

### Erreur : "Quota journalier atteint"

Augmentez `daily_quota` ou attendez le lendemain.

### Produits non importés

1. Vérifiez que le mapping existe
2. Vérifiez que `auto_import = True`
3. Vérifiez les logs de sync

### Stock non synchronisé

Vérifiez que `ProductSource.is_active = True`.

---

*Guide créé le 23/11/2025*
