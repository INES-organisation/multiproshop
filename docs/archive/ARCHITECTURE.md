# Architecture du Projet MultiProShop

## Structure MVC

Le projet suit une architecture **MVC (Model-View-Controller)** avec une couche de services supplémentaire pour une meilleure séparation des responsabilités.

### 📁 Organisation des dossiers

```
multiproshop/
├── models/              # Modèles de données (SQLAlchemy)
│   ├── user.py
│   ├── product.py
│   ├── category.py
│   ├── order.py
│   ├── cart.py
│   └── ...
│
├── views/               # Vues (Templates HTML)
│   └── templates/
│       ├── pages/       # Pages principales
│       ├── admin/       # Interface admin
│       ├── auth/        # Authentification
│       ├── cart/        # Panier
│       └── products/    # Produits
│
├── routes/              # Contrôleurs (Blueprints Flask)
│   ├── main.py          # Routes principales
│   ├── auth.py          # Authentification
│   ├── products.py      # Gestion produits
│   ├── cart.py          # Panier
│   ├── admin.py         # Administration
│   └── ...
│
├── services/            # Couche de services (Logique métier)
│   ├── auth_service.py      # Service d'authentification
│   ├── product_service.py   # Service produits
│   ├── cart_service.py      # Service panier
│   └── order_service.py     # Service commandes
│
├── static/              # Fichiers statiques (CSS, JS, images)
├── scripts/             # Scripts utilitaires
├── database/            # Configuration base de données
└── app.py               # Point d'entrée de l'application
```

## Composants de l'architecture

### 1. **Models (Modèles)** - `models/`

Les modèles représentent la structure des données et gèrent l'accès à la base de données via SQLAlchemy.

**Responsabilités :**
- Définir la structure des tables
- Relations entre entités
- Validation des données au niveau du modèle
- Méthodes spécifiques aux entités (ex: `set_password`, `check_password`)

**Exemple :**
```python
# models/user.py
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
```

### 2. **Views (Vues)** - `templates/`

Les vues sont les templates HTML qui définissent l'interface utilisateur.

**Responsabilités :**
- Affichage des données
- Interface utilisateur
- Formulaires
- Mise en page

**Technologies :**
- Jinja2 (moteur de templates)
- HTML/CSS
- JavaScript

### 3. **Controllers (Contrôleurs)** - `routes/`

Les contrôleurs gèrent les requêtes HTTP et orchestrent les interactions entre les services et les vues.

**Responsabilités :**
- Réception des requêtes HTTP
- Validation des données d'entrée
- Appel des services appropriés
- Rendu des templates
- Gestion des redirections et messages flash

**Exemple :**
```python
# routes/products.py
@products.route('/')
def list_products():
    products = ProductService.get_products_paginated(...)
    return render_template('pages/list.html', products=products)
```

### 4. **Services (Logique métier)** - `services/`

**Nouveauté !** Couche intermédiaire entre les contrôleurs et les modèles.

**Responsabilités :**
- Logique métier complexe
- Opérations sur plusieurs modèles
- Validation métier
- Transactions
- Réutilisabilité du code

**Avantages :**
- ✅ Code plus maintenable
- ✅ Meilleure testabilité
- ✅ Réutilisation de la logique
- ✅ Séparation des responsabilités
- ✅ Contrôleurs plus légers

**Services disponibles :**

#### `AuthService` - Authentification
```python
AuthService.register_user(username, email, password)
AuthService.authenticate_user(identifiant, password)
AuthService.authenticate_admin(identifiant, password)
```

#### `ProductService` - Gestion des produits
```python
ProductService.get_products_paginated(page, per_page, sort_by, category_id)
ProductService.search_products(query)
ProductService.get_product_by_id(product_id)
ProductService.get_related_products(product)
```

#### `CartService` - Gestion du panier
```python
CartService.add_to_cart(product_id, quantity)
CartService.remove_from_cart(product_id)
CartService.update_quantity(product_id, action)
CartService.get_cart_items()
CartService.clear_cart()
```

#### `OrderService` - Gestion des commandes
```python
OrderService.create_order_from_cart(user_id)
OrderService.get_user_orders(user_id)
OrderService.update_order_status(order_id, status)
OrderService.cancel_order(order_id)
```

## Flux de données

```
Requête HTTP
    ↓
Controller (routes/)
    ↓
Service (services/)
    ↓
Model (models/)
    ↓
Base de données
    ↓
Model
    ↓
Service
    ↓
Controller
    ↓
View (templates/)
    ↓
Réponse HTTP
```

## Bonnes pratiques

### ✅ À faire

1. **Contrôleurs légers** : Déléguer la logique métier aux services
2. **Services réutilisables** : Créer des méthodes génériques
3. **Validation en couches** : Valider au niveau contrôleur ET service
4. **Gestion des erreurs** : Retourner des tuples (success, message, data)
5. **Transactions** : Utiliser `db.session` dans les services

### ❌ À éviter

1. Ne pas mettre de logique métier dans les contrôleurs
2. Ne pas accéder directement aux modèles depuis les contrôleurs
3. Ne pas dupliquer la logique métier
4. Ne pas oublier les rollbacks en cas d'erreur

## Scripts utilitaires

Les scripts de maintenance et de test sont organisés dans `scripts/` :

- `create_admin.py` - Création d'un administrateur
- `init_admin.py` - Initialisation admin
- `test_admin_login.py` - Test de connexion admin
- `debug_*.py` - Scripts de débogage
- `fix_*.py` - Scripts de correction

## Extensions et configuration

- `extensions.py` - Extensions Flask (db, login_manager)
- `app.py` - Configuration et création de l'application
- `wsgi.py` - Point d'entrée WSGI pour le déploiement

## Technologies utilisées

- **Framework** : Flask
- **ORM** : SQLAlchemy
- **Authentification** : Flask-Login
- **Templates** : Jinja2
- **Base de données** : MySQL / SQLite
- **Serveur** : waohost

## Améliorations apportées

### ✨ Nouvelle architecture

1. **Couche de services** créée pour extraire la logique métier
2. **Scripts réorganisés** dans le dossier `scripts/`
3. **Contrôleurs refactorisés** pour utiliser les services
4. **Code plus maintenable** et testable

### 📊 Avant vs Après

**Avant :**
```python
# Logique métier dans le contrôleur
@cart.route('/add', methods=['POST'])
def add_to_cart():
    product = Product.query.get(product_id)
    if product.stock < quantity:
        flash('Stock insuffisant')
    cart[str(product_id)] = quantity
    session['cart'] = cart
```

**Après :**
```python
# Logique déléguée au service
@cart.route('/add', methods=['POST'])
def add_to_cart():
    success, message, product = CartService.add_to_cart(product_id, quantity)
    flash(message, 'success' if success else 'error')
```

## Conclusion

Cette architecture MVC avec couche de services offre :
- 🎯 Meilleure séparation des responsabilités
- 🔧 Code plus maintenable
- 🧪 Facilité de test
- 🔄 Réutilisabilité du code
- 📈 Scalabilité améliorée
