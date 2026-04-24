# 🚀 GUIDE DES FONCTIONNALITÉS AVANCÉES

## 📋 VUE D'ENSEMBLE

Ce guide couvre les fonctionnalités avancées du système API :
- ✅ **Amazon Product Advertising API** (Affiliation)
- ✅ **eBay Partner Network** (Affiliation)
- ✅ **Traduction Automatique** (Google Translate / DeepL)
- ✅ **Synchronisation Automatique** (Cron / Scheduler)
- ✅ **Webhooks Temps Réel** (Mises à jour instantanées)

---

## 🔌 NOUVEAUX PROVIDERS

### **1. Amazon Product Advertising API**

#### **Configuration**

1. Créez un compte Amazon Associates : https://affiliate-program.amazon.fr/
2. Inscrivez-vous à PA-API : https://webservices.amazon.com/paapi5/documentation/
3. Obtenez vos credentials :
   - **Access Key** (API Key)
   - **Secret Key** (API Secret)
   - **Associate Tag** (ID partenaire)

#### **Ajouter dans MPS**

```python
# Via l'interface admin
1. Allez sur /admin/api/providers
2. Cliquez "Ajouter un Provider"
3. Sélectionnez le template "Amazon Product Advertising"
4. Remplissez :
   - API Key: Votre Access Key
   - API Secret: Votre Secret Key
   - Config JSON: {"associate_tag": "votre-tag-20", "marketplace": "www.amazon.fr"}
```

#### **Caractéristiques**

- ✅ Affiliation (pas de dropshipping)
- ✅ Liens affiliés automatiques
- ✅ Commission sur ventes
- ⚠️ Limites strictes : 1 req/sec, 8640 req/jour
- ❌ Pas de gestion de commandes
- ❌ Pas d'info stock

#### **Exemple d'utilisation**

```python
from services.api_providers import AmazonProvider

provider = ApiProvider.query.filter_by(slug='amazon').first()
service = AmazonProvider(provider)

# Récupérer les catégories
categories = service.get_categories()

# Rechercher des produits
products = service.get_products(category_id='340858031', page=1, limit=10)

# Générer un lien affilié
affiliate_link = service._generate_affiliate_link([{'external_product_id': 'B08N5WRWNW'}])
# https://www.amazon.fr/dp/B08N5WRWNW?tag=votre-tag-20
```

---

### **2. eBay Partner Network**

#### **Configuration**

1. Créez un compte eBay Developer : https://developer.ebay.com/
2. Créez une application : https://developer.ebay.com/my/keys
3. Inscrivez-vous au Partner Network : https://partnernetwork.ebay.fr/
4. Obtenez vos credentials :
   - **Client ID** (API Key)
   - **Client Secret** (API Secret)
   - **Campaign ID** (ID campagne affiliation)

#### **Ajouter dans MPS**

```python
# Via l'interface admin
1. Allez sur /admin/api/providers
2. Cliquez "Ajouter un Provider"
3. Sélectionnez le template "eBay Partner Network"
4. Remplissez :
   - API Key: Votre Client ID
   - API Secret: Votre Client Secret
   - Config JSON: {"campaign_id": "5338xxxxx", "marketplace_id": "EBAY_FR"}
```

#### **Caractéristiques**

- ✅ Affiliation (pas de dropshipping)
- ✅ Liens affiliés automatiques
- ✅ Commission sur ventes
- ✅ Info stock disponible
- ✅ Catégories complètes
- ❌ Pas de gestion de commandes

#### **Exemple d'utilisation**

```python
from services.api_providers import EbayProvider

provider = ApiProvider.query.filter_by(slug='ebay').first()
service = EbayProvider(provider)

# Récupérer les catégories
categories = service.get_categories()

# Rechercher des produits
products = service.get_products(category_id='625', page=1, limit=50)

# Obtenir le stock
stock = service.get_product_stock('123456789012')
```

---

## 🌍 TRADUCTION AUTOMATIQUE

### **Installation**

```bash
pip install googletrans==4.0.0-rc1
# OU pour DeepL (payant)
pip install deepl==1.15.0
```

### **Configuration**

#### **Google Translate (Gratuit)**

```python
from services.translation_service import get_translation_service

# Initialiser (pas de clé API nécessaire)
translator = get_translation_service(provider='google')
```

#### **DeepL (Payant, meilleure qualité)**

```python
# Obtenez une clé API : https://www.deepl.com/pro-api
translator = get_translation_service(provider='deepl', api_key='votre-cle-deepl')
```

### **Utilisation**

#### **Traduire un texte simple**

```python
from services.translation_service import get_translation_service

translator = get_translation_service()

# Anglais → Français
text_fr = translator.translate_text(
    "iPhone 13 Pro Max Case",
    source_lang='en',
    target_lang='fr'
)
# Résultat: "Coque iPhone 13 Pro Max"
```

#### **Traduire un produit complet**

```python
product_data = {
    'name': 'Wireless Bluetooth Headphones',
    'description': 'High quality sound with noise cancellation',
    'features': ['Bluetooth 5.0', '30h battery life', 'Active noise cancellation'],
    'category_name': 'Electronics'
}

# Traduire tout
translated = translator.translate_product(product_data, source_lang='en', target_lang='fr')

print(translated['name'])  # "Casque Bluetooth Sans Fil"
print(translated['description'])  # "Son de haute qualité avec réduction de bruit"
```

#### **Détecter la langue automatiquement**

```python
lang = translator.detect_language("This is an English text")
print(lang)  # "en"
```

### **Intégration avec les Providers**

Modifiez `create_product_from_source` dans `routes/api_management.py` :

```python
from services.translation_service import get_translation_service

def create_product_from_source(provider, product_data, mapping):
    # Traduire les données
    translator = get_translation_service()
    
    # Détecter la langue source
    source_lang = translator.detect_language(product_data['name'])
    
    # Traduire si pas en français
    if source_lang != 'fr':
        product_data = translator.translate_product(
            product_data,
            source_lang=source_lang,
            target_lang='fr'
        )
    
    # Créer le produit avec données traduites
    product = Product(
        name=product_data['name'],  # Déjà traduit
        description=product_data['description'],  # Déjà traduit
        # ...
    )
```

---

## ⏰ SYNCHRONISATION AUTOMATIQUE

### **Installation**

```bash
pip install APScheduler==3.10.4
```

### **Configuration**

Le scheduler est automatiquement initialisé au démarrage de l'application.

### **Utilisation**

#### **Planifier une synchronisation quotidienne**

```python
from services.sync_scheduler import get_scheduler

scheduler = get_scheduler()

# Synchroniser tous les jours à 2h00
scheduler.add_sync_job(
    provider_id=1,
    schedule_type='daily',
    hour=2,
    minute=0
)
```

#### **Planifier une synchronisation horaire**

```python
# Synchroniser toutes les heures à la minute 0
scheduler.add_sync_job(
    provider_id=1,
    schedule_type='hourly',
    minute=0
)
```

#### **Planifier une synchronisation par intervalle**

```python
# Synchroniser toutes les 6 heures
scheduler.add_sync_job(
    provider_id=1,
    schedule_type='interval',
    interval_hours=6
)
```

#### **Synchroniser manuellement**

```python
# Synchroniser un provider spécifique
scheduler._sync_provider_task(provider_id=1)

# Synchroniser tous les providers actifs
scheduler.sync_all_active_providers()
```

#### **Supprimer une synchronisation**

```python
scheduler.remove_sync_job(provider_id=1)
```

#### **Voir les jobs planifiés**

```python
jobs = scheduler.get_jobs_status()
for job in jobs:
    print(f"{job['name']}: prochaine exécution {job['next_run']}")
```

### **Via l'Interface Admin**

Ajoutez cette route dans `routes/api_management.py` :

```python
@api_mgmt_bp.route('/providers/<int:provider_id>/schedule', methods=['POST'])
@login_required
@admin_required
def schedule_sync(provider_id):
    """Planifier la synchronisation d'un provider"""
    from services.sync_scheduler import get_scheduler
    
    schedule_type = request.form.get('schedule_type', 'daily')
    hour = int(request.form.get('hour', 2))
    minute = int(request.form.get('minute', 0))
    interval_hours = int(request.form.get('interval_hours', 6)) if schedule_type == 'interval' else None
    
    scheduler = get_scheduler()
    success = scheduler.add_sync_job(
        provider_id=provider_id,
        schedule_type=schedule_type,
        hour=hour,
        minute=minute,
        interval_hours=interval_hours
    )
    
    if success:
        flash(f'Synchronisation planifiée: {schedule_type}', 'success')
    else:
        flash('Erreur lors de la planification', 'error')
    
    return redirect(url_for('api_management.list_providers'))
```

---

## 🔔 WEBHOOKS TEMPS RÉEL

### **Configuration**

Les webhooks permettent de recevoir des mises à jour instantanées des providers.

#### **URLs des Webhooks**

```
CJ Dropshipping: https://votre-domaine.com/webhooks/cj-dropshipping
Printify: https://votre-domaine.com/webhooks/printify
eBay: https://votre-domaine.com/webhooks/ebay
Amazon: Non supporté
```

### **Configurer les Webhooks**

#### **CJ Dropshipping**

1. Connectez-vous à votre compte CJ
2. Allez dans Settings > Webhooks
3. Ajoutez l'URL : `https://votre-domaine.com/webhooks/cj-dropshipping`
4. Sélectionnez les événements :
   - `product.stock.updated`
   - `product.price.updated`
   - `order.status.updated`

#### **Printify**

1. Connectez-vous à Printify
2. Allez dans My Account > Webhooks
3. Ajoutez l'URL : `https://votre-domaine.com/webhooks/printify`
4. Sélectionnez les événements :
   - `order:sent-to-production`
   - `order:shipment:created`

#### **eBay**

1. Connectez-vous à eBay Developer
2. Allez dans Notifications
3. Configurez l'URL : `https://votre-domaine.com/webhooks/ebay`
4. Activez les notifications :
   - `ItemRevised`
   - `ItemEnded`

### **Événements Gérés**

#### **CJ Dropshipping**

| Événement | Action |
|-----------|--------|
| `product.stock.updated` | Met à jour le stock du produit MPS |
| `product.price.updated` | Met à jour le prix (avec marge) |
| `order.status.updated` | Met à jour le statut de commande |

#### **Printify**

| Événement | Action |
|-----------|--------|
| `order:sent-to-production` | Statut → "processing" |
| `order:shipment:created` | Statut → "shipped" + tracking |

#### **eBay**

| Événement | Action |
|-----------|--------|
| `ItemRevised` | Marque le produit pour resync |
| `ItemEnded` | Désactive le produit |

### **Sécurité**

Les webhooks vérifient les signatures pour éviter les faux appels :

```python
def verify_cj_signature(data, signature):
    """Vérifier la signature CJ"""
    provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
    
    expected = hmac.new(
        provider.api_secret.encode(),
        str(data).encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
```

---

## 📊 TABLEAU RÉCAPITULATIF

| Provider | Type | Traduction | Sync Auto | Webhooks | Stock | Commandes |
|----------|------|------------|-----------|----------|-------|-----------|
| **CJ Dropshipping** | Dropshipping | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Printify** | POD | ✅ | ✅ | ✅ | ✅ (∞) | ✅ |
| **Amazon** | Affiliation | ✅ | ✅ | ❌ | ❌ | ❌ |
| **eBay** | Affiliation | ✅ | ✅ | ✅ | ✅ | ❌ |

---

## 🎯 EXEMPLES COMPLETS

### **Exemple 1 : Dropshipping CJ avec Traduction et Sync Auto**

```python
from services.api_providers import CJDropshippingProvider
from services.translation_service import get_translation_service
from services.sync_scheduler import get_scheduler

# 1. Configurer le provider
provider = ApiProvider(
    name='CJ Dropshipping',
    slug='cj-dropshipping',
    provider_type='dropshipping',
    api_key='votre-email@example.com',
    api_secret='votre-cle-secrete',
    is_active=True
)
db.session.add(provider)
db.session.commit()

# 2. Mapper une catégorie
mapping = CategoryMapping(
    provider_id=provider.id,
    external_category_id='12345',
    external_category_name='Electronics',
    mps_category_id=1,
    auto_import=True,
    apply_markup=1.3
)
db.session.add(mapping)
db.session.commit()

# 3. Importer des produits avec traduction
service = CJDropshippingProvider(provider)
translator = get_translation_service()

products = service.get_products(category_id='12345', limit=50)

for product_data in products['products']:
    # Traduire
    product_data = translator.translate_product(product_data, 'en', 'fr')
    
    # Créer
    create_product_from_source(provider, product_data, mapping)

# 4. Planifier la synchronisation automatique
scheduler = get_scheduler()
scheduler.add_sync_job(
    provider_id=provider.id,
    schedule_type='daily',
    hour=2,
    minute=0
)

print("✅ CJ Dropshipping configuré avec traduction et sync auto !")
```

### **Exemple 2 : Affiliation Amazon + eBay**

```python
# Amazon
amazon = ApiProvider(
    name='Amazon Product Advertising',
    slug='amazon',
    provider_type='affiliate',
    api_key='VOTRE_ACCESS_KEY',
    api_secret='VOTRE_SECRET_KEY',
    config={'associate_tag': 'votre-tag-20', 'marketplace': 'www.amazon.fr'}
)

# eBay
ebay = ApiProvider(
    name='eBay Partner Network',
    slug='ebay',
    provider_type='affiliate',
    api_key='VOTRE_CLIENT_ID',
    api_secret='VOTRE_CLIENT_SECRET',
    config={'campaign_id': '5338xxxxx', 'marketplace_id': 'EBAY_FR'}
)

# Synchroniser toutes les 6 heures
scheduler.add_sync_job(amazon.id, 'interval', interval_hours=6)
scheduler.add_sync_job(ebay.id, 'interval', interval_hours=6)
```

---

## 🔧 DÉPANNAGE

### **Traduction ne fonctionne pas**

```bash
# Installer googletrans
pip install googletrans==4.0.0-rc1

# Tester
python -c "from googletrans import Translator; t = Translator(); print(t.translate('Hello', dest='fr').text)"
```

### **Scheduler ne démarre pas**

```python
# Vérifier
from services.sync_scheduler import get_scheduler
scheduler = get_scheduler()
print(scheduler.scheduler.running)  # Doit être True
```

### **Webhooks ne fonctionnent pas**

1. Vérifiez que votre serveur est accessible publiquement
2. Utilisez ngrok pour tester localement : `ngrok http 5000`
3. Vérifiez les logs : `tail -f app.log`

---

**Date de création** : 23/11/2025
