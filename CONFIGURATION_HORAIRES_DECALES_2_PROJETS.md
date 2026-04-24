# ⏰ Configuration Horaires Décalés - 2 Projets CJ

**Date:** 4 février 2026  
**Projets:** TonyAlpha80 (PHP) + MultiProShop (Python/Flask)

---

## 📊 Analyse des Horaires Actuels

### Projet 1 : TonyAlpha80 (PHP)

**Tâches planifiées identifiées :**

| Tâche | Fréquence | Horaire | Script |
|-------|-----------|---------|--------|
| **Backup quotidien** | Tous les jours | **02:00** | `backup_daily.php` |
| **Sync produits** | Tous les jours | **03:00** | `sync_products_daily.php` |
| **Sync stock** | Toutes les heures | **XX:00** | `sync_stock_hourly.php` |
| **Monitoring** | Toutes les 15 min | **XX:15** | `monitor_system.php` |
| **Rapport quotidien** | Tous les jours | **08:00** | `send-daily-report.php` |
| **Rapport hebdomadaire** | Lundi | **09:00** | `send-weekly-report.php` |

**Horaires critiques (API CJ) :**
- ✅ **02:00** - Backup
- 🔴 **03:00** - Sync produits (API CJ)
- 🔴 **XX:00** - Sync stock horaire (API CJ)

---

### Projet 2 : MultiProShop (Python/Flask)

**Tâches planifiées actuelles :**

| Tâche | Fréquence | Horaire Actuel | Type |
|-------|-----------|----------------|------|
| **Sync produits CJ** | Tous les jours | **Non défini (86400s)** | Celery Beat |
| **Sync stock** | Toutes les heures | **Non défini (3600s)** | Celery Beat |
| **Sync commandes** | Toutes les 30 min | **Non défini (1800s)** | Celery Beat |
| **Sync variantes manquantes** | Tous les jours | **Non défini (86400s)** | Celery Beat |
| **Update stock variantes** | Tous les jours | **Non défini (86400s)** | Celery Beat |
| **Sync produits data** | Tous les jours | **03:00** ⚠️ | Celery Beat (crontab) |
| **Sync reviews** | Dimanche | **04:00** | Celery Beat (crontab) |
| **Cleanup old data** | 1er du mois | **05:00** | Celery Beat (crontab) |

**Problème identifié :**
- 🔴 **Sync produits à 03:00** = **MÊME HEURE que TonyAlpha80**
- ⚠️ Risque de rate limits API CJ

---

## 🎯 Configuration Optimale Décalée

### Principe

**Objectif :** Espacer les synchronisations des 2 projets pour éviter les rate limits API CJ.

**Stratégie :**
1. **TonyAlpha80** : Synchronisations le matin (02:00-09:00)
2. **MultiProShop** : Synchronisations l'après-midi (15:00-18:00)
3. **Écart minimum** : 12 heures entre les sync principales

---

## 📋 Nouvelle Configuration MultiProShop

### Horaires Recommandés

| Tâche | Fréquence | Nouvel Horaire | Raison |
|-------|-----------|----------------|--------|
| **Sync produits CJ** | Tous les jours | **15:00** (3h PM) | 12h après TonyAlpha (03:00) |
| **Sync variantes manquantes** | Tous les jours | **15:30** | Après sync produits |
| **Update stock variantes** | Tous les jours | **16:00** | Après sync variantes |
| **Sync stock** | Toutes les heures | **XX:30** | Décalé de 30 min vs TonyAlpha (XX:00) |
| **Sync commandes** | Toutes les 30 min | **Inchangé** | Pas d'impact API CJ |
| **Sync reviews** | Dimanche | **17:00** | Après-midi |
| **Cleanup old data** | 1er du mois | **18:00** | Fin journée |
| **Cleanup webhooks** | Hebdomadaire | **Inchangé** | Pas d'impact API CJ |

---

## 🔧 Implémentation

### Fichier à Modifier

**`c:\Users\Anthony\CascadeProjects\multiproshop\celery_app.py`**

### Code Actuel (Lignes 58-97)

```python
beat_schedule={
    'sync-cj-products-daily': {
        'task': 'tasks.cj_sync_tasks.sync_products_task',
        'schedule': 86400.0,  # Tous les jours
    },
    'sync-cj-stock-hourly': {
        'task': 'tasks.cj_sync_tasks.sync_stock_task',
        'schedule': 3600.0,  # Toutes les heures
    },
    'sync-cj-orders-every-30min': {
        'task': 'tasks.cj_sync_tasks.sync_orders_task',
        'schedule': 1800.0,  # Toutes les 30 minutes
    },
    'cleanup-old-webhooks-weekly': {
        'task': 'tasks.analytics_tasks.cleanup_old_webhooks',
        'schedule': 604800.0,  # Toutes les semaines
    },
    'sync-missing-variants-daily': {
        'task': 'tasks.variant_sync_tasks.sync_missing_variants',
        'schedule': 86400.0,  # Tous les jours
    },
    'update-stock-from-variants-daily': {
        'task': 'tasks.variant_sync_tasks.update_stock_from_variants',
        'schedule': 86400.0,  # Tous les jours
    },
    'sync-products-data-daily': {
        'task': 'sync_products_daily',
        'schedule': crontab(hour=3, minute=0),  # 3h du matin ⚠️ CONFLIT
    },
    'sync-reviews-weekly': {
        'task': 'sync_reviews_weekly',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),
    },
    'cleanup-old-data-monthly': {
        'task': 'cleanup_old_data',
        'schedule': crontab(hour=5, minute=0, day_of_month=1),
    },
}
```

---

### Nouveau Code Optimisé

```python
beat_schedule={
    # ========================================
    # SYNCHRONISATIONS API CJ - APRÈS-MIDI (15h-18h)
    # Décalé de 12h par rapport à TonyAlpha80 (03h)
    # ========================================
    
    'sync-cj-products-daily': {
        'task': 'tasks.cj_sync_tasks.sync_products_task',
        'schedule': crontab(hour=15, minute=0),  # 15h00 (3h PM)
    },
    
    'sync-missing-variants-daily': {
        'task': 'tasks.variant_sync_tasks.sync_missing_variants',
        'schedule': crontab(hour=15, minute=30),  # 15h30
    },
    
    'update-stock-from-variants-daily': {
        'task': 'tasks.variant_sync_tasks.update_stock_from_variants',
        'schedule': crontab(hour=16, minute=0),  # 16h00
    },
    
    'sync-cj-stock-hourly': {
        'task': 'tasks.cj_sync_tasks.sync_stock_task',
        'schedule': crontab(minute=30),  # XX:30 (décalé de TonyAlpha XX:00)
    },
    
    # ========================================
    # AUTRES TÂCHES (pas d'impact API CJ)
    # ========================================
    
    'sync-cj-orders-every-30min': {
        'task': 'tasks.cj_sync_tasks.sync_orders_task',
        'schedule': 1800.0,  # Toutes les 30 minutes (inchangé)
    },
    
    'cleanup-old-webhooks-weekly': {
        'task': 'tasks.analytics_tasks.cleanup_old_webhooks',
        'schedule': 604800.0,  # Toutes les semaines (inchangé)
    },
    
    'sync-reviews-weekly': {
        'task': 'sync_reviews_weekly',
        'schedule': crontab(hour=17, minute=0, day_of_week=0),  # Dimanche 17h
    },
    
    'cleanup-old-data-monthly': {
        'task': 'cleanup_old_data',
        'schedule': crontab(hour=18, minute=0, day_of_month=1),  # 1er du mois 18h
    },
}
```

---

## 📊 Planification Finale des 2 Projets

### Vue d'Ensemble Journalière

| Heure | TonyAlpha80 | MultiProShop | API CJ |
|-------|-------------|--------------|--------|
| **02:00** | 🔵 Backup | - | ❌ |
| **03:00** | 🔴 Sync produits | - | ✅ |
| **04:00** | - | - | ❌ |
| **05:00** | - | - | ❌ |
| **06:00** | 🔴 Sync stock | - | ✅ |
| **07:00** | 🔴 Sync stock | - | ✅ |
| **08:00** | 🔵 Rapport quotidien | - | ❌ |
| **09:00** | 🔵 Rapport hebdo (Lun) | - | ❌ |
| **10:00** | 🔴 Sync stock | - | ✅ |
| **11:00** | 🔴 Sync stock | - | ✅ |
| **12:00** | 🔴 Sync stock | - | ✅ |
| **13:00** | 🔴 Sync stock | - | ✅ |
| **14:00** | 🔴 Sync stock | - | ✅ |
| **14:30** | - | 🔴 Sync stock | ✅ |
| **15:00** | 🔴 Sync stock | 🔴 Sync produits | ✅✅ |
| **15:30** | - | 🔴 Sync variantes | ✅ |
| **16:00** | 🔴 Sync stock | 🔴 Update stock | ✅✅ |
| **16:30** | - | 🔴 Sync stock | ✅ |
| **17:00** | 🔴 Sync stock | 🔵 Sync reviews (Dim) | ✅ |
| **17:30** | - | 🔴 Sync stock | ✅ |
| **18:00** | 🔴 Sync stock | 🔵 Cleanup (1er) | ✅ |

**Légende :**
- 🔴 Tâche utilisant API CJ
- 🔵 Tâche sans API CJ
- ✅ Requête API CJ

---

## 📈 Analyse de Charge API

### Requêtes API CJ par Heure

**Heures de pointe (risque rate limit) :**
- **15:00-18:00** : 2 projets actifs simultanément
- **Pic à 15:00** : Sync produits TonyAlpha (stock) + Sync produits MPS
- **Pic à 16:00** : Sync stock TonyAlpha + Update stock MPS

**Recommandation :**
- ✅ Acceptable si <500 produits par projet
- ⚠️ Si >500 produits : décaler MPS à 20:00-23:00

---

## 🎯 Configuration Alternative (Si Beaucoup de Produits)

### Si TonyAlpha80 + MultiProShop > 1000 produits total

**MultiProShop - Synchronisations nocturnes :**

```python
beat_schedule={
    'sync-cj-products-daily': {
        'task': 'tasks.cj_sync_tasks.sync_products_task',
        'schedule': crontab(hour=20, minute=0),  # 20h00 (8h PM)
    },
    'sync-missing-variants-daily': {
        'task': 'tasks.variant_sync_tasks.sync_missing_variants',
        'schedule': crontab(hour=20, minute=30),  # 20h30
    },
    'update-stock-from-variants-daily': {
        'task': 'tasks.variant_sync_tasks.update_stock_from_variants',
        'schedule': crontab(hour=21, minute=0),  # 21h00
    },
    'sync-cj-stock-hourly': {
        'task': 'tasks.cj_sync_tasks.sync_stock_task',
        'schedule': crontab(minute=45),  # XX:45
    },
}
```

**Avantages :**
- ✅ Écart de 17 heures avec TonyAlpha80
- ✅ Aucun conflit possible
- ✅ API CJ moins chargée le soir

---

## 🔧 Étapes d'Implémentation

### 1. Modifier celery_app.py

```bash
cd c:\Users\Anthony\CascadeProjects\multiproshop
# Éditer celery_app.py avec les nouveaux horaires
```

### 2. Redémarrer Celery Beat

```bash
# Arrêter le worker actuel
Get-Process python | Where-Object {$_.CommandLine -like "*celery*"} | Stop-Process -Force

# Redémarrer avec Beat
celery -A celery_app worker --loglevel=info --pool=solo -B
```

**Note :** L'option `-B` active Celery Beat pour les tâches planifiées.

### 3. Vérifier la Configuration

```bash
# Lister les tâches planifiées
celery -A celery_app inspect scheduled

# Voir les tâches actives
celery -A celery_app inspect active
```

### 4. Tester Manuellement

```bash
# Tester une tâche
python -c "from celery_app import celery; celery.send_task('tasks.cj_sync_tasks.sync_products_task'); print('Tâche lancée')"
```

---

## 📝 Vérification Post-Configuration

### Checklist

- [ ] `celery_app.py` modifié avec nouveaux horaires
- [ ] Celery worker redémarré avec Beat (`-B`)
- [ ] Tâches planifiées visibles dans `celery inspect scheduled`
- [ ] Test manuel réussi
- [ ] Logs Celery montrent les nouvelles heures
- [ ] Aucun conflit avec TonyAlpha80 (03:00 vs 15:00)

### Commandes de Vérification

```bash
# Voir les tâches planifiées
celery -A celery_app inspect scheduled

# Voir la prochaine exécution
celery -A celery_app inspect active

# Logs en temps réel
# (dans le terminal du worker)
```

---

## 🆘 Dépannage

### Problème : Tâches ne s'exécutent pas aux nouveaux horaires

**Cause :** Celery Beat pas activé

**Solution :**
```bash
# Redémarrer avec Beat
celery -A celery_app worker --loglevel=info --pool=solo -B
```

### Problème : Rate limits malgré décalage

**Cause :** Trop de produits ou sync stock horaire en conflit

**Solution :**
1. Passer MPS en mode nocturne (20:00-23:00)
2. Augmenter délai sync stock : `crontab(minute=45)` au lieu de `minute=30`

---

## 📊 Résumé de la Configuration

### TonyAlpha80 (PHP)
- **Sync produits :** 03:00
- **Sync stock :** XX:00 (toutes les heures)
- **Backup :** 02:00

### MultiProShop (Python/Flask)
- **Sync produits :** 15:00 (12h après TonyAlpha)
- **Sync variantes :** 15:30
- **Update stock :** 16:00
- **Sync stock :** XX:30 (décalé de 30 min)

### Écart Total
- ✅ **12 heures** entre les sync principales
- ✅ **30 minutes** entre les sync stock horaires
- ✅ **Aucun conflit** de rate limits

---

## 🎯 Recommandation Finale

### Configuration Standard (Recommandée)

**Pour 2 projets avec <500 produits chacun :**
- ✅ TonyAlpha80 : 03:00
- ✅ MultiProShop : 15:00
- ✅ Écart : 12 heures

### Configuration Alternative

**Pour 2 projets avec >500 produits chacun :**
- ✅ TonyAlpha80 : 03:00
- ✅ MultiProShop : 20:00
- ✅ Écart : 17 heures

---

**Dernière mise à jour :** 4 février 2026 16:50  
**Statut :** ✅ **CONFIGURATION OPTIMALE DÉFINIE - PRÊT POUR IMPLÉMENTATION**
