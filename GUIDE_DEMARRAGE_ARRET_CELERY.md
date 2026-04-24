# 🚀 Guide de Démarrage et Arrêt de la Synchronisation Automatique

**Date:** 4 février 2026 18:55  
**Système:** Celery Worker + Beat (Synchronisation CJ)

---

## ❓ La Synchronisation Démarre-t-elle Automatiquement ?

### ⚠️ NON - Démarrage Manuel Requis

**La synchronisation automatique NE démarre PAS toute seule au démarrage de Windows.**

Vous devez **lancer manuellement** les services Celery après chaque redémarrage :
- ❌ Pas de démarrage automatique au boot
- ❌ Pas de service Windows configuré
- ✅ Lancement manuel via PowerShell

---

## 🚀 Comment Lancer la Synchronisation Automatique

### Méthode 1 : Lancement Complet (Recommandé)

**Ouvrir 2 terminaux PowerShell dans le dossier du projet :**

#### Terminal 1 - Celery Worker
```powershell
# Naviguer vers le projet
cd C:\Users\Anthony\CascadeProjects\multiproshop

# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# Lancer le Worker
celery -A celery_app worker --loglevel=info --pool=solo
```

#### Terminal 2 - Celery Beat (Scheduler)
```powershell
# Naviguer vers le projet
cd C:\Users\Anthony\CascadeProjects\multiproshop

# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# Lancer Beat
celery -A celery_app beat --loglevel=info
```

**⚠️ Important :** Sous Windows, Worker et Beat doivent être lancés **séparément** (2 terminaux).

---

### Méthode 2 : Script de Lancement Rapide

**Créer un fichier `start_celery.bat` :**

```batch
@echo off
echo ========================================
echo Démarrage Celery MultiProShop
echo ========================================

cd C:\Users\Anthony\CascadeProjects\multiproshop

echo.
echo [1/2] Lancement Celery Worker...
start "Celery Worker" cmd /k "venv\Scripts\activate && celery -A celery_app worker --loglevel=info --pool=solo"

timeout /t 3 /nobreak > nul

echo [2/2] Lancement Celery Beat...
start "Celery Beat" cmd /k "venv\Scripts\activate && celery -A celery_app beat --loglevel=info"

echo.
echo ========================================
echo ✅ Celery démarré !
echo 2 fenêtres ouvertes (Worker + Beat)
echo ========================================
pause
```

**Utilisation :**
```powershell
# Double-cliquer sur start_celery.bat
# OU
.\start_celery.bat
```

---

### Méthode 3 : Lancement en Arrière-Plan (PowerShell)

```powershell
# Worker en arrière-plan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\Anthony\CascadeProjects\multiproshop; .\venv\Scripts\Activate.ps1; celery -A celery_app worker --loglevel=info --pool=solo"

# Beat en arrière-plan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\Anthony\CascadeProjects\multiproshop; .\venv\Scripts\Activate.ps1; celery -A celery_app beat --loglevel=info"
```

---

## 🛑 Comment Arrêter la Synchronisation Automatique

### Méthode 1 : Arrêt depuis les Terminaux

**Si lancé en mode interactif (2 terminaux) :**

1. **Terminal Worker :** Appuyer sur `Ctrl + C`
2. **Terminal Beat :** Appuyer sur `Ctrl + C`

**Attendre que les tâches en cours se terminent proprement.**

---

### Méthode 2 : Arrêt via PowerShell (Force)

```powershell
# Arrêter tous les processus Celery
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*celery*"} | Stop-Process -Force

# Vérifier qu'ils sont bien arrêtés
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*celery*"}
```

---

### Méthode 3 : Script d'Arrêt Rapide

**Créer un fichier `stop_celery.bat` :**

```batch
@echo off
echo ========================================
echo Arrêt Celery MultiProShop
echo ========================================

echo Recherche des processus Celery...
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like '*celery*'} | Stop-Process -Force"

timeout /t 2 /nobreak > nul

echo.
echo ✅ Celery arrêté !
echo ========================================
pause
```

**Utilisation :**
```powershell
.\stop_celery.bat
```

---

## 🎛️ Contrôle depuis l'Admin Dashboard

### ✅ Fonctionnalités Disponibles

**URL Dashboard :** `http://multiproshop.local/admin/celery/dashboard`

#### 1. Lancer des Synchronisations Manuelles

**Boutons disponibles :**

- **🔄 Sync Produits Manquants**
  - Synchronise uniquement les produits sans variantes
  - Tâche : `sync_missing_variants`
  - Clic sur le bouton → Tâche lancée immédiatement

- **🔄 Sync Tous les Produits**
  - Synchronise tous les produits CJ (par lots)
  - Tâche : `sync_all_variants`
  - Paramètres : batch_size=50, delay=600s

- **📦 Mettre à Jour Stocks**
  - Recalcule les stocks depuis les variantes
  - Tâche : `update_stock_from_variants`
  - Mise à jour immédiate

**Comment utiliser :**
```
1. Se connecter à l'admin
2. Aller sur /admin/celery/dashboard
3. Cliquer sur le bouton de la tâche souhaitée
4. Voir les logs en temps réel
5. Notification de succès/erreur
```

#### 2. Voir les Tâches en Cours

**Section "Tâches Actives" :**
- Liste des tâches en cours d'exécution
- Tâches planifiées (scheduled)
- Tâches en attente (reserved)

#### 3. Voir les Statistiques

**Informations affichées :**
- Nombre de workers actifs
- Tâches enregistrées
- Dernière synchronisation
- Produits CJ, variantes, catégories

---

### ❌ Fonctionnalités NON Disponibles

**Ce que vous NE POUVEZ PAS faire depuis l'admin :**

- ❌ **Démarrer les services Celery** (Worker + Beat)
  - Doit être fait via PowerShell/Terminal
  
- ❌ **Arrêter les services Celery** (Worker + Beat)
  - Doit être fait via PowerShell/Terminal ou Ctrl+C
  
- ❌ **Modifier les horaires de synchronisation**
  - Doit être fait dans `celery_app.py`
  
- ❌ **Activer/Désactiver les tâches planifiées**
  - Doit être fait dans `celery_app.py`

**Pourquoi ?**
- Celery Worker et Beat sont des **processus système**
- Ils doivent être lancés au niveau du système d'exploitation
- L'admin dashboard ne peut que **lancer des tâches ponctuelles**

---

## 📊 Vérifier que la Synchronisation Fonctionne

### 1. Vérifier les Services

```powershell
# Vérifier les processus Celery
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*celery*"}

# Devrait afficher 2 processus :
# - celery worker
# - celery beat
```

### 2. Vérifier les Tâches Planifiées

```powershell
cd C:\Users\Anthony\CascadeProjects\multiproshop
.\venv\Scripts\Activate.ps1

# Voir les tâches planifiées
celery -A celery_app inspect scheduled

# Voir les tâches actives
celery -A celery_app inspect active

# Voir les stats des workers
celery -A celery_app inspect stats
```

### 3. Vérifier depuis l'Admin Dashboard

```
1. Aller sur http://multiproshop.local/admin/celery/dashboard
2. Vérifier "Celery Status: Online"
3. Vérifier "Workers: 1" (ou plus)
4. Voir la section "Tâches Actives"
```

### 4. Vérifier les Logs

**Logs Worker :**
```
[2026-02-04 15:00:00] [Celery] Début sync produits
[2026-02-04 15:00:05] [Celery] ✅ Sync produits terminée: 50 produits
```

**Logs Beat :**
```
[2026-02-04 15:00:00] Scheduler: Sending due task sync-cj-products-daily
[2026-02-04 15:30:00] Scheduler: Sending due task sync-missing-variants-daily
```

---

## 🔄 Synchronisations Automatiques vs Manuelles

### Synchronisations Automatiques (Celery Beat)

**Requiert :** Worker + Beat lancés

| Tâche | Horaire | Description |
|-------|---------|-------------|
| Sync produits | 15:00 quotidien | Tous les produits CJ |
| Sync variantes | 15:30 quotidien | Produits sans variantes |
| Update stock | 16:00 quotidien | Recalcul depuis variantes |
| Sync stock | XX:30 horaire | Stock depuis API CJ |
| Sync commandes | Toutes les 30 min | Statuts commandes |
| Sync avis | Dimanche 17:00 | Avis clients |

**Avantages :**
- ✅ Automatique, pas d'intervention
- ✅ Horaires optimisés (décalés vs TonyAlpha80)
- ✅ Retry automatique en cas d'erreur

---

### Synchronisations Manuelles (Dashboard Admin)

**Requiert :** Worker lancé (Beat optionnel)

| Bouton | Tâche | Quand l'utiliser |
|--------|-------|------------------|
| Sync Produits Manquants | `sync_missing_variants` | Après ajout de nouveaux produits |
| Sync Tous les Produits | `sync_all_variants` | Synchronisation complète forcée |
| Mettre à Jour Stocks | `update_stock_from_variants` | Recalcul immédiat des stocks |

**Avantages :**
- ✅ Lancement immédiat (pas d'attente)
- ✅ Contrôle précis de ce qui est synchronisé
- ✅ Logs en temps réel dans le dashboard

---

## 🎯 Scénarios d'Utilisation

### Scénario 1 : Démarrage Quotidien

**Matin (avant 15h) :**
```powershell
# Lancer les services
.\start_celery.bat

# Vérifier dans l'admin dashboard
# http://multiproshop.local/admin/celery/dashboard
```

**Soir (fin de journée) :**
```powershell
# Arrêter les services
.\stop_celery.bat
```

---

### Scénario 2 : Synchronisation Urgente

**Si vous avez besoin de synchroniser immédiatement :**

1. **Vérifier que Worker est lancé**
   ```powershell
   Get-Process python | Where-Object {$_.CommandLine -like "*celery*worker*"}
   ```

2. **Si Worker n'est pas lancé :**
   ```powershell
   cd C:\Users\Anthony\CascadeProjects\multiproshop
   .\venv\Scripts\Activate.ps1
   celery -A celery_app worker --loglevel=info --pool=solo
   ```

3. **Aller sur le dashboard admin**
   - `http://multiproshop.local/admin/celery/dashboard`
   - Cliquer sur le bouton de synchronisation souhaité
   - Voir les logs en temps réel

---

### Scénario 3 : Redémarrage après Erreur

**Si Celery plante ou rate limit :**

1. **Arrêter tous les processus**
   ```powershell
   .\stop_celery.bat
   ```

2. **Attendre 5 minutes** (reset rate limit API CJ)

3. **Relancer les services**
   ```powershell
   .\start_celery.bat
   ```

4. **Vérifier les logs** pour confirmer le bon fonctionnement

---

## 📝 Résumé des Commandes

### Démarrage
```powershell
# Script rapide
.\start_celery.bat

# OU manuel (2 terminaux)
# Terminal 1: celery -A celery_app worker --loglevel=info --pool=solo
# Terminal 2: celery -A celery_app beat --loglevel=info
```

### Arrêt
```powershell
# Script rapide
.\stop_celery.bat

# OU manuel
# Ctrl+C dans chaque terminal
```

### Vérification
```powershell
# Processus
Get-Process python | Where-Object {$_.CommandLine -like "*celery*"}

# Tâches
celery -A celery_app inspect scheduled
celery -A celery_app inspect active
celery -A celery_app inspect stats
```

### Dashboard Admin
```
URL: http://multiproshop.local/admin/celery/dashboard

Actions disponibles:
- ✅ Lancer synchronisations manuelles
- ✅ Voir tâches en cours
- ✅ Voir statistiques
- ❌ Démarrer/Arrêter services (PowerShell requis)
```

---

## ⚠️ Points Importants

### À Retenir

1. **Démarrage Manuel Requis**
   - Celery ne démarre PAS automatiquement
   - Lancer Worker + Beat après chaque redémarrage Windows

2. **2 Processus Séparés sous Windows**
   - Worker (exécute les tâches)
   - Beat (planifie les tâches)
   - Ne peuvent pas être combinés avec `-B` sous Windows

3. **Dashboard Admin = Tâches Manuelles Uniquement**
   - Peut lancer des synchronisations ponctuelles
   - Ne peut PAS démarrer/arrêter les services Celery

4. **Horaires Décalés**
   - MultiProShop : 15h-18h
   - TonyAlpha80 : 3h-5h
   - Évite les conflits de rate limit API CJ

5. **Vérification Régulière**
   - Vérifier le dashboard admin quotidiennement
   - Surveiller les logs pour détecter les erreurs
   - Relancer si nécessaire après rate limit

---

**Dernière mise à jour :** 4 février 2026 18:55  
**Statut :** ✅ Guide complet de démarrage/arrêt
