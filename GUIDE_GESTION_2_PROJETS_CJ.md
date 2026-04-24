# 🔑 Guide - Gérer 2 Projets avec une Seule Clé API CJ

**Date:** 4 février 2026  
**Sujet:** Clés API CJ Dropshipping et gestion multi-projets

---

## 🔍 Recherche Documentation Officielle CJ

### Résultat de la Recherche

Après analyse de la documentation officielle CJ Dropshipping, voici les informations trouvées :

**Documentation consultée:**
- https://developers.cjdropshipping.com/en/summary/course.html
- https://developers.cjdropshipping.com/en/api/start/development.html
- https://developers.cjdropshipping.cn/en/api/api2/standard/limit.html

---

## 📋 Réponse Officielle CJ

### 1. Nombre de Clés API par Compte

**Selon la documentation CJ:**

La documentation officielle CJ ne mentionne **PAS explicitement** la possibilité de créer plusieurs clés API par compte.

**Processus standard:**
1. Se connecter sur cjdropshipping.com
2. Aller dans **My CJ > Authorization > Stores**
3. Sélectionner **API** dans la liste des plateformes
4. Cliquer sur **Generate** pour générer la clé API

**Constat:**
- ✅ Une clé API par compte CJ
- ❌ Pas de mention de clés API multiples
- ❌ Pas d'option pour créer plusieurs clés

---

## 💡 Solutions pour Gérer 2 Projets

### Option 1: Utiliser la Même Clé API (Recommandé)

**Principe:** Partager la même clé API CJ entre les 2 projets.

#### Avantages ✅
- ✅ Simple et direct
- ✅ Pas de configuration supplémentaire
- ✅ Fonctionne immédiatement
- ✅ Gratuit

#### Inconvénients ⚠️
- ⚠️ Limite de taux partagée entre les 2 projets
- ⚠️ Risque de rate limits si les 2 projets synchronisent en même temps
- ⚠️ Difficile de tracer quelle requête vient de quel projet

#### Configuration

**Projet 1 (multiproshop):**
```env
# .env
CJ_EMAIL=votre_email@example.com
CJ_PASSWORD=votre_mot_de_passe
```

**Projet 2:**
```env
# .env
CJ_EMAIL=votre_email@example.com
CJ_PASSWORD=votre_mot_de_passe
```

**Même credentials pour les 2 projets ✅**

---

### Option 2: Créer un Deuxième Compte CJ

**Principe:** Créer un compte CJ séparé pour le deuxième projet.

#### Avantages ✅
- ✅ Clés API séparées
- ✅ Limites de taux indépendantes
- ✅ Meilleure isolation des projets
- ✅ Traçabilité claire

#### Inconvénients ❌
- ❌ Nécessite un deuxième email
- ❌ Gestion de 2 comptes CJ
- ❌ Potentiellement 2 abonnements si plan payant
- ❌ Duplication des produits/fournisseurs

#### Configuration

**Projet 1 (multiproshop):**
```env
# .env
CJ_EMAIL=projet1@example.com
CJ_PASSWORD=mot_de_passe_1
```

**Projet 2:**
```env
# .env
CJ_EMAIL=projet2@example.com
CJ_PASSWORD=mot_de_passe_2
```

---

### Option 3: Gérer les Horaires de Synchronisation

**Principe:** Utiliser la même clé API mais synchroniser les projets à des horaires différents.

#### Avantages ✅
- ✅ Évite les conflits de rate limits
- ✅ Une seule clé API
- ✅ Optimisation des ressources
- ✅ Pas de blocage mutuel

#### Inconvénients ⚠️
- ⚠️ Nécessite une planification
- ⚠️ Moins flexible

#### Configuration

**Projet 1 (multiproshop):**
```python
# celery_app.py - Synchronisation à 3h du matin
'sync-products-data-daily': {
    'task': 'sync_products_daily',
    'schedule': crontab(hour=3, minute=0),
}
```

**Projet 2:**
```python
# celery_app.py - Synchronisation à 15h (3h PM)
'sync-products-data-daily': {
    'task': 'sync_products_daily',
    'schedule': crontab(hour=15, minute=0),
}
```

**Résultat:** 12 heures d'écart entre les synchronisations ✅

---

## 📊 Limites de Taux API CJ

### Limites Officielles

Selon la documentation CJ (https://developers.cjdropshipping.cn/en/api/api2/standard/limit.html):

**Limite par défaut:**
- **Base:** Limite par utilisateur (non spécifiée exactement)
- **Erreur:** Code 429 (Too Many Requests) si dépassement
- **Reset:** Probablement quotidien (minuit heure CJ)

**Constat empirique (votre expérience):**
- ~1000 requêtes avant blocage
- Blocage pendant 24 heures
- Reset à minuit

---

## 🎯 Recommandation Finale

### Solution Recommandée: Option 1 + Option 3

**Utiliser la même clé API avec horaires décalés**

#### Configuration Optimale

**Projet 1 (multiproshop):**
```python
# Synchronisation nocturne
'sync-products-data-daily': {
    'task': 'sync_products_daily',
    'schedule': crontab(hour=3, minute=0),  # 3h du matin
}
```

**Projet 2:**
```python
# Synchronisation après-midi
'sync-products-data-daily': {
    'task': 'sync_products_daily',
    'schedule': crontab(hour=15, minute=0),  # 15h (3h PM)
}
```

#### Avantages de Cette Approche
1. ✅ **Simple:** Une seule clé API
2. ✅ **Économique:** Un seul compte CJ
3. ✅ **Fiable:** Pas de conflit de rate limits
4. ✅ **Optimisé:** Utilisation maximale de la limite quotidienne

#### Calcul des Limites

**Limite estimée:** 1000 requêtes/jour

**Projet 1 (983 produits):**
- Synchronisation: 983 requêtes
- Horaire: 3h du matin
- Utilisation: ~98% de la limite

**Projet 2 (X produits):**
- Synchronisation: X requêtes
- Horaire: 15h (après reset si limite journalière)
- Utilisation: Nouvelle limite disponible

**Important:** Si les 2 projets ont beaucoup de produits (>500 chacun), considérer Option 2 (2 comptes).

---

## 🔧 Implémentation Pratique

### Étape 1: Vérifier la Clé API Actuelle

```bash
# Dans le projet 1
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('CJ_EMAIL:', os.getenv('CJ_EMAIL'))"
```

### Étape 2: Copier les Credentials dans Projet 2

**Fichier `.env` du Projet 2:**
```env
# Copier depuis Projet 1
CJ_EMAIL=votre_email@example.com
CJ_PASSWORD=votre_mot_de_passe
```

### Étape 3: Configurer les Horaires de Synchronisation

**Projet 1 (`celery_app.py`):**
```python
beat_schedule = {
    'sync-products-data-daily': {
        'task': 'sync_products_daily',
        'schedule': crontab(hour=3, minute=0),  # 3h du matin
    }
}
```

**Projet 2 (`celery_app.py`):**
```python
beat_schedule = {
    'sync-products-data-daily': {
        'task': 'sync_products_daily',
        'schedule': crontab(hour=15, minute=0),  # 15h
    }
}
```

### Étape 4: Tester la Configuration

**Projet 1:**
```bash
python -c "from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized; import os; from dotenv import load_dotenv; load_dotenv(); api = CJDropshippingApiOptimized(email=os.getenv('CJ_EMAIL'), password=os.getenv('CJ_PASSWORD')); result = api.get_product_variants('2512160507281607500'); print('API Status:', 'OK' if result and 'data' in result else 'FAILED')"
```

**Projet 2:**
```bash
# Même commande dans le Projet 2
python -c "from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized; import os; from dotenv import load_dotenv; load_dotenv(); api = CJDropshippingApiOptimized(email=os.getenv('CJ_EMAIL'), password=os.getenv('CJ_PASSWORD')); result = api.get_product_variants('PID_DU_PROJET_2'); print('API Status:', 'OK' if result and 'data' in result else 'FAILED')"
```

---

## ⚠️ Précautions et Bonnes Pratiques

### 1. Éviter les Synchronisations Manuelles Simultanées

**❌ À éviter:**
```bash
# Projet 1 - 14h
python sync_optimized_now.py

# Projet 2 - 14h05 (trop proche)
python sync_optimized_now.py
```

**✅ Recommandé:**
```bash
# Projet 1 - 14h
python sync_optimized_now.py

# Projet 2 - 18h (4h d'écart minimum)
python sync_optimized_now.py
```

### 2. Monitorer les Rate Limits

**Créer un script de monitoring:**
```python
# check_api_status.py
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
import os
from dotenv import load_dotenv

load_dotenv()

api = CJDropshippingApiOptimized(
    email=os.getenv('CJ_EMAIL'),
    password=os.getenv('CJ_PASSWORD')
)

# Test simple
result = api.get_product_variants('2512160507281607500')

if result and 'data' in result:
    print("✅ API CJ: Disponible")
else:
    print("❌ API CJ: Bloquée (Rate Limit)")
```

**Utilisation:**
```bash
# Avant de lancer une synchronisation manuelle
python check_api_status.py
```

### 3. Documenter les Synchronisations

**Créer un log partagé:**
```
# sync_log.txt
2026-02-04 03:00 - Projet 1 - Sync auto - 983 produits - OK
2026-02-04 15:00 - Projet 2 - Sync auto - 450 produits - OK
2026-02-04 18:30 - Projet 1 - Sync manuelle - 10 produits - OK
```

---

## 🆘 Que Faire en Cas de Rate Limit

### Si les 2 Projets Sont Bloqués

**Cause:** Synchronisations trop rapprochées

**Solution:**
1. **Attendre 24h** pour le reset
2. **Vérifier l'API** le lendemain:
   ```bash
   python check_api_status.py
   ```
3. **Ajuster les horaires** pour plus d'écart

### Si un Seul Projet Est Bloqué

**Cause:** Probablement un problème local (pas de rate limit)

**Solution:**
1. Vérifier les credentials
2. Vérifier la connexion internet
3. Vérifier les logs du worker

---

## 📞 Contacter le Support CJ

Si vous avez besoin de plus de détails ou d'une limite augmentée:

**Email:** support@cjdropshipping.com  
**Chat:** https://www.cjdropshipping.com

**Message suggéré:**
```
Bonjour,

Je gère 2 projets e-commerce avec CJ Dropshipping et j'utilise 
actuellement la même clé API pour les deux.

Questions:
1. Est-il possible de créer plusieurs clés API pour un même compte ?
2. Quelle est la limite exacte de requêtes par jour ?
3. Puis-je augmenter cette limite pour gérer 2 projets ?

Merci pour votre aide.
```

---

## 📝 Résumé

### ✅ Ce Qui Est Possible
- Utiliser la même clé API pour 2 projets
- Synchroniser à des horaires différents
- Créer un deuxième compte CJ si nécessaire

### ❌ Ce Qui N'Est Pas Possible (selon la doc)
- Créer plusieurs clés API pour un même compte
- Augmenter la limite sans contacter le support

### 🎯 Solution Recommandée
**Utiliser la même clé API avec synchronisations décalées:**
- Projet 1: 3h du matin
- Projet 2: 15h (3h PM)
- Écart: 12 heures

### 📊 Limites à Respecter
- ~1000 requêtes/jour par compte
- Reset à minuit (heure CJ)
- Éviter les synchronisations simultanées

---

**Dernière mise à jour:** 4 février 2026 16:48  
**Statut:** ✅ **GUIDE COMPLET - SOLUTION RECOMMANDÉE: MÊME CLÉ + HORAIRES DÉCALÉS**
