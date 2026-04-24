# Optimisations Performance Urgentes - MultiProShop

## 🔴 Problèmes Identifiés

Votre site est 4-5x plus lent que webox et tonyalpha80 à cause de :

1. **Context Processor lourd** - Charge TOUTES les catégories sur chaque page
2. **Requêtes N+1** - La sidebar génère 50-100+ requêtes DB par page
3. **Scheduler actif en dev** - Consomme des ressources inutilement
4. **40+ Blueprints** - Temps d'initialisation long

---

## ✅ Solutions Immédiates

### 1. OPTIMISER LE CONTEXT PROCESSOR (Priorité 1)

**Fichier : `app.py` lignes 59-69**

**Avant :**
```python
@app.context_processor
def inject_global_vars():
    from utils.datetime_utils import now_naive
    main_categories = Category.query.filter_by(
        level=1, is_active=True
    ).order_by(Category.order, Category.name).all()
    return {
        'now': now_naive(),
        'categories': Category.query.all(),  # ⚠️ TRÈS LOURD
        'main_categories': main_categories
    }
```

**Après (avec cache) :**
```python
@app.context_processor
def inject_global_vars():
    from utils.datetime_utils import now_naive
    
    # Utiliser le cache pour les catégories (5 minutes)
    @cache.memoize(timeout=300)
    def get_main_categories():
        return Category.query.filter_by(
            level=1, is_active=True
        ).order_by(Category.order, Category.name).all()
    
    return {
        'now': now_naive(),
        'main_categories': get_main_categories()
        # ⚠️ Supprimer 'categories': Category.query.all() si non utilisé
    }
```

**Gain estimé : 60-70% de réduction du temps de chargement**

---

### 2. OPTIMISER LA SIDEBAR (Priorité 1)

**Fichier : `templates/partials/sidebar_dynamic.html`**

**Problème :** Requêtes N+1 avec `.children.count()` et `.children.filter_by()`

**Solution A - Eager Loading dans le Context Processor :**
```python
@app.context_processor
def inject_global_vars():
    from utils.datetime_utils import now_naive
    from sqlalchemy.orm import joinedload
    
    @cache.memoize(timeout=300)
    def get_main_categories_with_children():
        return Category.query.filter_by(
            level=1, is_active=True
        ).options(
            joinedload(Category.children).joinedload(Category.children)
        ).order_by(Category.order, Category.name).all()
    
    return {
        'now': now_naive(),
        'main_categories': get_main_categories_with_children()
    }
```

**Solution B - Créer une Route API Dédiée (Recommandé) :**

Créer `routes/categories_api.py` :
```python
from flask import Blueprint, jsonify
from models.category import Category
from extensions import cache

categories_api = Blueprint('categories_api', __name__)

@categories_api.route('/api/categories/sidebar')
@cache.cached(timeout=600)  # Cache 10 minutes
def get_sidebar_categories():
    """API optimisée pour la sidebar"""
    from sqlalchemy.orm import joinedload
    
    categories = Category.query.filter_by(
        level=1, is_active=True
    ).options(
        joinedload(Category.children).joinedload(Category.children)
    ).order_by(Category.order, Category.name).all()
    
    result = []
    for cat in categories:
        cat_data = {
            'id': cat.id,
            'name': cat.name,
            'icon': cat.icon,
            'children': []
        }
        
        for subcat in cat.children.filter_by(is_active=True).all():
            subcat_data = {
                'id': subcat.id,
                'name': subcat.name,
                'children_count': subcat.children.count()
            }
            cat_data['children'].append(subcat_data)
        
        result.append(cat_data)
    
    return jsonify(result)
```

Puis charger la sidebar en AJAX (chargement asynchrone).

**Gain estimé : 70-80% de réduction des requêtes DB**

---

### 3. DÉSACTIVER LE SCHEDULER EN DÉVELOPPEMENT (Priorité 2)

**Fichier : `app.py` lignes 181-188**

**Avant :**
```python
def init_scheduler(app):
    """Initialiser le scheduler de synchronisation"""
    from services.sync_scheduler import get_scheduler
    scheduler = get_scheduler(app)
    
    import atexit
    atexit.register(lambda: scheduler.shutdown())
```

**Après :**
```python
def init_scheduler(app):
    """Initialiser le scheduler de synchronisation"""
    # Ne démarrer le scheduler qu'en production
    if not app.config.get('DEBUG', True):
        from services.sync_scheduler import get_scheduler
        scheduler = get_scheduler(app)
        
        import atexit
        atexit.register(lambda: scheduler.shutdown())
    else:
        print("⚠️  Scheduler désactivé en mode développement")
```

**Gain estimé : 10-15% de réduction de la charge CPU**

---

### 4. LAZY LOADING DES BLUEPRINTS (Priorité 3)

**Fichier : `app.py` fonction `register_blueprints`**

Certains blueprints peuvent être chargés à la demande :

```python
def register_blueprints(app):
    """Enregistrer tous les blueprints"""
    
    # Blueprints essentiels (toujours chargés)
    from routes.main import main as main_blueprint
    from routes.auth import auth as auth_blueprint
    from routes.products import products as products_blueprint
    from routes.cart import cart_bp as cart_blueprint
    from routes.errors import errors_bp
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(products_blueprint, url_prefix='/products')
    app.register_blueprint(cart_blueprint, url_prefix='/cart')
    app.register_blueprint(errors_bp)
    
    # Blueprints admin (chargés seulement si nécessaire)
    if app.config.get('ENABLE_ADMIN', True):
        from routes.admin import admin_bp
        from routes.admin_cj_sync import bp as admin_cj_sync_bp
        # ... autres blueprints admin
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(admin_cj_sync_bp)
    
    # Blueprints API (optionnels)
    if app.config.get('ENABLE_API', True):
        from routes.api import api_blueprint
        app.register_blueprint(api_blueprint, url_prefix='/api')
```

**Gain estimé : 15-20% de réduction du temps de démarrage**

---

### 5. AJOUTER DES INDEX EN BASE DE DONNÉES

**Créer : `scripts/add_performance_indexes.py`**

```python
from app import create_app
from extensions import db

app = create_app()

with app.app_context():
    # Index pour les catégories
    db.session.execute("""
        CREATE INDEX IF NOT EXISTS idx_category_level_active 
        ON category(level, is_active);
    """)
    
    db.session.execute("""
        CREATE INDEX IF NOT EXISTS idx_category_parent_id 
        ON category(parent_id);
    """)
    
    # Index pour les produits
    db.session.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_category_active 
        ON product(category_id, is_active);
    """)
    
    db.session.commit()
    print("✅ Index de performance ajoutés")
```

**Exécuter :**
```powershell
python scripts/add_performance_indexes.py
```

**Gain estimé : 20-30% de réduction du temps des requêtes**

---

### 6. ACTIVER LA COMPRESSION GZIP

**Fichier : `config.py`**

Vérifier que la compression est bien activée :
```python
COMPRESS_MIMETYPES = [
    'text/html',
    'text/css',
    'text/xml',
    'application/json',
    'application/javascript',
]
COMPRESS_LEVEL = 6
COMPRESS_MIN_SIZE = 500
```

**Déjà configuré ✅**

---

## 📊 Résultats Attendus

Après application de ces optimisations :

| Optimisation | Gain Estimé | Priorité |
|--------------|-------------|----------|
| Context Processor avec cache | 60-70% | ⭐⭐⭐ |
| Sidebar optimisée (eager loading) | 70-80% | ⭐⭐⭐ |
| Scheduler désactivé en dev | 10-15% | ⭐⭐ |
| Lazy loading blueprints | 15-20% | ⭐⭐ |
| Index DB | 20-30% | ⭐⭐ |

**Gain total estimé : 3-4x plus rapide (comparable à webox et tonyalpha80)**

---

## 🎯 Plan d'Action Recommandé

### Phase 1 - Optimisations Immédiates (30 min)
1. ✅ Ajouter cache au context processor
2. ✅ Désactiver scheduler en dev
3. ✅ Ajouter index DB

### Phase 2 - Optimisations Sidebar (1h)
4. ✅ Implémenter eager loading
5. ✅ Tester les performances

### Phase 3 - Optimisations Avancées (optionnel)
6. ⚪ Lazy loading des blueprints
7. ⚪ API dédiée pour la sidebar

---

## 🔧 Commandes de Test

### Mesurer les performances avant/après :

```powershell
# Installer l'outil de benchmark
pip install locust

# Tester le temps de réponse
Measure-Command { Invoke-WebRequest -Uri "http://localhost:5000" }
```

### Analyser les requêtes SQL :

Ajouter temporairement dans `config.py` :
```python
SQLALCHEMY_ECHO = True  # Affiche toutes les requêtes SQL
```

---

## 📝 Notes Importantes

- **Redis doit être actif** pour que le cache fonctionne
- **Tester après chaque modification** pour valider les gains
- **Ne pas supprimer le cache en production** sans raison
- **Monitorer la mémoire** si vous utilisez beaucoup de cache

---

## ✅ Checklist de Validation

Après optimisations, vérifier :
- [ ] Temps de chargement page d'accueil < 500ms
- [ ] Nombre de requêtes SQL par page < 10
- [ ] Sidebar s'affiche rapidement
- [ ] Pas de ralentissement après navigation
- [ ] Redis fonctionne correctement

---

**Créé le :** 4 février 2026
**Statut :** À appliquer
