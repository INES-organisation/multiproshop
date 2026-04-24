# 🚀 DÉMARRAGE RAPIDE - SYNCHRONISATION CJ

## ⚡ Démarrer le Worker en 30 secondes

### Windows

Double-cliquez sur :
```
start_sync_worker.bat
```

Ou en ligne de commande :
```bash
cd C:\Users\Anthony\CascadeProjects\multiproshop
start_sync_worker.bat
```

### Ligne de commande directe

```bash
cd C:\Users\Anthony\CascadeProjects\multiproshop
python workers\sync_worker.py
```

### Via Flask CLI

```bash
flask sync worker
```

---

## 📊 Voir les Statistiques

```bash
flask sync stats
```

**Résultat** :
```
📊 STATISTIQUES DE SYNCHRONISATION
==================================================
Total produits CJ:        500
Produits actifs:          450
Jamais synchronisés:      23
Synchronisés 24h:         127
Stock bas (<10):          15
Rupture de stock:         8
==================================================
✅ Peut synchroniser maintenant
```

---

## 🔄 Synchroniser Manuellement

### Un batch de produits

```bash
flask sync batch --batch-size 10
```

### Un produit spécifique

```bash
flask sync product 42
```

---

## 🌐 Interface Admin

1. Ouvrir : `http://localhost:5000/admin/cj-products`
2. Cliquer sur **"Sync Masse Stocks"**
3. Confirmer et attendre (50 produits max, ~30s)

---

## 📝 Voir les Logs

```bash
# Temps réel
tail -f logs/sync_worker.log

# Dernières 50 lignes
tail -n 50 logs/sync_worker.log

# Sous Windows PowerShell
Get-Content logs\sync_worker.log -Tail 50 -Wait
```

---

## ⏹️ Arrêter le Worker

Appuyez sur **Ctrl+C** dans le terminal du worker

---

## 🔧 Configuration Rapide

### Modifier la fréquence de synchronisation

**Fichier** : `workers/sync_worker.py`

```python
# Ligne 141 : Modifier la pause entre cycles
time.sleep(300)  # 300 = 5 minutes
```

### Modifier le nombre de produits par batch

**Fichier** : `workers/sync_worker.py`

```python
# Ligne 94 : Modifier batch_size
result = sync_service.sync_batch(batch_size=10)
```

---

## ❓ Problèmes Courants

### Le worker ne démarre pas

**Vérifier** :
1. Python est installé : `python --version`
2. Dépendances installées : `pip install -r requirements.txt`
3. Dossier logs existe : `mkdir logs`

### Erreur "Module not found"

```bash
# Installer les dépendances
pip install -r requirements.txt
```

### Erreur CJ API

**Vérifier** :
1. Clés API configurées dans `.env`
2. Rate limit respecté (5 minutes entre requêtes)
3. Connexion internet active

---

## 📚 Documentation Complète

Voir : `docs/SYSTEME_SYNCHRONISATION_AUTOMATIQUE.md`

---

**Dernière mise à jour** : 23 Janvier 2026
