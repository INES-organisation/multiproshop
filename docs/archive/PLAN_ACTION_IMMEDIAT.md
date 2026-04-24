# 🚀 PLAN D'ACTION IMMÉDIAT - MULTIPROSHOP
## Rendre la plateforme fonctionnelle pour vendre

---

## 🎯 OBJECTIF CETTE SEMAINE
**Créer un workflow complet d'ajout de produits et d'achat**

---

## 📋 TÂCHES PRIORITAIRES (Ordre d'exécution)

### ✅ JOUR 1-2 : GESTION DES PRODUITS (Admin)

#### 1. Améliorer le modèle Product
```python
# Ajouter dans models/product.py
- SKU (référence unique)
- Images multiples (JSON ou table séparée)
- Caractéristiques techniques (JSON)
- Poids (pour calcul livraison)
- Dimensions
- is_active (publié/brouillon)
- is_featured (produit mis en avant)
- tags (mots-clés)
```

#### 2. Créer l'interface admin produits
- [ ] Route `/admin/products` - Liste des produits
- [ ] Route `/admin/products/create` - Formulaire création
- [ ] Route `/admin/products/edit/<id>` - Formulaire édition
- [ ] Route `/admin/products/delete/<id>` - Suppression
- [ ] Template `admin/products.html` - Liste avec filtres
- [ ] Template `admin/product_form.html` - Formulaire complet

#### 3. Upload d'images
- [ ] Installer Pillow : `pip install Pillow`
- [ ] Créer dossier `static/uploads/products/`
- [ ] Fonction upload avec redimensionnement
- [ ] Miniatures automatiques
- [ ] Validation format (JPG, PNG, WEBP)
- [ ] Limite de taille (2MB max)

#### 4. Ajouter des produits de test
- [ ] Créer un script `add_sample_products.py`
- [ ] Ajouter 30-50 produits variés
- [ ] Répartir dans différentes catégories
- [ ] Images de placeholder (via API ou locales)

---

### ✅ JOUR 3 : PANIER FONCTIONNEL

#### 1. Améliorer le modèle Cart
```python
# Vérifier models/cart.py
- session_id (pour utilisateurs non connectés)
- expires_at (expiration panier)
- Méthodes: add_item(), remove_item(), update_quantity(), get_total()
```

#### 2. Routes du panier
- [ ] Route `/cart` - Afficher le panier
- [ ] Route `/cart/add/<product_id>` - Ajouter au panier (AJAX)
- [ ] Route `/cart/update/<item_id>` - Modifier quantité (AJAX)
- [ ] Route `/cart/remove/<item_id>` - Supprimer item (AJAX)
- [ ] Route `/cart/clear` - Vider le panier

#### 3. Template panier
- [ ] Template `pages/cart.html`
- [ ] Liste des produits avec images
- [ ] Modification quantité (+/-)
- [ ] Suppression d'un item
- [ ] Calcul sous-total
- [ ] Calcul total
- [ ] Bouton "Continuer mes achats"
- [ ] Bouton "Passer commande"

#### 4. JavaScript panier
- [ ] Fonction `addToCart(productId, quantity)` fonctionnelle
- [ ] Mise à jour du compteur panier dans le header
- [ ] Notifications toast (succès/erreur)
- [ ] Animations

---

### ✅ JOUR 4 : CHECKOUT (Tunnel d'achat)

#### 1. Créer le modèle Address
```python
# Nouveau fichier models/address.py
class Address(db.Model):
    - user_id
    - first_name
    - last_name
    - address_line1
    - address_line2
    - city
    - postal_code
    - country
    - phone
    - is_default
```

#### 2. Routes checkout
- [ ] Route `/checkout` - Page récapitulatif
- [ ] Route `/checkout/address` - Choix/ajout adresse
- [ ] Route `/checkout/shipping` - Choix mode livraison
- [ ] Route `/checkout/payment` - Paiement
- [ ] Route `/checkout/confirm` - Confirmation

#### 3. Templates checkout
- [ ] Template `pages/checkout.html` - Récapitulatif
- [ ] Template `pages/checkout_address.html` - Adresse
- [ ] Template `pages/checkout_payment.html` - Paiement
- [ ] Template `pages/checkout_success.html` - Confirmation

#### 4. Logique métier
- [ ] Service `checkout_service.py`
- [ ] Validation du panier (stock disponible)
- [ ] Calcul des frais de livraison
- [ ] Calcul des taxes (TVA)
- [ ] Création de la commande
- [ ] Réduction du stock
- [ ] Vidage du panier

---

### ✅ JOUR 5 : PAIEMENT & CONFIRMATION

#### 1. Intégration Stripe (mode test)
- [ ] Installer : `pip install stripe`
- [ ] Créer compte Stripe test
- [ ] Ajouter clés API dans `.env`
- [ ] Route `/checkout/create-payment-intent`
- [ ] Formulaire de paiement Stripe Elements
- [ ] Gestion des webhooks Stripe

#### 2. Emails de confirmation
- [ ] Installer : `pip install Flask-Mail`
- [ ] Configuration SMTP dans `.env`
- [ ] Template email `email/order_confirmation.html`
- [ ] Fonction `send_order_confirmation(order)`
- [ ] Email avec récapitulatif commande
- [ ] Email avec lien de suivi

#### 3. Page de confirmation
- [ ] Template `pages/order_success.html`
- [ ] Affichage numéro de commande
- [ ] Récapitulatif complet
- [ ] Bouton "Télécharger la facture"
- [ ] Bouton "Suivre ma commande"

---

### ✅ JOUR 6-7 : GESTION DES COMMANDES

#### 1. Interface admin commandes
- [ ] Route `/admin/orders` - Liste des commandes
- [ ] Route `/admin/orders/<id>` - Détail commande
- [ ] Route `/admin/orders/<id>/status` - Changer statut
- [ ] Template `admin/orders.html` - Liste avec filtres
- [ ] Template `admin/order_detail.html` - Détail complet

#### 2. Statuts de commande
```python
# Ajouter dans models/order.py
STATUSES = [
    'pending',      # En attente de paiement
    'paid',         # Payée
    'processing',   # En préparation
    'shipped',      # Expédiée
    'delivered',    # Livrée
    'cancelled',    # Annulée
    'refunded'      # Remboursée
]
```

#### 3. Historique utilisateur
- [ ] Route `/account/orders` - Mes commandes
- [ ] Route `/account/orders/<id>` - Détail commande
- [ ] Template `pages/my_orders.html`
- [ ] Template `pages/order_detail.html`
- [ ] Filtres par statut
- [ ] Recherche par numéro

#### 4. Génération facture PDF
- [ ] Installer : `pip install weasyprint`
- [ ] Template `pdf/invoice.html`
- [ ] Route `/orders/<id>/invoice`
- [ ] Logo entreprise
- [ ] Informations légales
- [ ] Détail produits
- [ ] Calculs (HT, TVA, TTC)

---

## 🛠️ FICHIERS À CRÉER/MODIFIER

### Nouveaux fichiers à créer
```
models/
  ├─ address.py (nouveau)
  
routes/
  ├─ checkout.py (nouveau)
  
services/
  ├─ checkout_service.py (nouveau)
  ├─ email_service.py (nouveau)
  ├─ payment_service.py (nouveau)
  
templates/
  ├─ admin/
  │   ├─ products.html (nouveau)
  │   ├─ product_form.html (nouveau)
  │   ├─ orders.html (nouveau)
  │   └─ order_detail.html (nouveau)
  ├─ pages/
  │   ├─ cart.html (nouveau)
  │   ├─ checkout.html (nouveau)
  │   ├─ checkout_address.html (nouveau)
  │   ├─ checkout_payment.html (nouveau)
  │   ├─ checkout_success.html (nouveau)
  │   ├─ my_orders.html (nouveau)
  │   └─ order_detail.html (nouveau)
  ├─ email/
  │   └─ order_confirmation.html (nouveau)
  └─ pdf/
      └─ invoice.html (nouveau)

static/
  ├─ uploads/
  │   └─ products/ (nouveau dossier)
  └─ js/
      └─ cart.js (nouveau)

scripts/
  └─ add_sample_products.py (nouveau)
```

### Fichiers à modifier
```
models/
  ├─ product.py (améliorer)
  ├─ cart.py (améliorer)
  └─ order.py (améliorer)

routes/
  ├─ admin.py (ajouter routes produits)
  ├─ cart.py (compléter)
  └─ products.py (améliorer)

services/
  ├─ cart_service.py (compléter)
  └─ order_service.py (compléter)

app.py (ajouter blueprints)
requirements.txt (ajouter dépendances)
.env (ajouter clés API)
```

---

## 📦 DÉPENDANCES À INSTALLER

```bash
pip install Pillow              # Traitement d'images
pip install stripe              # Paiement Stripe
pip install Flask-Mail          # Envoi d'emails
pip install weasyprint          # Génération PDF
pip install python-dotenv       # Variables d'environnement
```

---

## 🔧 CONFIGURATION .env

```env
# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-app

# Upload
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=2097152  # 2MB

# Livraison
SHIPPING_COST_STANDARD=5.99
SHIPPING_COST_EXPRESS=12.99
FREE_SHIPPING_THRESHOLD=50.00

# TVA
VAT_RATE=0.20  # 20%
```

---

## ✅ CHECKLIST DE VALIDATION

### Avant de passer à la suite, vérifier :

#### Produits
- [ ] Je peux ajouter un produit via l'admin
- [ ] Je peux uploader une image
- [ ] Je peux modifier un produit
- [ ] Je peux supprimer un produit
- [ ] Les produits s'affichent sur la page liste
- [ ] Je peux cliquer sur un produit pour voir le détail

#### Panier
- [ ] Je peux ajouter un produit au panier
- [ ] Le compteur du panier se met à jour
- [ ] Je peux voir mon panier
- [ ] Je peux modifier les quantités
- [ ] Je peux supprimer un produit
- [ ] Le total se calcule correctement

#### Checkout
- [ ] Je peux accéder au checkout depuis le panier
- [ ] Je peux entrer mon adresse de livraison
- [ ] Je vois le récapitulatif de ma commande
- [ ] Je peux payer avec Stripe (mode test)
- [ ] Je reçois une confirmation après paiement
- [ ] Je reçois un email de confirmation

#### Commandes
- [ ] Ma commande apparaît dans "Mes commandes"
- [ ] Je peux voir le détail de ma commande
- [ ] L'admin voit la commande dans son interface
- [ ] L'admin peut changer le statut
- [ ] Je peux télécharger ma facture PDF

---

## 🎯 RÉSULTAT ATTENDU FIN DE SEMAINE

**Une plateforme e-commerce fonctionnelle où :**
1. ✅ Un admin peut ajouter des produits avec images
2. ✅ Un utilisateur peut naviguer dans les catégories
3. ✅ Un utilisateur peut ajouter des produits au panier
4. ✅ Un utilisateur peut passer commande et payer
5. ✅ Un utilisateur reçoit une confirmation par email
6. ✅ Un admin peut gérer les commandes
7. ✅ Un utilisateur peut consulter ses commandes

**= MARKETPLACE OPÉRATIONNELLE ! 🚀**

---

## 📞 SUPPORT & RESSOURCES

### Documentation
- Flask: https://flask.palletsprojects.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- Stripe: https://stripe.com/docs
- Bootstrap: https://getbootstrap.com/

### Exemples de code
- Voir `services/` pour la logique métier
- Voir `routes/` pour les routes existantes
- Voir `templates/admin/` pour les templates admin

---

**Date**: 23 novembre 2025
**Priorité**: 🔴 CRITIQUE
**Durée estimée**: 7 jours
**Difficulté**: ⭐⭐⭐ (Moyenne)
