# 🚀 GUIDE D'INTÉGRATION CJ ORDER SERVICE
## MultiProShop - Système de Commandes CJ Dropshipping

---

## 📋 TABLE DES MATIÈRES

1. [Vue d'ensemble](#vue-densemble)
2. [Installation et Configuration](#installation-et-configuration)
3. [Migration de la Base de Données](#migration-de-la-base-de-données)
4. [Utilisation](#utilisation)
5. [Interface Admin](#interface-admin)
6. [Tests](#tests)
7. [Dépannage](#dépannage)
8. [API Reference](#api-reference)

---

## 🎯 VUE D'ENSEMBLE

### Fonctionnalités Implémentées

Le **CJ Order Service** permet de :

- ✅ **Créer automatiquement** des commandes sur CJ après paiement Stripe
- ✅ **Synchroniser** les statuts de commandes depuis CJ
- ✅ **Récupérer** les numéros de tracking
- ✅ **Gérer** les variantes de produits dans les commandes
- ✅ **Annuler** des commandes sur CJ
- ✅ **Interface admin** complète pour gérer les commandes CJ

### Architecture

```
┌─────────────────┐
│  Paiement       │
│  Stripe         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Order créée    │─────▶│  CjOrderService  │
│  (local)        │      │  .create_cj_order│
└─────────────────┘      └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  API CJ          │
                         │  Commande créée  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  cj_order_id     │
                         │  stocké en DB    │
                         └──────────────────┘
```

---

## 🔧 INSTALLATION ET CONFIGURATION

### 1. Fichiers Créés

Les fichiers suivants ont été ajoutés au projet :

```
services/
  └── cj_order_service.py          # Service principal

routes/
  └── admin_cj_orders.py            # Routes admin

templates/admin/
  └── cj_orders.html                # Interface admin

database/migrations/
  ├── add_cj_order_fields.sql       # Migration SQL
  └── run_cj_order_migration.py     # Script de migration
```

### 2. Modifications Apportées

**Modèles modifiés :**
- `models/order.py` : Ajout champs CJ (cj_order_id, cj_tracking_number, cj_status, cj_logistics_name)
- `models/order.py` : Ajout variant_id dans OrderItem

**Routes modifiées :**
- `routes/cart.py` : Intégration création automatique commande CJ après paiement
- `app.py` : Enregistrement du blueprint admin_cj_orders

### 3. Configuration Requise

Vérifier que votre fichier `.env` contient :

```env
# CJ Dropshipping API
CJ_API_KEY=votre_api_key
CJ_API_SECRET=votre_api_secret
CJ_API_ENDPOINT=https://developers.cjdropshipping.com/api2.0/v1

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## 💾 MIGRATION DE LA BASE DE DONNÉES

### Étape 1 : Exécuter la Migration

```powershell
# Depuis le répertoire racine du projet
python database/migrations/run_cj_order_migration.py
```

**Sortie attendue :**
```
🔄 Début de la migration CJ Order...
  Exécution: ALTER TABLE "order" ADD COLUMN IF NOT EXISTS cj_order_id VARCHAR(100)...
  Exécution: ALTER TABLE "order" ADD COLUMN IF NOT EXISTS cj_tracking_number VARCHAR...
  Exécution: ALTER TABLE "order" ADD COLUMN IF NOT EXISTS cj_status VARCHAR(50)...
  Exécution: ALTER TABLE "order" ADD COLUMN IF NOT EXISTS cj_logistics_name VARCHAR...
  Exécution: ALTER TABLE order_item ADD COLUMN IF NOT EXISTS variant_id INTEGER...
✅ Migration CJ Order terminée avec succès!

Champs ajoutés:
  - order.cj_order_id
  - order.cj_tracking_number
  - order.cj_status
  - order.cj_logistics_name
  - order_item.variant_id
```

### Étape 2 : Vérifier la Migration

```powershell
# Lancer l'application
python app.py
```

Si aucune erreur n'apparaît, la migration est réussie.

---

## 🎮 UTILISATION

### Flux Automatique (Recommandé)

Le système fonctionne **automatiquement** après paiement Stripe :

1. **Client effectue un paiement** via Stripe
2. **Commande locale créée** avec statut `paid`
3. **CJ Order Service appelé automatiquement**
4. **Commande créée sur CJ** et confirmée
5. **cj_order_id stocké** dans la base de données
6. **Client reçoit confirmation** par email

### Flux Manuel (Admin)

Vous pouvez aussi créer des commandes manuellement depuis l'admin :

1. Aller sur `/admin/cj/orders`
2. Trouver une commande payée sans CJ Order ID
3. Cliquer sur le bouton **"+"** (Créer sur CJ)
4. La commande est créée et confirmée automatiquement

---

## 🖥️ INTERFACE ADMIN

### Accès

URL : `http://localhost:5000/admin/cj/orders`

**Droits requis :** Administrateur

### Fonctionnalités

#### 1. Dashboard

Affiche les statistiques :
- Total commandes
- En attente
- En traitement
- Expédiées
- Livrées
- Avec ID CJ

#### 2. Liste des Commandes

Colonnes affichées :
- N° Commande
- Client (email + nom)
- Date
- Montant
- Statut local
- Statut CJ (avec tracking si disponible)
- Actions

#### 3. Actions Disponibles

**Par commande :**
- 👁️ **Voir détails** : Afficher les détails complets
- ➕ **Créer sur CJ** : Créer la commande sur CJ (si pas encore créée)
- 🔄 **Synchroniser** : Mettre à jour le statut depuis CJ

**Actions en masse :**
- Sélectionner plusieurs commandes
- Créer toutes sur CJ
- Synchroniser toutes

**Action globale :**
- 🔄 **Synchroniser Tout** : Synchronise toutes les commandes en attente

#### 4. Filtres

Filtrer par statut :
- Tous
- En Attente
- Payée
- En Traitement
- Expédiée
- Livrée
- Annulée

---

## 🧪 TESTS

### Test 1 : Création Manuelle

```python
# Dans un shell Python ou script
from app import app
from models.order import Order
from models.api_provider import ApiProvider
from services.api_providers.cj_dropshipping import CJDropshippingProvider
from services.cj_order_service import CjOrderService

with app.app_context():
    # Récupérer une commande payée
    order = Order.query.filter_by(payment_status='paid').first()
    
    # Créer le service
    provider = ApiProvider.query.filter_by(name='CJ Dropshipping', active=True).first()
    cj_api = CJDropshippingProvider(provider)
    service = CjOrderService(cj_api)
    
    # Créer la commande sur CJ
    result = service.create_cj_order(order.id)
    
    print(result)
    # {'success': True, 'cj_order_id': 'CJ123456', ...}
```

### Test 2 : Synchronisation Statut

```python
# Synchroniser le statut d'une commande
result = service.sync_order_status(order.id)
print(result)
# {'success': True, 'old_status': 'paid', 'new_status': 'processing', ...}
```

### Test 3 : Récupération Tracking

```python
# Récupérer le tracking
result = service.get_tracking_info(order.cj_order_id)
print(result)
# {'success': True, 'tracking_number': 'TRACK123', ...}
```

### Test 4 : Flux Complet E2E

1. Ajouter un produit CJ au panier
2. Aller au checkout
3. Effectuer un paiement test Stripe
4. Vérifier que la commande est créée localement
5. Vérifier que `cj_order_id` est renseigné
6. Vérifier dans l'admin CJ que la commande existe

---

## 🔍 DÉPANNAGE

### Problème : Commande non créée sur CJ

**Symptômes :**
- Paiement réussi
- Commande locale créée
- Pas de `cj_order_id`

**Solutions :**

1. **Vérifier les logs :**
```powershell
# Chercher les erreurs CJ dans les logs
# Regarder la console où l'app tourne
```

2. **Vérifier la configuration CJ :**
```python
from models.api_provider import ApiProvider
provider = ApiProvider.query.filter_by(name='CJ Dropshipping').first()
print(f"Active: {provider.active}")
print(f"API Key: {provider.api_key[:10]}...")
```

3. **Tester l'API CJ manuellement :**
```python
from services.api_providers.cj_dropshipping import CJDropshippingProvider
cj_api = CJDropshippingProvider(provider)
# Tester un appel simple
response = cj_api._make_request('GET', '/shopping/products/list', {'pageNum': 1, 'pageSize': 1})
print(response)
```

4. **Créer manuellement depuis l'admin :**
- Aller sur `/admin/cj/orders`
- Trouver la commande
- Cliquer sur le bouton "+"

### Problème : Erreur "Produit non CJ"

**Cause :** La commande contient des produits sans `cj_pid`

**Solution :**
- Vérifier que tous les produits ont un `cj_pid`
- Synchroniser les produits CJ : `/admin/cj/sync`

### Problème : Statut non synchronisé

**Cause :** La synchronisation automatique n'est pas activée

**Solution :**
1. Synchroniser manuellement depuis l'admin
2. Configurer un CRON job pour synchronisation automatique :

```python
# Dans services/scheduler_service.py
from services.cj_order_service import CjOrderService

def sync_cj_orders():
    """Job CRON pour synchroniser les commandes CJ"""
    with app.app_context():
        provider = ApiProvider.query.filter_by(name='CJ Dropshipping', active=True).first()
        if provider:
            cj_api = CJDropshippingProvider(provider)
            service = CjOrderService(cj_api)
            result = service.sync_all_pending_orders()
            print(f"Sync CJ: {result}")

# Ajouter au scheduler (toutes les heures)
scheduler.add_job(
    func=sync_cj_orders,
    trigger="interval",
    hours=1,
    id='sync_cj_orders'
)
```

### Problème : Variante non envoyée à CJ

**Cause :** Le panier ne stocke pas le `variant_id`

**Solution :**
- Vérifier que le modèle `Cart` supporte les variantes
- Vérifier que le JavaScript envoie le `variant_id` lors de l'ajout au panier

---

## 📚 API REFERENCE

### CjOrderService

#### `create_cj_order(order_id: int) -> Dict`

Crée une commande sur CJ Dropshipping.

**Paramètres :**
- `order_id` (int) : ID de la commande locale

**Retour :**
```python
{
    'success': True,
    'cj_order_id': 'CJ123456789',
    'order_number': 'ORD-20260123-A1B2',
    'confirmed': True
}
```

**Erreurs possibles :**
- Commande introuvable
- Commande non payée
- Commande déjà créée sur CJ
- Aucun produit CJ dans la commande
- Erreur API CJ

---

#### `confirm_cj_order(cj_order_id: str) -> Dict`

Confirme une commande CJ (appelé automatiquement après création).

**Paramètres :**
- `cj_order_id` (str) : ID de la commande CJ

**Retour :**
```python
{
    'success': True,
    'message': 'Commande confirmée',
    'cj_order_id': 'CJ123456789'
}
```

---

#### `get_order_status(cj_order_id: str) -> Dict`

Récupère le statut d'une commande CJ.

**Paramètres :**
- `cj_order_id` (str) : ID de la commande CJ

**Retour :**
```python
{
    'success': True,
    'cj_order_id': 'CJ123456789',
    'status': 'SHIPPED',
    'tracking_number': 'TRACK123456',
    'logistics_name': 'DHL Express',
    'created_at': '2026-01-23T10:00:00',
    'shipped_at': '2026-01-24T14:30:00'
}
```

---

#### `get_tracking_info(cj_order_id: str) -> Dict`

Récupère les informations de tracking.

**Paramètres :**
- `cj_order_id` (str) : ID de la commande CJ

**Retour :**
```python
{
    'success': True,
    'cj_order_id': 'CJ123456789',
    'tracking_number': 'TRACK123456',
    'logistics_name': 'DHL Express',
    'logistics_url': 'https://track.dhl.com/...',
    'shipped_at': '2026-01-24T14:30:00'
}
```

---

#### `sync_order_status(order_id: int) -> Dict`

Synchronise le statut d'une commande depuis CJ.

**Paramètres :**
- `order_id` (int) : ID de la commande locale

**Retour :**
```python
{
    'success': True,
    'message': 'Statut synchronisé',
    'old_status': 'paid',
    'new_status': 'shipped',
    'cj_status': 'SHIPPED',
    'tracking_number': 'TRACK123456'
}
```

---

#### `cancel_cj_order(cj_order_id: str, reason: str = '') -> Dict`

Annule une commande CJ.

**Paramètres :**
- `cj_order_id` (str) : ID de la commande CJ
- `reason` (str) : Raison de l'annulation

**Retour :**
```python
{
    'success': True,
    'message': 'Commande annulée',
    'cj_order_id': 'CJ123456789'
}
```

---

#### `sync_all_pending_orders() -> Dict`

Synchronise toutes les commandes en attente.

**Retour :**
```python
{
    'success': True,
    'message': '5 créées, 10 synchronisées, 0 erreurs',
    'results': {
        'total': 15,
        'created': 5,
        'synced': 10,
        'errors': 0,
        'details': [...]
    }
}
```

---

## 🎯 MAPPING DES STATUTS

### Statuts CJ → Statuts Locaux

| Statut CJ | Statut Local | Description |
|-----------|--------------|-------------|
| PENDING | pending | En attente de traitement |
| PAID | paid | Payée |
| PROCESSING | processing | En préparation |
| SHIPPED | shipped | Expédiée |
| DELIVERED | delivered | Livrée |
| CANCELLED | cancelled | Annulée |
| REFUNDED | cancelled | Remboursée |

---

## 📊 STRUCTURE DES DONNÉES

### Table `order` (nouveaux champs)

```sql
cj_order_id VARCHAR(100)        -- ID de la commande sur CJ
cj_tracking_number VARCHAR(100) -- Numéro de suivi
cj_status VARCHAR(50)           -- Statut CJ
cj_logistics_name VARCHAR(100)  -- Nom du transporteur
```

### Table `order_item` (nouveau champ)

```sql
variant_id INTEGER              -- ID de la variante sélectionnée
```

---

## ✅ CHECKLIST DE MISE EN PRODUCTION

Avant de mettre en production, vérifier :

- [ ] Migration de la base de données exécutée
- [ ] Configuration CJ API dans `.env`
- [ ] Configuration Stripe dans `.env`
- [ ] Test de création de commande manuelle réussi
- [ ] Test de paiement Stripe → Création CJ réussi
- [ ] Test de synchronisation statut réussi
- [ ] Interface admin accessible et fonctionnelle
- [ ] Logs activés pour le monitoring
- [ ] CRON job de synchronisation configuré (optionnel)
- [ ] Emails de confirmation fonctionnels
- [ ] Webhooks CJ configurés (optionnel)

---

## 🚀 PROCHAINES ÉTAPES

### Phase 2 - Automatisation (Recommandé)

1. **CRON Jobs**
   - Synchronisation quotidienne du stock
   - Synchronisation horaire des statuts
   - Synchronisation hebdomadaire des nouveaux produits

2. **Webhooks CJ**
   - Notifications temps réel des expéditions
   - Mise à jour automatique des statuts
   - Notifications clients automatiques

3. **Dashboard Analytics**
   - KPIs de ventes
   - Graphiques d'évolution
   - Rapport des produits les plus vendus

### Phase 3 - Améliorations UX

1. **Filtres Avancés**
   - Filtres par prix, couleur, taille
   - Tri personnalisé
   - Recherche avec auto-complétion

2. **Optimisations**
   - Téléchargement images en local
   - Compression et optimisation
   - CDN pour les images

---

## 📞 SUPPORT

En cas de problème :

1. Consulter les logs de l'application
2. Vérifier la configuration CJ API
3. Tester manuellement depuis l'admin
4. Consulter la documentation CJ : https://developers.cjdropshipping.com/

---

## 📝 CHANGELOG

### Version 1.0.0 (23 Janvier 2026)

**Ajouté :**
- Service CjOrderService complet
- Routes admin pour gestion commandes CJ
- Interface admin moderne
- Intégration automatique dans le flux de paiement
- Support des variantes de produits
- Migration de base de données
- Documentation complète

**Modifié :**
- Modèle Order (ajout champs CJ)
- Modèle OrderItem (ajout variant_id)
- Routes cart.py (intégration CJ Order)
- app.py (enregistrement blueprint)

---

**🎉 Félicitations ! Le système de commandes CJ est maintenant opérationnel !**
