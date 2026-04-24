# 🧪 GUIDE DES TESTS - MultiProShop

**Guide rapide pour lancer et comprendre les tests**

---

## 🚀 DÉMARRAGE RAPIDE

### **1. Installer les dépendances**

```bash
# Dans le venv activé
pip install -r requirements_test.txt
```

**Dépendances installées** :
- `pytest` - Framework de test
- `pytest-flask` - Extension Flask pour pytest
- `pytest-cov` - Couverture de code
- `coverage` - Outil de couverture

---

### **2. Lancer les tests**

```bash
# Tous les tests
pytest

# Avec détails
pytest -v

# Avec couverture
pytest --cov=. --cov-report=html

# Tests spécifiques
pytest tests/test_models.py
pytest tests/test_routes.py
```

---

## 📊 RÉSULTATS ATTENDUS

### **Sortie normale**

```
========================= test session starts =========================
platform win32 -- Python 3.11.0, pytest-7.4.3, pluggy-1.3.0
rootdir: C:\Users\Anthony\CascadeProjects\multiproshop
configfile: pytest.ini
testpaths: tests
plugins: flask-1.3.0, cov-4.1.0
collected 35 items

tests/test_models.py ............                                [ 34%]
tests/test_routes.py .......................                     [100%]

========================== 35 passed in 4.52s ==========================
```

### **Avec couverture**

```
========================= test session starts =========================
...
tests/test_models.py ............                                [ 34%]
tests/test_routes.py .......................                     [100%]

---------- coverage: platform win32, python 3.11.0-final-0 -----------
Name                                Stmts   Miss  Cover
-------------------------------------------------------
models/user.py                         25      2    92%
models/product.py                      30      3    90%
models/category.py                     20      1    95%
models/order.py                        35      5    86%
routes/main.py                         15      0   100%
routes/auth.py                         40      8    80%
routes/products.py                     50     10    80%
routes/cart.py                         60     12    80%
routes/admin.py                       120     30    75%
-------------------------------------------------------
TOTAL                                 395     71    82%

========================== 35 passed in 5.23s ==========================
```

---

## 📁 STRUCTURE DES TESTS

```
tests/
├── __init__.py              # Package de tests
├── conftest.py              # Configuration + fixtures
├── test_models.py           # Tests des modèles
└── test_routes.py           # Tests des routes
```

---

## 🔧 FIXTURES DISPONIBLES

### **`app`**
Instance Flask de test avec base de données temporaire

```python
def test_something(app):
    with app.app_context():
        # Votre test ici
        pass
```

### **`client`**
Client de test Flask pour simuler des requêtes

```python
def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
```

### **`auth_client`**
Client authentifié en tant qu'admin

```python
def test_admin_page(auth_client):
    response = auth_client.get('/admin/')
    assert response.status_code == 200
```

### **`runner`**
Runner CLI de test

```python
def test_cli_command(runner):
    result = runner.invoke(my_command)
    assert result.exit_code == 0
```

---

## 📝 EXEMPLES DE TESTS

### **Test de modèle**

```python
def test_user_creation(app):
    """Test création d'un utilisateur"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            role_id=2
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.check_password('password123') is True
```

### **Test de route**

```python
def test_login_success(client):
    """Test connexion réussie"""
    response = client.post('/auth/login', data={
        'email': 'admin@test.com',
        'password': 'admin123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
```

### **Test AJAX**

```python
def test_add_to_cart(client, app):
    """Test ajout au panier"""
    with app.app_context():
        product = Product.query.first()
        
        response = client.post('/cart/add', 
            json={
                'product_id': product.id,
                'quantity': 1
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
```

---

## 🎯 COMMANDES UTILES

### **Tests basiques**

```bash
# Tous les tests
pytest

# Mode verbose
pytest -v

# Arrêter au premier échec
pytest -x

# Afficher les print()
pytest -s

# Tests en parallèle (plus rapide)
pytest -n auto
```

### **Tests spécifiques**

```bash
# Un fichier
pytest tests/test_models.py

# Une classe
pytest tests/test_models.py::TestUserModel

# Un test
pytest tests/test_models.py::TestUserModel::test_user_creation

# Par mot-clé
pytest -k "user"
pytest -k "not slow"
```

### **Couverture**

```bash
# Rapport dans le terminal
pytest --cov=.

# Rapport HTML (ouvre htmlcov/index.html)
pytest --cov=. --cov-report=html

# Rapport XML (pour CI/CD)
pytest --cov=. --cov-report=xml

# Afficher les lignes manquantes
pytest --cov=. --cov-report=term-missing
```

### **Markers**

```bash
# Tests unitaires uniquement
pytest -m unit

# Tests d'intégration uniquement
pytest -m integration

# Tests lents
pytest -m slow

# Exclure les tests lents
pytest -m "not slow"
```

---

## 📊 COUVERTURE DE CODE

### **Objectifs**

| Niveau | Couverture | Statut |
|--------|-----------|--------|
| Minimum | 70% | ⚠️ Acceptable |
| Bon | 80% | ✅ Recommandé |
| Excellent | 90%+ | 🌟 Idéal |

### **Zones prioritaires**

1. **Modèles** - 90%+ (critique)
2. **Routes principales** - 80%+ (important)
3. **Utilitaires** - 80%+ (important)
4. **Routes admin** - 70%+ (acceptable)

### **Voir le rapport**

```bash
# Générer le rapport HTML
pytest --cov=. --cov-report=html

# Ouvrir dans le navigateur
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
xdg-open htmlcov/index.html  # Linux
```

---

## 🐛 DÉBOGAGE

### **Afficher les erreurs détaillées**

```bash
# Traceback complet
pytest --tb=long

# Traceback court
pytest --tb=short

# Ligne seule
pytest --tb=line

# Pas de traceback
pytest --tb=no
```

### **Debugger interactif**

```bash
# Ouvrir pdb au premier échec
pytest --pdb

# Ouvrir pdb à chaque échec
pytest --pdb --maxfail=1
```

### **Dans le code**

```python
def test_something(client):
    response = client.get('/')
    
    # Point d'arrêt
    import pdb; pdb.set_trace()
    
    assert response.status_code == 200
```

---

## ✅ BONNES PRATIQUES

### **1. Noms de tests clairs**

```python
# ❌ Mauvais
def test_1():
    pass

# ✅ Bon
def test_user_creation_with_valid_data():
    pass
```

### **2. Un test = une assertion principale**

```python
# ❌ Mauvais
def test_user():
    user = create_user()
    assert user.id is not None
    assert user.username == 'test'
    assert user.email == 'test@test.com'
    assert user.role.name == 'client'

# ✅ Bon
def test_user_has_id_after_creation():
    user = create_user()
    assert user.id is not None

def test_user_has_correct_username():
    user = create_user()
    assert user.username == 'test'
```

### **3. Utiliser les fixtures**

```python
# ❌ Mauvais
def test_product_creation():
    app = create_app()
    with app.app_context():
        db.create_all()
        # Test...

# ✅ Bon
def test_product_creation(app):
    with app.app_context():
        # Test...
```

### **4. Nettoyer après les tests**

```python
def test_something(app):
    with app.app_context():
        # Créer des données
        user = User(...)
        db.session.add(user)
        db.session.commit()
        
        # Test...
        
        # Nettoyage automatique par fixture
```

---

## 🚨 PROBLÈMES COURANTS

### **1. Import errors**

```
ModuleNotFoundError: No module named 'models'
```

**Solution** :
```bash
# Installer le projet en mode dev
pip install -e .

# Ou ajouter au PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:."  # Linux/Mac
$env:PYTHONPATH = "."  # Windows PowerShell
```

### **2. Base de données**

```
sqlalchemy.exc.OperationalError: no such table: user
```

**Solution** : Les fixtures créent automatiquement les tables. Vérifiez que vous utilisez la fixture `app`.

### **3. Fixtures non trouvées**

```
fixture 'auth_client' not found
```

**Solution** : Vérifiez que `conftest.py` est dans le dossier `tests/`.

---

## 📈 AMÉLIORER LA COUVERTURE

### **1. Identifier les zones non testées**

```bash
pytest --cov=. --cov-report=term-missing
```

### **2. Ajouter des tests**

Priorités :
1. Routes critiques (paiement, commandes)
2. Logique métier complexe
3. Cas limites (erreurs, validations)

### **3. Tests à ajouter**

```python
# tests/test_payment.py
def test_stripe_payment_success(client):
    pass

def test_stripe_payment_failure(client):
    pass

# tests/test_api_providers.py
def test_cj_dropshipping_connection(app):
    pass

def test_product_sync_from_api(app):
    pass

# tests/test_webhooks.py
def test_webhook_stock_update(client):
    pass
```

---

## 🎯 CHECKLIST

- [ ] Dépendances installées (`requirements_test.txt`)
- [ ] Tests lancés (`pytest`)
- [ ] Tous les tests passent (35/35)
- [ ] Couverture > 80% (`pytest --cov`)
- [ ] Rapport HTML généré (`htmlcov/index.html`)
- [ ] Pas de warnings
- [ ] Documentation lue

---

## 📚 RESSOURCES

- [Documentation pytest](https://docs.pytest.org/)
- [pytest-flask](https://pytest-flask.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Testing Flask Applications](https://flask.palletsprojects.com/en/2.3.x/testing/)

---

**Bon testing ! 🧪**
