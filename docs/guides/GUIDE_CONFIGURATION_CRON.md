# 🕐 GUIDE DE CONFIGURATION CRON JOBS CJ

## 📋 VUE D'ENSEMBLE

Trois scripts CRON pour la synchronisation automatique avec CJ Dropshipping :

| Script | Fréquence | Fonction |
|--------|-----------|----------|
| `cron_sync_stock.py` | Quotidien (3h) | Synchronise le stock de tous les produits |
| `cron_sync_orders.py` | Horaire | Synchronise les statuts des commandes |
| `cron_sync_products.py` | Hebdomadaire (Lundi 2h) | Importe nouveaux produits CJ |

---

## 🔧 CONFIGURATION WINDOWS (Task Scheduler)

### Prérequis

1. Python installé
2. Application MultiProShop fonctionnelle
3. Identifiants CJ configurés dans `.env`

### Étape 1 : Créer un Script Batch

Créer `C:\Users\Anthony\CascadeProjects\multiproshop\run_cron.bat` :

```batch
@echo off
cd /d C:\Users\Anthony\CascadeProjects\multiproshop
python %1
```

### Étape 2 : Configurer Task Scheduler

#### CRON 1 : Synchronisation Stock (Quotidien)

1. Ouvrir **Task Scheduler** (Planificateur de tâches)
2. Cliquer **Create Basic Task** (Créer une tâche de base)
3. Nom : `MultiProShop - Sync Stock CJ`
4. Description : `Synchronisation quotidienne du stock CJ Dropshipping`
5. Trigger : **Daily** à **3:00 AM**
6. Action : **Start a program**
   - Program : `C:\Users\Anthony\CascadeProjects\multiproshop\run_cron.bat`
   - Arguments : `scripts\cron_sync_stock.py`
   - Start in : `C:\Users\Anthony\CascadeProjects\multiproshop`
7. Finish

#### CRON 2 : Synchronisation Commandes (Horaire)

1. Create Basic Task
2. Nom : `MultiProShop - Sync Orders CJ`
3. Description : `Synchronisation horaire des statuts de commandes CJ`
4. Trigger : **Daily** à **0:00 AM**
5. **Advanced** → Repeat task every **1 hour** for **24 hours**
6. Action : **Start a program**
   - Program : `C:\Users\Anthony\CascadeProjects\multiproshop\run_cron.bat`
   - Arguments : `scripts\cron_sync_orders.py`
   - Start in : `C:\Users\Anthony\CascadeProjects\multiproshop`
7. Finish

#### CRON 3 : Nouveaux Produits (Hebdomadaire)

1. Create Basic Task
2. Nom : `MultiProShop - Sync New Products CJ`
3. Description : `Import hebdomadaire nouveaux produits CJ`
4. Trigger : **Weekly** → **Monday** à **2:00 AM**
5. Action : **Start a program**
   - Program : `C:\Users\Anthony\CascadeProjects\multiproshop\run_cron.bat`
   - Arguments : `scripts\cron_sync_products.py`
   - Start in : `C:\Users\Anthony\CascadeProjects\multiproshop`
6. Finish

---

## 🐧 CONFIGURATION LINUX (Crontab)

### Éditer Crontab

```bash
crontab -e
```

### Ajouter les CRON Jobs

```cron
# Synchronisation stock CJ - Tous les jours à 3h
0 3 * * * cd /path/to/multiproshop && python scripts/cron_sync_stock.py >> logs/cron_stock.log 2>&1

# Synchronisation commandes CJ - Toutes les heures
0 * * * * cd /path/to/multiproshop && python scripts/cron_sync_orders.py >> logs/cron_orders.log 2>&1

# Nouveaux produits CJ - Tous les lundis à 2h
0 2 * * 1 cd /path/to/multiproshop && python scripts/cron_sync_products.py >> logs/cron_products.log 2>&1
```

### Créer le Dossier Logs

```bash
mkdir -p /path/to/multiproshop/logs
```

---

## 🧪 TESTS MANUELS

### Test 1 : Synchronisation Stock

```powershell
cd C:\Users\Anthony\CascadeProjects\multiproshop
python scripts/cron_sync_stock.py
```

**Résultat attendu :**
```
======================================================================
🔄 SYNCHRONISATION STOCK CJ DROPSHIPPING
======================================================================
Date: 2026-01-24 17:00:00
✅ Provider: CJ Dropshipping

📦 Produits à synchroniser: 15

[1/15] Produit: T-Shirt Premium
  CJ PID: 123456
  Variante ABC: 50 → 45
  ✅ Stock mis à jour: 45 unités

...

======================================================================
📊 RÉSUMÉ DE LA SYNCHRONISATION
======================================================================
Total produits: 15
✅ Succès: 15
❌ Erreurs: 0
🔄 Variantes mises à jour: 45
Taux de réussite: 100.0%
======================================================================
```

### Test 2 : Synchronisation Commandes

```powershell
python scripts/cron_sync_orders.py
```

**Résultat attendu :**
```
======================================================================
🔄 SYNCHRONISATION STATUTS COMMANDES CJ
======================================================================
Date: 2026-01-24 17:00:00
✅ Provider: CJ Dropshipping

📦 Commandes à synchroniser: 5

[1/5] Commande: ORD-2026-001
  CJ Order ID: 210823100016290555
  Statut actuel: processing
  ✅ Statut mis à jour: processing → shipped

...

======================================================================
📊 RÉSUMÉ DE LA SYNCHRONISATION
======================================================================
Total commandes: 5
✅ Succès: 5
🔄 Changements: 2
❌ Erreurs: 0
Taux de réussite: 100.0%
======================================================================
```

### Test 3 : Nouveaux Produits

```powershell
python scripts/cron_sync_products.py
```

**Résultat attendu :**
```
======================================================================
🔄 SYNCHRONISATION NOUVEAUX PRODUITS CJ
======================================================================
Date: 2026-01-24 17:00:00
✅ Provider: CJ Dropshipping

📦 Produits CJ actuels: 15
🔍 Recherche de nouveaux produits...

  ✅ Produit 789012 importé: Nouveau T-Shirt
  ⏭️ Produit 123456 existe déjà
  ✅ Produit 345678 importé: Casquette Premium

======================================================================
📊 RÉSUMÉ DE LA SYNCHRONISATION
======================================================================
Produits actuels: 15
✅ Nouveaux importés: 2
⏭️ Ignorés (déjà existants): 48
📦 Total après import: 17
======================================================================
```

---

## 📊 MONITORING

### Vérifier les Logs (Windows)

```powershell
# Créer un dossier logs
mkdir logs

# Rediriger la sortie vers un fichier
python scripts/cron_sync_stock.py > logs/cron_stock.log 2>&1
```

### Consulter les Dernières Exécutions

```powershell
# Dernières lignes du log stock
Get-Content logs/cron_stock.log -Tail 50

# Dernières lignes du log commandes
Get-Content logs/cron_orders.log -Tail 50
```

### Statistiques Base de Données

```sql
-- Dernières mises à jour stock
SELECT name, stock, updated_at 
FROM product 
WHERE cj_pid IS NOT NULL 
ORDER BY updated_at DESC 
LIMIT 10;

-- Dernières mises à jour commandes
SELECT order_number, status, cj_status, updated_at 
FROM order 
WHERE cj_order_id IS NOT NULL 
ORDER BY updated_at DESC 
LIMIT 10;

-- Produits importés cette semaine
SELECT COUNT(*) 
FROM product 
WHERE cj_pid IS NOT NULL 
AND created_at >= DATE('now', '-7 days');
```

---

## 🔍 DÉPANNAGE

### Problème 1 : Script ne s'exécute pas

**Cause :** Chemin Python incorrect

**Solution :**
```powershell
# Vérifier le chemin Python
where python

# Utiliser le chemin complet dans le batch
C:\Users\Anthony\AppData\Local\Programs\Python\Python39\python.exe scripts\cron_sync_stock.py
```

### Problème 2 : Erreur "Provider non trouvé"

**Cause :** Base de données non accessible

**Solution :**
```powershell
# Vérifier que la base existe
dir instance\multiproshop.db

# Vérifier la connexion
python -c "from app import app; from models.api_provider import ApiProvider; print(ApiProvider.query.all())"
```

### Problème 3 : Erreur API CJ

**Cause :** Identifiants CJ invalides ou API inaccessible

**Solution :**
```powershell
# Vérifier les identifiants dans .env
type .env | findstr CJ_

# Tester la connexion API
python -c "from services.api_providers.cj_dropshipping import CJDropshippingProvider; print('OK')"
```

### Problème 4 : Pas de mise à jour

**Cause :** Aucun produit/commande à synchroniser

**Solution :**
```sql
-- Vérifier les produits CJ
SELECT COUNT(*) FROM product WHERE cj_pid IS NOT NULL;

-- Vérifier les commandes CJ actives
SELECT COUNT(*) FROM order 
WHERE cj_order_id IS NOT NULL 
AND status IN ('pending', 'processing', 'shipped');
```

---

## ⚙️ CONFIGURATION AVANCÉE

### Personnaliser les Horaires

Modifier les horaires selon vos besoins :

```python
# Dans les scripts, vous pouvez ajouter des paramètres

# Exemple : Limiter le nombre de produits
python scripts/cron_sync_stock.py --limit 10

# Exemple : Synchroniser seulement une catégorie
python scripts/cron_sync_products.py --category "T-Shirts"
```

### Notifications par Email

Ajouter à la fin de chaque script :

```python
# Envoyer un email en cas d'erreur
if error_count > 0:
    from utils.email import send_email
    send_email(
        to='admin@multiproshop.com',
        subject='Erreur CRON Sync Stock',
        body=f'{error_count} erreurs détectées'
    )
```

### Logging Avancé

Créer un fichier de log rotatif :

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/cron_stock.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
logger.addHandler(handler)
```

---

## ✅ CHECKLIST DE CONFIGURATION

Avant de considérer les CRON configurés :

- [ ] Scripts testés manuellement avec succès
- [ ] Tâches créées dans Task Scheduler (Windows)
- [ ] Horaires configurés correctement
- [ ] Dossier `logs` créé
- [ ] Première exécution automatique vérifiée
- [ ] Logs consultés et validés
- [ ] Statistiques base de données cohérentes
- [ ] Emails de notification configurés (optionnel)

---

## 📈 IMPACT ATTENDU

### Synchronisation Stock
- ✅ Stock toujours à jour
- ✅ Évite les ventes de produits en rupture
- ✅ Améliore l'expérience client

### Synchronisation Commandes
- ✅ Statuts à jour en temps quasi-réel
- ✅ Emails automatiques aux clients
- ✅ Réduction du support client

### Nouveaux Produits
- ✅ Catalogue toujours frais
- ✅ Nouveautés CJ automatiquement disponibles
- ✅ Gain de temps administratif

---

**Date :** 24 Janvier 2026  
**Version :** 1.0  
**Statut :** ✅ Scripts prêts - Configuration manuelle requise
