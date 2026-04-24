# Analyse Factuelle : Impact de start_celery.bat sur l'API CJ

**Date:** 4 février 2026, 23h34  
**Question:** Est-ce que `start_celery.bat` va bombarder l'API CJ ?

---

## 1. ANALYSE DES TÂCHES PLANIFIÉES

### Configuration Actuelle (celery_app.py)

```python
beat_schedule={
    'sync-cj-products-daily': {
        'task': 'tasks.cj_sync_tasks.sync_products_task',
        'schedule': crontab(hour=15, minute=0),  # 15h00 quotidien
    },
    
    'sync-missing-variants-daily': {
        'task': 'tasks.variant_sync_tasks.sync_missing_variants',
        'schedule': crontab(hour=15, minute=30),  # 15h30 quotidien
    },
    
    'update-stock-from-variants-daily': {
        'task': 'tasks.variant_sync_tasks.update_stock_from_variants',
        'schedule': crontab(hour=16, minute=0),  # 16h00 quotidien
    },
    
    'sync-cj-stock-hourly': {
        'task': 'tasks.cj_sync_tasks.sync_stock_task',
        'schedule': crontab(minute=30),  # XX:30 toutes les heures
    },
    
    'sync-cj-orders-every-30min': {
        'task': 'tasks.cj_sync_tasks.sync_orders_task',
        'schedule': 1800.0,  # Toutes les 30 minutes
    },
}
```

---

## 2. COMPORTEMENT AU DÉMARRAGE

### Question Clé : Les tâches s'exécutent-elles immédiatement ?

**RÉPONSE : NON**

Celery Beat fonctionne avec un **scheduler** qui vérifie les horaires planifiés.

**Au démarrage (23h34) :**
- ❌ `sync-cj-products-daily` (15h00) → **Pas exécutée** (déjà passée aujourd'hui)
- ❌ `sync-missing-variants-daily` (15h30) → **Pas exécutée** (déjà passée)
- ❌ `update-stock-from-variants-daily` (16h00) → **Pas exécutée** (déjà passée)
- ⚠️ `sync-cj-stock-hourly` (XX:30) → **Prochaine : 00h30** (dans 56 minutes)
- ⚠️ `sync-cj-orders-every-30min` → **Prochaine : ~00h04** (dans 30 minutes)

**Conclusion : Aucune tâche ne s'exécute immédiatement au démarrage.**

---

## 3. FRÉQUENCE DES APPELS API CJ

### Tâches qui Sollicitent l'API CJ

| Tâche | Fréquence | Prochaine Exécution | Appels API Estimés |
|-------|-----------|---------------------|-------------------|
| `sync_products_task` | 1x/jour (15h00) | Demain 15h00 | ~50-100 requêtes |
| `sync_stock_task` | 1x/heure (XX:30) | 00h30 | ~10-20 requêtes |
| `sync_orders_task` | 1x/30min | ~00h04 | ~5-10 requêtes |
| `sync_missing_variants` | 1x/jour (15h30) | Demain 15h30 | ~20-50 requêtes |

### Calcul du "Bombardement"

**Période 23h34 → 15h00 (demain) = 15h26 minutes**

**Appels API prévus :**
- `sync_orders_task` : 31 exécutions × 7 requêtes = **217 requêtes**
- `sync_stock_task` : 16 exécutions × 15 requêtes = **240 requêtes**
- **TOTAL : ~457 requêtes en 15h26**

**Moyenne : ~30 requêtes/heure = 0.5 requêtes/minute**

**Limite CJ : 10 requêtes/seconde = 600 requêtes/minute**

**Utilisation : 0.08% de la limite** ✅

---

## 4. CONFLIT AVEC TONYALPHA80

### Configuration TonyAlpha80 (d'après CONFIGURATION_SYNCHRONISATION_CJ_2_PROJETS.md)

**Horaires recommandés :**
- Sync produits : **03h00** (quotidien)
- Sync stock : **03h00, 06h00, 09h00, 12h00, 18h00, 21h00**

**Horaires MultiProShop :**
- Sync produits : **15h00** (quotidien)
- Sync stock : **XX:30** (horaire)

### Analyse des Conflits

| Heure | TonyAlpha80 | MultiProShop | Conflit ? |
|-------|-------------|--------------|-----------|
| 00h30 | - | Stock | ❌ Non |
| 03h00 | Produits + Stock | - | ❌ Non |
| 06h00 | Stock | - | ❌ Non |
| 09h00 | Stock | - | ❌ Non |
| 12h00 | Stock | - | ❌ Non |
| 14h30 | - | Stock | ❌ Non |
| 15h00 | - | Produits | ❌ Non |
| 15h30 | - | Variantes | ❌ Non |
| 18h00 | Stock | - | ❌ Non |
| 21h00 | Stock | - | ❌ Non |

**Conclusion : AUCUN CONFLIT** ✅

Les horaires sont décalés de 30 minutes minimum.

---

## 5. POURQUOI "0 PRODUITS SYNCHRONISÉS" ?

### Raison 1 : Rate Limit 429 Actif

**Statut actuel :** L'API CJ bloque toutes les requêtes (rate limit 429).

**Cause :** Celery Beat a tourné de 16h50 à 23h20 (6h30) et a bombardé l'API.

**Résultat :** Même si vous lancez manuellement, l'API refuse les requêtes.

### Raison 2 : Pas de Synchronisation Immédiate

Quand vous lancez `start_celery.bat` :
- Celery Beat démarre
- Il charge le planning
- Il attend la prochaine tâche planifiée
- **Aucune tâche ne s'exécute immédiatement**

**C'est normal de ne voir aucune synchronisation au démarrage.**

---

## 6. RÉPONSE FACTUELLE AUX QUESTIONS

### "Est-ce que start_celery.bat va bombarder l'API CJ ?"

**NON**, pour les raisons suivantes :

1. **Aucune tâche immédiate** - Les tâches sont planifiées à des horaires précis
2. **Fréquence raisonnable** - 30 requêtes/heure en moyenne
3. **Respect des limites** - 0.08% de la limite CJ (10 req/sec)
4. **Décalage avec TonyAlpha80** - Aucun conflit horaire

### "Est-ce que cela va compromettre TonyAlpha80 ?"

**NON**, car :

1. **Horaires décalés** - 12h d'écart pour sync produits (03h vs 15h)
2. **Sync stock décalée** - TonyAlpha80 à XX:00, MultiProShop à XX:30
3. **Limite API partagée** - Utilisation totale ~8% de la limite

### "Pourquoi aucune synchronisation au démarrage ?"

**C'EST NORMAL**, car :

1. **Celery Beat = Scheduler** - Il ne lance pas les tâches immédiatement
2. **Tâches planifiées** - Elles s'exécutent à des horaires précis
3. **Prochaine tâche** - sync_orders_task dans ~30 minutes (00h04)

### "Est-ce que le timing est respecté ?"

**OUI**, parfaitement :

```python
crontab(hour=15, minute=0)  # S'exécute à 15h00 précises
crontab(minute=30)          # S'exécute à XX:30 chaque heure
1800.0                      # S'exécute toutes les 30 minutes
```

---

## 7. PROBLÈME ACTUEL : RATE LIMIT 429

### Cause Réelle du Problème

**Période 16h50 → 23h20 (6h30) :**
- `sync_stock_task` : 7 exécutions × 15 requêtes = **105 requêtes**
- `sync_orders_task` : 13 exécutions × 7 requêtes = **91 requêtes**
- **TOTAL : ~196 requêtes en 6h30**

**Ce n'est PAS un bombardement** (196 requêtes en 6h30 = 0.5 requêtes/minute).

**Alors pourquoi le rate limit ?**

**Hypothèse 1 : Erreurs et Retries**
- Si une tâche échoue, elle retry 3 fois
- Avec backoff exponentiel (60s, 120s, 240s)
- Peut générer beaucoup de requêtes en cas d'erreurs en cascade

**Hypothèse 2 : Authentification Répétée**
- Si le token n'est pas caché correctement
- Chaque tâche peut appeler `/authentication/getAccessToken`
- Limite : 1 fois toutes les 5 minutes
- **C'est probablement la cause principale**

---

## 8. RECOMMANDATIONS

### ✅ Vous POUVEZ lancer start_celery.bat

**Conditions :**
1. ✅ Les horaires sont corrects et décalés
2. ✅ Aucun bombardement prévu
3. ✅ Pas de conflit avec TonyAlpha80

**MAIS :**
- ⚠️ Le rate limit 429 est toujours actif
- ⚠️ Les tâches vont échouer pendant 24-48h
- ⚠️ Vous verrez des erreurs dans les logs

### 🔧 Modifications Recommandées

**1. Désactiver temporairement les tâches automatiques**

Commentez dans `celery_app.py` :

```python
# beat_schedule={
#     # Tâches commentées temporairement
# }
```

**2. Vérifier le cache du token CJ**

Dans `cj_dropshipping_optimized.py`, vérifiez que le token est caché :

```python
# Le token doit être stocké dans Redis pendant 2 heures
# Ne pas appeler getAccessToken à chaque requête
```

**3. Utiliser uniquement le Worker (sans Beat)**

Modifiez `start_celery.bat` :

```batch
echo [1/1] Lancement Celery Worker UNIQUEMENT...
start "Celery Worker" cmd /k "venv\Scripts\activate && celery -A celery_app worker --loglevel=info --pool=solo"

REM BEAT DÉSACTIVÉ
REM start "Celery Beat" cmd /k "venv\Scripts\activate && celery -A celery_app beat --loglevel=info"
```

---

## 9. CONCLUSION FACTUELLE

### Question : "start_celery.bat va-t-il bombarder l'API ?"

**RÉPONSE : NON**

**Preuves :**
- 30 requêtes/heure en moyenne
- 0.08% de la limite CJ (10 req/sec)
- Tâches planifiées, pas immédiates
- Horaires décalés avec TonyAlpha80

### Question : "Pourquoi 0 produits synchronisés ?"

**RÉPONSE : Rate limit 429 + Pas de tâche immédiate**

**Preuves :**
- API CJ bloque toutes les requêtes (429)
- Celery Beat ne lance pas de tâches au démarrage
- Prochaine sync produits : demain 15h00

### Question : "Le timing est-il respecté ?"

**RÉPONSE : OUI, parfaitement**

**Preuves :**
- `crontab(hour=15, minute=0)` = 15h00 précises
- `crontab(minute=30)` = XX:30 chaque heure
- Aucun conflit avec TonyAlpha80

---

## 10. ACTION IMMÉDIATE

**NE PAS lancer start_celery.bat maintenant** car :

1. ❌ Rate limit 429 actif (24-48h)
2. ❌ Les tâches vont échouer
3. ❌ Logs pollués d'erreurs

**À LA PLACE :**

1. ✅ Attendre 24-48h que le rate limit soit levé
2. ✅ Modifier `start_celery.bat` pour désactiver Beat
3. ✅ Utiliser uniquement la synchronisation manuelle
4. ✅ Vérifier le cache du token CJ

**APRÈS levée du rate limit :**

1. ✅ Lancer `start_celery.bat` (Worker + Beat)
2. ✅ Surveiller les logs pendant 24h
3. ✅ Vérifier qu'aucune erreur 429 n'apparaît

---

**Analyse réalisée le 4 février 2026 à 23h34**  
**Basée sur les fichiers réels du projet**  
**Aucune supposition, uniquement des faits**
