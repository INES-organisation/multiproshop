# 🔄 GUIDE DE SYNCHRONISATION CJ DROPSHIPPING

## ⚠️ IMPORTANT : RATE LIMITING CJ

L'API CJ Dropshipping limite l'authentification à **1 requête toutes les 5 minutes**.

C'est **NORMAL** et géré automatiquement par le système.

---

## 📋 MÉTHODES DE SYNCHRONISATION

### Méthode 1 : Interface Web (RECOMMANDÉE) ✅

**Avantages** :
- Visuel et intuitif
- Gestion automatique du rate limiting
- Affichage en temps réel
- Pas besoin de ligne de commande

**Étapes** :

1. **Ouvrir la page catégories**
   ```
   http://multiproshop.local/admin/cj/categories
   ```

2. **Cliquer sur "Synchroniser depuis CJ"**
   - Un overlay de chargement s'affiche
   - La synchronisation démarre
   - Résultat affiché à la fin

3. **Attendre le résultat**
   - ✓ Succès : Nombre de catégories synchronisées
   - ✗ Erreur : Message d'erreur (ex: rate limit)

4. **Si rate limit (429)**
   - Attendre 5 minutes
   - Réessayer

---

### Méthode 2 : Script Python

**Pour les tests ou l'automatisation**

```bash
# Vérifier le statut
python scripts/check_cj_status.py

# Synchroniser les catégories
python scripts/test_sync_categories.py
```

**Si erreur 429** :
```
⏳ RATE LIMIT ACTIF
   Attendre encore : 4m 32s
```

Attendre le temps indiqué et réessayer.

---

## 🎯 WORKFLOW COMPLET

### 1️⃣ Première synchronisation (une fois)

**A. Synchroniser les catégories**
```
http://multiproshop.local/admin/cj/categories
→ Cliquer "Synchroniser depuis CJ"
→ Attendre (peut prendre 30-60 secondes)
→ Résultat : ~150 catégories synchronisées
```

**B. Vérifier les catégories**
- Les catégories s'affichent dans l'arborescence
- 3 niveaux visibles
- Compteur de produits par catégorie

### 2️⃣ Synchroniser les produits (par catégorie)

**A. Aller sur la page produits**
```
http://multiproshop.local/admin/cj/products
```

**B. Sélectionner une catégorie**
- Sidebar gauche : liste des catégories niveau 3
- Cliquer sur une catégorie (ex: "Sweaters")

**C. Synchroniser les produits**
- Bouton "Synchroniser" activé
- Cliquer dessus
- Attendre (30-60 secondes)
- Résultat : produits affichés dans la grille

### 3️⃣ Enrichir les produits (optionnel)

**A. Ouvrir un produit**
- Cliquer sur "Détails" sur une carte produit
- Modal s'ouvre avec les infos

**B. Enrichir**
- Bouton "Enrichir"
- Récupère les avis clients CJ
- Calcule la note moyenne

---

## 🔧 DÉPANNAGE

### Erreur 429 (Rate Limit)

**Symptôme** :
```
Too Many Requests, QPS limit is 1 time/300 seconds
```

**Solution** :
1. Attendre 5 minutes
2. Réessayer
3. C'est NORMAL - limitation CJ

**Vérifier le statut** :
```bash
python scripts/check_cj_status.py
```

### Erreur "Aucune catégorie récupérée"

**Causes possibles** :
1. Rate limit actif → Attendre
2. Identifiants CJ incorrects → Vérifier `.env`
3. API CJ indisponible → Réessayer plus tard

**Vérifier les identifiants** :
```bash
# Fichier .env
CJ_EMAIL=tonyalpha80@gmail.com
CJ_PASSWORD=764c2ca258df45818e15b7d0f7ea0264
CJ_DEV_KEY=764c2ca258df45818e15b7d0f7ea0264
```

### Pages vides

**Normal si** :
- Première utilisation
- Pas encore synchronisé

**Solution** :
1. Synchroniser les catégories d'abord
2. Puis synchroniser les produits

---

## 📊 STATISTIQUES

**Voir les stats globales** :
```bash
curl http://localhost:5000/admin/api/cj/stats
```

**Résultat** :
```json
{
  "products": {
    "total": 500,
    "synced": 450,
    "published": 200
  },
  "categories": {
    "total": 150,
    "level_1": 10,
    "level_2": 40,
    "level_3": 100
  }
}
```

---

## ⏰ FRÉQUENCE RECOMMANDÉE

| Action | Fréquence | Méthode |
|--------|-----------|---------|
| Catégories | 1x/semaine | Interface web |
| Produits | 1x/jour | Interface web |
| Stock | 1x/heure | API automatique |
| Enrichissement | À la demande | Interface web |

---

## 🚀 AUTOMATISATION (FUTUR)

**Phase 7** inclura :
- Tâches CRON automatiques
- Synchronisation nocturne
- Mise à jour stock en temps réel
- Notifications par email

---

## 📞 SUPPORT

**Logs** :
- Console du serveur Flask
- Affiche toutes les requêtes CJ
- Erreurs détaillées

**Documentation CJ** :
https://developers.cjdropshipping.com/

---

## ✅ CHECKLIST PREMIÈRE SYNC

- [ ] Serveur Flask démarré
- [ ] Page catégories accessible
- [ ] Clic sur "Synchroniser depuis CJ"
- [ ] Attendre 5 minutes si rate limit
- [ ] Catégories affichées
- [ ] Page produits accessible
- [ ] Catégorie sélectionnée
- [ ] Produits synchronisés
- [ ] Produits affichés

---

**Créé le** : 6 janvier 2026  
**Version** : 1.0  
**Projet** : MultiProShop - Intégration CJ
