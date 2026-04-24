# 🚀 INSTALLATION REDIS POUR WINDOWS

## Option 1 : Memurai (Recommandé pour Windows)

### **Téléchargement**
```
https://www.memurai.com/get-memurai
```

### **Installation**
1. Télécharger Memurai Developer Edition (gratuit)
2. Installer
3. Le service démarre automatiquement

### **Vérification**
```powershell
# Ouvrir PowerShell
redis-cli ping
# Devrait répondre : PONG
```

---

## Option 2 : Redis via WSL (Windows Subsystem for Linux)

### **Installation WSL**
```powershell
wsl --install
```

### **Installation Redis dans WSL**
```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

### **Vérification**
```bash
redis-cli ping
# Devrait répondre : PONG
```

---

## Option 3 : Redis via Docker (Si Docker installé)

### **Lancer Redis**
```powershell
docker run -d -p 6379:6379 --name redis redis:alpine
```

### **Vérification**
```powershell
docker exec -it redis redis-cli ping
# Devrait répondre : PONG
```

---

## Configuration MultiProShop

Une fois Redis installé, modifier `app.py` :

```python
# Remplacer
app.config['CACHE_TYPE'] = 'SimpleCache'

# Par
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
```

Redémarrer le serveur et c'est tout !

---

## ⚠️ Si Redis n'est pas disponible

Le code actuel utilise **SimpleCache** qui fonctionne très bien pour le développement.

**SimpleCache** :
- ✅ Fonctionne immédiatement
- ✅ Aucune installation requise
- ✅ Parfait pour développement
- ⚠️ Cache perdu au redémarrage
- ⚠️ Non partagé entre processus

**Redis** :
- ✅ Cache persistant
- ✅ Partagé entre processus
- ✅ Meilleure performance
- ⚠️ Nécessite installation

**Conclusion** : SimpleCache est suffisant pour l'instant !
