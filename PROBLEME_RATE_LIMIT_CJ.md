# Problème Rate Limit API CJ - Résolu Partiellement

**Date:** 4 février 2026, 23h20

## Problème Identifié

L'API CJ Dropshipping bloque toutes les requêtes avec un **rate limit 429** (trop de requêtes).

### Cause Racine

**Celery Beat** tournait en permanence depuis 16h50 et sollicitait l'API CJ avec des tâches planifiées :

```python
# celery_app.py - Tâches qui sollicitaient l'API CJ
'sync-cj-stock-hourly': {
    'task': 'tasks.cj_sync_tasks.sync_stock_task',
    'schedule': crontab(minute=30),  # Toutes les heures à XX:30
},

'sync-cj-orders-every-30min': {
    'task': 'tasks.cj_sync_tasks.sync_orders_task',
    'schedule': 1800.0,  # Toutes les 30 minutes
},
```

Ces tâches ont bombardé l'API CJ pendant **7 heures** (16h50 → 23h20), déclenchant le rate limit.

## Actions Effectuées

### 1. Arrêt de Celery Beat ✓
```powershell
Stop-Process -Id 18308 -Force  # PID du processus Celery beat
```

### 2. Nettoyage du Cache Redis ✓
```powershell
redis-cli FLUSHDB
```

### 3. Vérification TonyAlpha80 ✓
- TonyAlpha80 est un projet PHP (pas Python)
- Aucun processus Celery actif
- Pas de conflit entre les deux projets

### 4. Test de l'API CJ ✗
Le rate limit **429 est toujours actif côté serveur CJ**.

## Statut Actuel

❌ **API CJ bloquée** - Rate limit 429 actif
✅ **Celery arrêté** - Plus de sollicitation automatique
✅ **Cache nettoyé** - Prêt pour nouvelle tentative

## Solutions

### Solution Immédiate (Recommandée)

**Attendre 24-48 heures** que CJ lève automatiquement le rate limit.

### Solution Alternative 1 : Contacter le Support CJ

Si urgent, contactez le support CJ Dropshipping :
- Email : support@cjdropshipping.com
- Expliquez que vous avez eu un problème technique avec Celery
- Demandez la levée du rate limit

### Solution Alternative 2 : Utiliser des Credentials Différents

Si vous avez un autre compte CJ :
1. Modifiez `.env` :
   ```env
   CJ_EMAIL=autre_email@gmail.com
   CJ_PASSWORD=autre_password
   CJ_DEV_KEY=autre_dev_key
   ```
2. Redémarrez Flask

## Prévention Future

### 1. Désactiver Celery Beat en Développement

Modifiez `celery_app.py` pour désactiver les tâches planifiées en dev :

```python
import os

# Ne pas activer beat_schedule en développement
if os.getenv('FLASK_ENV') != 'development':
    celery.conf.update(
        beat_schedule={
            # ... tâches planifiées
        }
    )
```

### 2. Augmenter les Délais

Dans `.env`, augmentez le délai entre requêtes :
```env
CJ_RATE_LIMIT_DELAY=3  # Au lieu de 1
```

### 3. Limiter les Synchronisations Automatiques

Réduisez la fréquence des tâches dans `celery_app.py` :
```python
'sync-cj-stock-hourly': {
    'task': 'tasks.cj_sync_tasks.sync_stock_task',
    'schedule': crontab(hour='*/6', minute=30),  # Toutes les 6h au lieu de 1h
},
```

### 4. Utiliser un Script de Démarrage Sécurisé

Créez `start_dev.bat` :
```batch
@echo off
echo Démarrage MultiProShop en mode développement
echo ATTENTION: Celery Beat désactivé pour éviter rate limit
python app.py
```

## Commandes Utiles

### Vérifier les Processus Celery
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*celery*"}
```

### Arrêter Tous les Processus Celery
```powershell
Get-Process celery | Stop-Process -Force
```

### Vérifier le Cache Redis
```powershell
redis-cli KEYS "*cj*"
```

### Nettoyer le Cache Redis
```powershell
redis-cli FLUSHDB
```

## Prochaines Étapes

1. ⏳ **Attendre 24-48h** que le rate limit soit levé
2. 🔧 **Modifier celery_app.py** pour désactiver beat en dev
3. 📝 **Documenter** la procédure de démarrage sécurisée
4. ✅ **Tester** la synchronisation manuelle après levée du rate limit

## Notes

- Le rate limit CJ est **côté serveur**, pas local
- Le nettoyage du cache Redis ne lève pas le rate limit CJ
- Celery Beat doit être utilisé **uniquement en production**
- En développement, privilégier la **synchronisation manuelle**
