# 🔧 Configuration et Utilisation de l'Admin CJ

**Date:** 4 février 2026  
**Objectif:** Rendre les pages admin CJ fonctionnelles pour une gestion multi-fournisseurs

---

## 🎯 Architecture du Système

### Double Structure de Catégories

Votre marketplace utilise une **double structure** pour gérer les fournisseurs :

```
┌─────────────────────────────────────────────────────────────┐
│                    BASE DE DONNÉES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📁 CATÉGORIES MPS FRANÇAISES (visible=True)               │
│  ├─ Électronique & High-Tech                               │
│  ├─ Informatique                                           │
│  ├─ Mode & Vêtements                                       │
│  └─ ... (17 catégories principales)                        │
│      └─ Visibles sur le site public                        │
│                                                             │
│  📁 CATÉGORIES CJ (visible=False)                          │
│  ├─ Consumer Electronics                                   │
│  ├─ Computer & Office                                      │
│  ├─ Women's Clothing                                       │
│  └─ ... (catégories CJ)                                    │
│      └─ Visibles uniquement dans l'admin                   │
│                                                             │
│  🔗 MAPPINGS CJ → MPS                                      │
│  ├─ Consumer Electronics → Électronique & High-Tech        │
│  ├─ Computer & Office → Informatique                       │
│  └─ Women's Clothing → Mode & Vêtements                    │
│      └─ Assignation automatique des produits               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Étape 1 : Configuration des Credentials CJ

### Problème Actuel

Les credentials CJ dans la base de données ne sont pas au bon format. L'API CJ nécessite :
- **Email CJ** (votre email de compte CJ Dropshipping)
- **Password CJ** (votre mot de passe CJ)

### Solution

1. **Accéder à la configuration des providers**
   ```
   http://multiproshop.local/admin/api-providers
   ```

2. **Éditer le provider "CJ Dropshipping"**
   - Cliquer sur le bouton "Éditer"
   - Vérifier/Modifier les champs :
     - **API Key** : Votre **email** CJ Dropshipping
     - **API Secret** : Votre **mot de passe** CJ Dropshipping
     - **Endpoint** : `https://developers.cjdropshipping.com/api2.0/v1`

3. **Sauvegarder**

---

## 📋 Étape 2 : Synchronisation des Catégories CJ

### Via l'Interface Admin (Recommandé)

1. **Accéder à la page CJ Catégories**
   ```
   http://multiproshop.local/admin/cj/categories
   ```

2. **Cliquer sur "Synchroniser depuis CJ"**
   - Le système va :
     - ✅ Récupérer toutes les catégories CJ depuis l'API
     - ✅ Les créer dans la base avec `visible=False` (non visibles sur le site)
     - ✅ Créer automatiquement les mappings vers vos catégories françaises

3. **Résultat attendu**
   - Les catégories CJ apparaissent dans l'admin
   - Les mappings sont créés automatiquement
   - Les catégories françaises restent inchangées

### Modification du Service de Sync

Pour que la synchronisation depuis l'admin fonctionne correctement, j'ai besoin de modifier le service `CjSyncService` pour :

1. **Marquer les catégories CJ comme non visibles** (`visible=False`)
2. **Créer automatiquement les mappings** lors de la synchronisation

---

## 📊 Étape 3 : Pages Admin CJ Fonctionnelles

### Page 1 : CJ Catégories

**URL:** `http://multiproshop.local/admin/cj/categories`

**Fonctionnalités:**
- ✅ Affiche toutes les catégories CJ synchronisées
- ✅ Hiérarchie à 3 niveaux visible
- ✅ Statistiques (nombre de produits par catégorie)
- ✅ Recherche et filtres
- ✅ Bouton de synchronisation

**Ce que vous verrez:**
```
┌─────────────────────────────────────────────────────────┐
│ CJ Catégories                    [Synchroniser depuis CJ]│
├─────────────────────────────────────────────────────────┤
│ Total: 500+ catégories                                  │
│                                                          │
│ 📁 Consumer Electronics (Niveau 1)                      │
│   └─ 📁 Portable Audio & Video (Niveau 2)              │
│       └─ 📁 Headphones (Niveau 3) - 150 produits       │
│                                                          │
│ 📁 Computer & Office (Niveau 1)                         │
│   └─ 📁 Storage Devices (Niveau 2)                     │
│       └─ 📁 USB Flash Drives (Niveau 3) - 80 produits  │
└─────────────────────────────────────────────────────────┘
```

### Page 2 : CJ Produits

**URL:** `http://multiproshop.local/admin/cj/products`

**Fonctionnalités:**
- ✅ Affiche les produits CJ par catégorie
- ✅ Montre la catégorie MPS mappée
- ✅ Prix CJ + Prix avec marge
- ✅ Stock disponible
- ✅ Bouton de synchronisation par catégorie

**Ce que vous verrez:**
```
┌─────────────────────────────────────────────────────────┐
│ CJ Produits - Headphones                                │
├─────────────────────────────────────────────────────────┤
│ Catégorie CJ: Consumer Electronics > Headphones         │
│ Catégorie MPS: Électronique & High-Tech                │
│ Mapping: ✓ Actif                                        │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Wireless Bluetooth Headphones                       │ │
│ │ Prix CJ: $15.99                                     │ │
│ │ Prix MPS: €20.79 (marge 30%)                       │ │
│ │ Stock: 500                                          │ │
│ │ [Synchroniser ce produit]                           │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Page 3 : CJ Pricing

**URL:** `http://multiproshop.local/admin/cj/pricing`

**Fonctionnalités:**
- ✅ Affiche les marges par catégorie
- ✅ Permet de modifier les marges
- ✅ Calcul automatique des prix
- ✅ Aperçu des prix avant/après

**Ce que vous verrez:**
```
┌─────────────────────────────────────────────────────────┐
│ CJ Pricing - Configuration des Marges                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Catégorie MPS          │ Marge    │ Exemple             │
│────────────────────────┼──────────┼─────────────────────│
│ Électronique & High-Tech│ 30%     │ $100 → €130        │
│ Informatique           │ 25%      │ $100 → €125        │
│ Mode & Vêtements       │ 50%      │ $100 → €150        │
│ Maison & Jardin        │ 40%      │ $100 → €140        │
│                                                          │
│ [Modifier les marges] [Appliquer à tous les produits]   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Flux de Synchronisation Complet

### 1. Synchronisation des Catégories

```
[Admin] Clic sur "Synchroniser depuis CJ"
    ↓
[API CJ] Récupération des catégories
    ↓
[Base de données] Création des catégories CJ (visible=False)
    ↓
[Mappings] Création automatique CJ → MPS français
    ↓
[Admin] Affichage des catégories + mappings
```

### 2. Synchronisation des Produits

```
[Admin] Clic sur "Synchroniser les produits"
    ↓
[API CJ] Récupération des produits
    ↓
[Mappings] Recherche de la catégorie MPS correspondante
    ↓
[Base de données] Création du produit dans la catégorie MPS française
    ↓
[Site public] Produit visible dans la catégorie française
```

---

## ✅ Avantages de cette Architecture

### Pour l'Admin

1. **Visibilité complète** : Vous voyez toutes les catégories et produits CJ
2. **Gestion des mappings** : Vous pouvez modifier les correspondances
3. **Contrôle des marges** : Vous définissez les prix par catégorie
4. **Multi-fournisseurs** : Prêt pour ajouter d'autres fournisseurs (AliExpress, Amazon, etc.)

### Pour le Site Public

1. **Catégories françaises** : Interface propre en français
2. **Pas de doublons** : Une seule structure de catégories visible
3. **SEO optimisé** : URLs en français
4. **Expérience utilisateur** : Navigation claire et cohérente

---

## 🛠️ Modifications Nécessaires

Pour que tout fonctionne, je dois modifier le fichier `services/cj_sync_service.py` :

### Modification 1 : Catégories non visibles sur le site

```python
def _sync_category(self, category_data: Dict) -> None:
    # ...
    category = Category(
        name=category_data.get('name', ''),
        slug=unique_slug,
        cj_category_id=cj_id,
        visible=False,  # ← AJOUTER CETTE LIGNE
        is_active=True,
        # ...
    )
```

### Modification 2 : Création automatique des mappings

```python
def _sync_category(self, category_data: Dict) -> None:
    # Après création de la catégorie CJ
    # Créer le mapping automatiquement
    self._create_auto_mapping(category_data)
```

---

## 📝 Checklist de Configuration

- [ ] Vérifier les credentials CJ dans `/admin/api-providers`
- [ ] Corriger l'email et le mot de passe si nécessaire
- [ ] Modifier `services/cj_sync_service.py` (visible=False)
- [ ] Ajouter la création automatique des mappings
- [ ] Tester la synchronisation des catégories
- [ ] Vérifier que les pages admin CJ sont fonctionnelles
- [ ] Lancer la synchronisation des produits
- [ ] Vérifier que les produits apparaissent dans les catégories françaises

---

## 🎉 Résultat Final

Une fois tout configuré, vous aurez :

✅ **Admin CJ complet** : Catégories, Produits, Pricing visibles et modifiables  
✅ **Mappings automatiques** : Produits CJ → Catégories françaises  
✅ **Site public propre** : Uniquement les catégories françaises visibles  
✅ **Multi-fournisseurs prêt** : Architecture extensible pour d'autres APIs  

---

**Dernière mise à jour :** 4 février 2026 21:00  
**Statut :** Configuration en cours - Credentials à vérifier
