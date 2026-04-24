# 📖 GUIDE D'UTILISATION COMPLET - MULTIPROSHOP CJ INTÉGRATION

**Version** : 1.0  
**Date** : 6 janvier 2026  
**Statut** : Phases 1-5 complétées

---

## 🎯 INTRODUCTION

Ce guide explique comment utiliser toutes les fonctionnalités d'intégration CJ Dropshipping dans MultiProShop.

### Fonctionnalités disponibles :
✅ Synchronisation catégories CJ (3 niveaux)  
✅ Synchronisation produits avec variantes  
✅ Calcul frais de livraison en temps réel  
✅ Interface admin moderne  
✅ API REST complète  

---

## 🚀 DÉMARRAGE RAPIDE

### 1. Configuration initiale

**Vérifier le fichier `.env`** :
```bash
# Identifiants CJ Dropshipping
CJ_EMAIL=votre_email@gmail.com
CJ_PASSWORD=votre_mot_de_passe
CJ_DEV_KEY=votre_dev_key
CJ_BASE_URL=https://developers.cjdropshipping.com/api2.0/v1/
```

### 2. Lancer l'application

```bash
# Activer l'environnement virtuel
.\venv\Scripts\activate

# Lancer le serveur
python app.py
```

L'application sera accessible sur : `http://localhost:5000`

### 3. Accéder à l'admin

URL : `http://localhost:5000/admin/cj/categories`

---

## 📂 GESTION DES CATÉGORIES

### Interface admin catégories

**URL** : `/admin/cj/categories`

#### Fonctionnalités :

1. **Synchroniser depuis CJ**
   - Cliquer sur "Synchroniser depuis CJ"
   - Attend 5 minutes entre chaque sync (rate limiting CJ)
   - Importe toutes les catégories (3 niveaux)

2. **Rechercher une catégorie**
   - Utiliser la barre de recherche
   - Recherche dans nom, nom FR et chemin complet

3. **Filtrer par niveau**
   - Niveau 1 : Catégories principales
   - Niveau 2 : Sous-catégories
   - Niveau 3 : Catégories finales (produits)

4. **Voir les détails**
   - Cliquer sur une catégorie
   - Affiche ID CJ, nom, traduction, chemin, produits

### API Catégories

```bash
# Synchroniser les catégories
curl -X POST http://localhost:5000/admin/api/cj/sync/categories \
  -H "Content-Type: application/json"

# Récupérer les catégories visibles
curl -X POST http://localhost:5000/admin/api/cj/categories/visible \
  -H "Content-Type: application/json"
```

**Réponse** :
```json
{
  "success": true,
  "categories": [
    {
      "id": 1,
      "cj_category_id": "UUID",
      "name": "Women's Clothing",
      "name_fr": "Vêtements Femme",
      "level": 1,
      "product_count": 150,
      "visible": true,
      "path": "Women's Clothing"
    }
  ]
}
```

---

## 🛍️ GESTION DES PRODUITS

### Interface admin produits

**URL** : `/admin/cj/products`

#### Workflow :

1. **Sélectionner une catégorie**
   - Sidebar gauche : liste des catégories niveau 3
   - Cliquer sur une catégorie pour voir ses produits

2. **Synchroniser les produits**
   - Bouton "Synchroniser"
   - Importe jusqu'à 100 produits de la catégorie
   - Avec variantes, images, prix

3. **Voir les détails d'un produit**
   - Cliquer sur "Détails"
   - Affiche toutes les infos : prix, stock, variantes

4. **Enrichir un produit**
   - Bouton "Enrichir" dans le modal
   - Récupère avis clients depuis CJ
   - Calcule note moyenne

5. **Publier un produit**
   - Bouton "Publier"
   - Rend le produit visible sur le magasin

### API Produits

```bash
# Synchroniser les produits d'une catégorie
curl -X POST http://localhost:5000/admin/api/cj/sync/products \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": "UUID-CATEGORY",
    "limit": 100
  }'

# Récupérer les produits d'une catégorie
curl -X POST http://localhost:5000/admin/api/cj/products/by-category \
  -H "Content-Type: application/json" \
  -d '{
    "category_cj_id": "UUID-CATEGORY",
    "page": 1,
    "per_page": 20
  }'

# Enrichir un produit
curl -X POST http://localhost:5000/admin/api/cj/enrich/PRODUCT_PID
```

**Réponse produits** :
```json
{
  "success": true,
  "products": [
    {
      "id": 123,
      "cj_pid": "2509301040541613300",
      "name": "Women's Sweater",
      "sku": "CJMY2546714",
      "price": 6.63,
      "suggested_price": 34.68,
      "stock": 379,
      "image_url": "https://...",
      "published": false,
      "synced_at": "2026-01-06T12:00:00"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

---

## 🚚 CALCUL DES FRAIS DE LIVRAISON

### Service ShippingService

Le service calcule automatiquement les frais avec :
1. **Priorité API CJ** : Frais réels depuis CJ
2. **Fallback intelligent** : Méthodes standard si API indisponible

### API Shipping

```bash
# Calculer pour un panier
curl -X POST http://localhost:5000/api/shipping/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "cj_pid": "2509301040541613300",
        "cj_vid": "2509301040541613500",
        "quantity": 2,
        "product": {
          "cj_pid": "2509301040541613300",
          "product_weight": "360"
        }
      }
    ],
    "country": "FR"
  }'

# Calculer pour un produit unique
curl -X POST http://localhost:5000/api/shipping/calculate/product/123 \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 1,
    "country": "FR"
  }'

# Obtenir les méthodes disponibles
curl http://localhost:5000/api/shipping/methods?country=FR
```

**Réponse** :
```json
{
  "success": true,
  "methods": [
    {
      "code": "STANDARD",
      "name": "Livraison Standard",
      "price": 4.99,
      "delivery_time": "10-20 jours",
      "description": "Livraison économique",
      "source": "cj"
    },
    {
      "code": "EXPRESS",
      "name": "Livraison Express",
      "price": 12.99,
      "delivery_time": "5-10 jours",
      "description": "Livraison rapide",
      "source": "cj"
    }
  ],
  "total_weight": 720,
  "source": "cj"
}
```

### Méthodes de livraison

| Code | Nom | Prix base | Délai |
|------|-----|-----------|-------|
| STANDARD | Livraison Standard | 4.99€ | 10-20 jours |
| EXPRESS | Livraison Express | 12.99€ | 5-10 jours |
| PREMIUM | Livraison Premium | 24.99€ | 3-5 jours |

**Ajustements automatiques** :
- Poids > 2kg : +50%
- Poids > 5kg : +100%
- Hors Europe : +30%

---

## 📊 STATISTIQUES

### Obtenir les statistiques globales

```bash
curl http://localhost:5000/admin/api/cj/stats
```

**Réponse** :
```json
{
  "success": true,
  "stats": {
    "products": {
      "total": 500,
      "synced": 450,
      "published": 200,
      "in_stock": 380
    },
    "variants": {
      "total": 1500,
      "active": 1400
    },
    "categories": {
      "total": 150,
      "level_1": 10,
      "level_2": 40,
      "level_3": 100,
      "visible": 145
    },
    "last_sync": "2026-01-06T12:00:00"
  }
}
```

---

## 🔄 SYNCHRONISATION

### Workflow complet

1. **Synchroniser les catégories** (une fois)
   ```bash
   POST /admin/api/cj/sync/categories
   ```

2. **Synchroniser les produits** (par catégorie)
   ```bash
   POST /admin/api/cj/sync/products
   Body: {"category_id": "UUID", "limit": 100}
   ```

3. **Enrichir les produits** (optionnel)
   ```bash
   POST /admin/api/cj/enrich/PRODUCT_PID
   ```

4. **Mettre à jour le stock** (régulièrement)
   ```bash
   POST /admin/api/cj/sync/stock
   ```

### Fréquence recommandée

- **Catégories** : 1 fois par semaine
- **Produits** : 1 fois par jour
- **Stock** : Toutes les heures
- **Enrichissement** : À la demande

---

## ⚠️ LIMITATIONS ET RATE LIMITING

### API CJ Dropshipping

**Authentification** :
- 1 requête toutes les 5 minutes
- Cache token en session Flask
- Durée token : 14 jours

**Requêtes générales** :
- Respecter les limites CJ
- Gestion automatique des erreurs 429
- Retry après 5 minutes

### Gestion des erreurs

Le système gère automatiquement :
- ✅ Rate limiting (429)
- ✅ Erreurs réseau
- ✅ Token expiré
- ✅ Fallback sur méthodes standard

---

## 🛠️ DÉVELOPPEMENT

### Structure des fichiers

```
multiproshop/
├── services/
│   ├── api_providers/
│   │   └── cj_dropshipping_optimized.py  # API CJ
│   ├── cj_sync_service.py                # Synchronisation
│   └── shipping_service.py               # Calcul livraison
├── routes/
│   ├── admin_cj_sync.py                  # Routes API admin
│   ├── admin_cj_pages.py                 # Pages admin
│   └── shipping_api.py                   # API livraison
├── templates/admin/
│   ├── cj_categories.html                # Interface catégories
│   └── cj_products.html                  # Interface produits
├── models/
│   ├── category.py                       # Modèle catégorie
│   ├── product.py                        # Modèle produit
│   └── product_variant.py                # Modèle variante
└── database/migrations/
    ├── add_cj_fields.sql                 # Migration SQL
    └── run_migration.py                  # Exécuteur
```

### Ajouter une nouvelle fonctionnalité

1. **Service** : Créer dans `services/`
2. **Routes** : Créer blueprint dans `routes/`
3. **Template** : Créer dans `templates/`
4. **Enregistrer** : Ajouter dans `app.py`

---

## 🧪 TESTS

### Scripts de test disponibles

```bash
# Test API CJ complet
python scripts/test_cj_optimized.py

# Test authentification simple
python scripts/test_cj_auth_simple.py

# Test migration BDD
python database/migrations/run_migration.py
```

### Test manuel via curl

```bash
# 1. Synchroniser catégories
curl -X POST http://localhost:5000/admin/api/cj/sync/categories

# 2. Récupérer catégories
curl -X POST http://localhost:5000/admin/api/cj/categories/visible

# 3. Synchroniser produits
curl -X POST http://localhost:5000/admin/api/cj/sync/products \
  -H "Content-Type: application/json" \
  -d '{"category_id": "UUID", "limit": 10}'

# 4. Calculer livraison
curl -X POST http://localhost:5000/api/shipping/calculate/product/1 \
  -H "Content-Type: application/json" \
  -d '{"quantity": 1, "country": "FR"}'
```

---

## 📝 NOTES IMPORTANTES

### Sécurité

- ⚠️ Ne jamais versionner `.env` sur Git
- ⚠️ Utiliser HTTPS en production
- ⚠️ Protéger les routes admin avec authentification

### Performance

- ✅ Cache token en session (14 jours)
- ✅ Index BDD pour requêtes rapides
- ✅ Pagination automatique
- ✅ Fallback shipping intelligent

### Maintenance

- 🔄 Synchroniser catégories : 1x/semaine
- 🔄 Synchroniser produits : 1x/jour
- 🔄 Mettre à jour stock : 1x/heure
- 🔄 Sauvegarder BDD : 1x/jour

---

## 🆘 DÉPANNAGE

### Erreur "Rate limit"

**Symptôme** : `Too Many Requests, QPS limit is 1 time/300 seconds`

**Solution** : Attendre 5 minutes avant de réessayer. C'est normal.

### Erreur "Token expiré"

**Symptôme** : `Token expired`

**Solution** : Le système rafraîchit automatiquement. Réessayer.

### Produits non synchronisés

**Vérifier** :
1. Catégories synchronisées ?
2. ID catégorie correct ?
3. Limite pas atteinte ?

### Frais de livraison incorrects

**Vérifier** :
1. Poids produit renseigné ?
2. Code pays correct (ISO) ?
3. API CJ accessible ?

---

## 📞 SUPPORT

### Logs

Les logs sont affichés dans la console :
```
[CJ API] Authentification réussie !
[CjSync] 150 catégories synchronisées
[Shipping] Utilisation des méthodes par défaut
```

### Documentation API CJ

https://developers.cjdropshipping.com/

---

## ✅ CHECKLIST MISE EN PRODUCTION

- [ ] Variables `.env` configurées
- [ ] Base de données migrée
- [ ] Catégories synchronisées
- [ ] Produits synchronisés
- [ ] Tests effectués
- [ ] HTTPS activé
- [ ] Authentification admin sécurisée
- [ ] Sauvegardes automatiques configurées
- [ ] Monitoring activé
- [ ] Logs configurés

---

**Document créé le** : 6 janvier 2026  
**Version** : 1.0  
**Auteur** : Cascade AI  
**Projet** : MultiProShop - Intégration CJ Optimisée
