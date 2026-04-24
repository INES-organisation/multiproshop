# Réponses - Cache Flask, Stocks et Workers Celery

**Date:** 2 février 2026 19:40

---

## 1. 🔄 Faut-il Réactiver le Cache Flask ?

### ✅ OUI - Réactivez-le Maintenant

Le cache a été désactivé temporairement pour faciliter les tests des modifications du template. Maintenant que tout fonctionne, **vous devriez le réactiver** pour améliorer les performances.

### Comment Réactiver

**Fichier:** `routes/products.py` ligne 52

**Avant (désactivé) :**
```python
@products.route('/<int:product_id>')
# @cache.cached(timeout=600)  # Cache désactivé temporairement
def product_detail(product_id):
```

**Après (réactivé) :**
```python
@products.route('/<int:product_id>')
@cache.cached(timeout=600)  # Cache 10 minutes
def product_detail(product_id):
```

### Avantages du Cache

- ⚡ **Performance** : Pages produits 10x plus rapides
- 💾 **Réduction charge DB** : Moins de requêtes SQL
- 🚀 **Meilleure expérience** : Temps de chargement réduit
- 💰 **Économie ressources** : Moins de CPU/mémoire

### Durée du Cache

- **600 secondes = 10 minutes**
- Les pages produits sont mises en cache pendant 10 minutes
- Après 10 minutes, le cache est automatiquement rafraîchi

### Quand Vider le Cache Manuellement

Si vous modifiez des produits et voulez voir les changements immédiatement :

```bash
# Vider tout le cache Redis
redis-cli FLUSHALL

# Ou redémarrer Flask (vide le cache au démarrage)
```

---

## 2. 📊 Comment Vérifier la Synchronisation des Stocks ?

### État Actuel des Stocks

**Résultats de la vérification :**

```
Produits CJ: 883
Produits avec stock: 783 (88.7%)
Total variantes: 3642
Variantes avec stock: 2376 (65.2%)
```

### Interprétation

✅ **Très bon taux de synchronisation :**
- 88.7% des produits ont du stock
- 65.2% des variantes ont du stock
- 100 produits sans stock (normal - rupture chez le fournisseur)
- 1266 variantes sans stock (normal - certaines tailles/couleurs épuisées)

### Vérifier un Produit Spécifique

**Via Python :**
```python
from app import create_app
from models.product import Product

app = create_app()
app.app_context().push()

# Vérifier un produit par ID
product = Product.query.get(586)
print(f"Produit: {product.name}")
print(f"Stock: {product.stock}")
print(f"Variantes: {len(product.variants)}")

# Vérifier les variantes
for variant in product.variants:
    print(f"  - {variant.variant_key}: Stock {variant.stock}")
```

**Via Dashboard Admin :**
1. Allez sur `http://multiproshop.local/admin/products`
2. Cherchez le produit
3. Colonne "Stock" affiche le stock total
4. Cliquez sur "Modifier" pour voir les variantes

**Via Page Produit :**
1. Ouvrez `http://multiproshop.local/products/586`
2. Section "Options disponibles" affiche le stock de chaque variante
3. Indicateur vert = En stock
4. Indicateur rouge = Rupture de stock

### Script de Vérification Complète

**Créer :** `scripts/check_stock_sync.py`

```python
from app import create_app
from models.product import Product
from models.product_variant import ProductVariant

app = create_app()
app.app_context().push()

print("=== RAPPORT SYNCHRONISATION STOCKS ===\n")

# Produits
total_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
products_with_stock = Product.query.filter(
    Product.cj_pid.isnot(None), 
    Product.stock > 0
).count()
products_no_stock = total_products - products_with_stock

print(f"📦 PRODUITS CJ")
print(f"  Total: {total_products}")
print(f"  Avec stock: {products_with_stock} ({products_with_stock/total_products*100:.1f}%)")
print(f"  Sans stock: {products_no_stock} ({products_no_stock/total_products*100:.1f}%)")

# Variantes
total_variants = ProductVariant.query.count()
variants_with_stock = ProductVariant.query.filter(ProductVariant.stock > 0).count()
variants_no_stock = total_variants - variants_with_stock

print(f"\n🎨 VARIANTES")
print(f"  Total: {total_variants}")
print(f"  Avec stock: {variants_with_stock} ({variants_with_stock/total_variants*100:.1f}%)")
print(f"  Sans stock: {variants_no_stock} ({variants_no_stock/total_variants*100:.1f}%)")

# Top 10 produits avec le plus de variantes
print(f"\n🏆 TOP 10 PRODUITS (plus de variantes)")
products = Product.query.filter(Product.cj_pid.isnot(None)).all()
products_sorted = sorted(products, key=lambda p: len(p.variants), reverse=True)[:10]

for i, p in enumerate(products_sorted, 1):
    variants_count = len(p.variants)
    variants_stock = sum(1 for v in p.variants if v.stock > 0)
    print(f"  {i}. {p.name[:50]}")
    print(f"     Variantes: {variants_count} | Avec stock: {variants_stock}")

# Produits sans variantes
products_no_variants = Product.query.filter(
    Product.cj_pid.isnot(None),
    ~Product.variants.any()
).count()

print(f"\n⚠️  PRODUITS SANS VARIANTES: {products_no_variants}")

print("\n=== FIN DU RAPPORT ===")
```

**Lancer :**
```bash
python scripts/check_stock_sync.py
```

---

## 3. 🔧 Workers Celery - Processus et Synchronisation

### Qu'est-ce qu'un Worker Celery ?

Un **worker** est un processus en arrière-plan qui exécute des tâches asynchrones :
- Synchronisation produits
- Synchronisation variantes
- Synchronisation stocks
- Synchronisation avis
- Envoi d'emails
- Nettoyage de données

### Processus Actuel de Synchronisation

**Fichier:** `celery_app.py`

```python
beat_schedule = {
    # Synchronisation quotidienne produits (3h du matin)
    'sync-products-data-daily': {
        'task': 'sync_products_daily',
        'schedule': crontab(hour=3, minute=0),
    },
    
    # Synchronisation hebdomadaire avis (dimanche 4h)
    'sync-reviews-weekly': {
        'task': 'sync_reviews_weekly',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),
    },
    
    # Nettoyage mensuel (1er du mois 5h)
    'cleanup-old-data-monthly': {
        'task': 'cleanup_old_data',
        'schedule': crontab(hour=5, minute=0, day_of_month=1),
    },
}
```

### Que Synchronise le Worker ?

**1. Synchronisation Produits (quotidienne 3h) :**
- ✅ Informations produits (nom, description, prix)
- ✅ Images produits
- ✅ Catégories
- ✅ Spécifications techniques
- ✅ Stock global

**2. Synchronisation Variantes (manuelle ou automatique) :**
- ✅ Toutes les variantes (couleurs, tailles, etc.)
- ✅ Prix de chaque variante
- ✅ Stock de chaque variante
- ✅ Images de variantes
- ✅ SKU variantes

**3. Synchronisation Avis (hebdomadaire dimanche 4h) :**
- ✅ Avis clients depuis CJ API
- ✅ Notes moyennes
- ✅ Commentaires
- ✅ Photos d'avis

**4. Nettoyage (mensuel 1er du mois 5h) :**
- ✅ Suppression anciennes données temporaires
- ✅ Optimisation base de données
- ✅ Nettoyage logs

### Comment Démarrer un Worker Manuellement

**Terminal 1 - Worker :**
```bash
celery -A celery_app worker --loglevel=info --pool=solo
```

**Terminal 2 - Beat (Scheduler) :**
```bash
celery -A celery_app beat --loglevel=info
```

**Terminal 3 - Flower (Monitoring) :**
```bash
celery -A celery_app flower --port=5555
```

### Tâches Disponibles

**Fichier:** `tasks/product_sync_tasks.py`

1. **`sync_products_daily`** : Synchronise tous les produits
2. **`sync_reviews_weekly`** : Synchronise les avis
3. **`cleanup_old_data`** : Nettoie les anciennes données

**Lancer manuellement une tâche :**
```python
from tasks.product_sync_tasks import sync_products_daily

# Lancer immédiatement
sync_products_daily.delay()

# Ou via le dashboard admin
# http://multiproshop.local/admin/celery/dashboard
```

---

## 4. 🎮 Dashboard Celery - Bouton "Démarrer Workers"

### Problème Identifié

Le dashboard a un bouton "Arrêter Workers" mais pas de bouton "Démarrer Workers".

### Pourquoi ?

Les workers Celery sont des **processus système** qui doivent être lancés depuis le terminal, pas depuis l'interface web. C'est une limitation de sécurité.

### Solution : Boutons de Contrôle Disponibles

**Le dashboard permet de :**
- ✅ **Lancer des tâches** (synchronisation manuelle)
- ✅ **Voir le statut** des workers (actifs/inactifs)
- ✅ **Consulter les logs** en temps réel
- ✅ **Voir les statistiques** (produits, variantes, stocks)
- ❌ **Démarrer/Arrêter** les workers (doit être fait en terminal)

### Comment Vérifier si les Workers Sont Actifs

**Via Dashboard :**
1. Allez sur `http://multiproshop.local/admin/celery/dashboard`
2. Section "Statut Celery"
3. Indicateur vert = Workers actifs
4. Indicateur rouge = Workers inactifs

**Via Terminal :**
```bash
# Vérifier les processus Celery
Get-Process python | Where-Object {$_.CommandLine -like "*celery*"}

# Ou via Flower
# http://localhost:5555
```

### Démarrer les Workers (Si Inactifs)

**Script PowerShell :** `start_celery_workers.ps1`

```powershell
# Terminal 1 - Worker
Start-Process powershell -ArgumentList "-NoExit", "-Command", "celery -A celery_app worker --loglevel=info --pool=solo"

# Terminal 2 - Beat
Start-Process powershell -ArgumentList "-NoExit", "-Command", "celery -A celery_app beat --loglevel=info"

# Terminal 3 - Flower
Start-Process powershell -ArgumentList "-NoExit", "-Command", "celery -A celery_app flower --port=5555"

Write-Host "✅ Workers Celery démarrés !" -ForegroundColor Green
Write-Host "📊 Dashboard: http://localhost:5000/admin/celery/dashboard" -ForegroundColor Cyan
Write-Host "🌸 Flower: http://localhost:5555" -ForegroundColor Magenta
```

**Lancer :**
```bash
.\start_celery_workers.ps1
```

---

## 📋 Résumé des Réponses

### 1. Cache Flask
✅ **OUI, réactivez-le maintenant** pour améliorer les performances.
- Décommenter `@cache.cached(timeout=600)` dans `routes/products.py` ligne 52

### 2. Vérification Stocks
✅ **Très bonne synchronisation actuelle :**
- 88.7% des produits ont du stock
- 65.2% des variantes ont du stock
- Script de vérification disponible : `scripts/check_stock_sync.py`

### 3. Workers Celery
✅ **Processus de synchronisation :**
- **Quotidien (3h)** : Produits, prix, images, stock
- **Hebdomadaire (dimanche 4h)** : Avis clients
- **Mensuel (1er du mois 5h)** : Nettoyage
- **Manuel** : Via dashboard ou terminal

### 4. Démarrer Workers
⚠️ **Les workers ne peuvent pas être démarrés depuis le dashboard** (limitation sécurité).
- Utiliser le terminal : `celery -A celery_app worker --loglevel=info --pool=solo`
- Ou le script : `start_celery_workers.ps1`

---

## 🚀 Actions Recommandées

1. **Réactiver le cache Flask** (ligne 52 de `routes/products.py`)
2. **Vérifier que les workers sont actifs** (dashboard ou Flower)
3. **Lancer une synchronisation manuelle** si besoin (via dashboard)
4. **Créer le script de vérification stocks** pour monitoring régulier

---

**Dernière mise à jour:** 2 février 2026 19:40
