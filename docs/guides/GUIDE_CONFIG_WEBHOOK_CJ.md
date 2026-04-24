# 🔧 GUIDE DE CONFIGURATION WEBHOOK CJ DROPSHIPPING

## ⚠️ IMPORTANT

L'API CJ ne permet pas de configurer les webhooks programmatiquement via `/webhook/setting`. La configuration doit être faite **manuellement** via le dashboard CJ.

---

## 📋 CONFIGURATION MANUELLE

### Étape 1 : Se Connecter au Dashboard CJ

1. Aller sur **https://cjdropshipping.com**
2. Se connecter avec vos identifiants :
   - Email : `tonyalpha80@gmail.com`
   - Mot de passe : (votre mot de passe CJ)

### Étape 2 : Accéder aux Paramètres Webhook

1. Dans le menu principal, cliquer sur **Settings** (Paramètres)
2. Chercher la section **Webhooks** ou **API Settings**
3. Cliquer sur **Webhook Configuration**

### Étape 3 : Configurer l'URL du Webhook

**URL à configurer :**
```
https://tonyalpha80.com/webhooks/cj/message
```

**Configuration requise :**
- ✅ **URL** : `https://tonyalpha80.com/webhooks/cj/message`
- ✅ **Méthode** : POST
- ✅ **Content-Type** : application/json
- ✅ **Activer** : Oui

### Étape 4 : Sélectionner les Types d'Événements

Cocher les événements suivants :

- ✅ **ORDER** - Mises à jour commandes
- ✅ **STOCK** - Mises à jour stock
- ✅ **LOGISTIC** - Mises à jour tracking/livraison
- ⚠️ **PRODUCT** - (Optionnel) Mises à jour produits
- ⚠️ **VARIANT** - (Optionnel) Mises à jour variantes
- ⚠️ **ORDERSPLIT** - (Optionnel) Divisions de commandes

**Recommandation :** Activer au minimum ORDER, STOCK et LOGISTIC.

### Étape 5 : Sauvegarder et Tester

1. Cliquer sur **Save** ou **Enregistrer**
2. Utiliser le bouton **Test** si disponible
3. Vérifier que le statut est **Active** ou **Activé**

---

## 🧪 VÉRIFICATION DE LA CONFIGURATION

### Test 1 : Vérifier que le Serveur est Accessible

Votre serveur doit être **accessible publiquement** sur `https://tonyalpha80.com`.

**Vérification :**
```powershell
# Tester l'accessibilité
curl https://tonyalpha80.com/webhooks/cj/message
```

**Réponse attendue :** 
- Status 200 ou 405 (Method Not Allowed pour GET)
- **PAS** 404 ou timeout

### Test 2 : Créer une Commande Test

1. Dans le dashboard CJ, créer une **commande test**
2. Changer le statut de la commande (ex: SHIPPED)
3. Vérifier les logs de votre application

**Vérifier les logs :**
```powershell
# Dans votre application Flask
# Vous devriez voir :
📥 Webhook CJ reçu
type=ORDER, id=xxx
✅ Commande XXX mise à jour
```

### Test 3 : Consulter les Logs Webhook

Dans votre application :

```powershell
# Démarrer l'application
python app.py

# Dans un autre terminal, consulter les logs
curl http://localhost:5000/webhooks/cj/logs
```

---

## 🔍 DÉPANNAGE

### Problème 1 : Webhook Non Reçu

**Causes possibles :**
1. ❌ URL incorrecte dans CJ
2. ❌ Serveur non accessible publiquement
3. ❌ Firewall bloque les requêtes CJ
4. ❌ HTTPS non configuré

**Solutions :**
```powershell
# Vérifier que le serveur répond
curl -X POST https://tonyalpha80.com/webhooks/cj/message \
  -H "Content-Type: application/json" \
  -d '{"messageId":"test","type":"ORDER","messageType":"UPDATE","params":{}}'

# Réponse attendue : 200 OK
```

### Problème 2 : Erreur 404

**Cause :** Route non enregistrée ou application non démarrée

**Solution :**
```powershell
# Vérifier que le blueprint est enregistré
# Dans app.py, ligne ~143 :
app.register_blueprint(webhooks_cj)

# Redémarrer l'application
python app.py
```

### Problème 3 : Erreur 500

**Cause :** Erreur dans le traitement du webhook

**Solution :**
```powershell
# Consulter les logs détaillés
# Les erreurs sont loggées dans la console

# Vérifier la base de données
# La table webhook_log doit exister
```

---

## 📊 MONITORING

### Consulter les Webhooks Reçus

**Via API :**
```powershell
# Derniers webhooks
curl http://localhost:5000/webhooks/cj/logs?limit=10

# Statistiques
curl http://localhost:5000/webhooks/cj/stats
```

**Via Base de Données :**
```sql
-- Derniers webhooks
SELECT * FROM webhook_log 
ORDER BY created_at DESC 
LIMIT 10;

-- Statistiques par type
SELECT event_type, COUNT(*), 
       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
FROM webhook_log 
GROUP BY event_type;
```

---

## ✅ CHECKLIST DE CONFIGURATION

Avant de considérer la configuration terminée :

- [ ] Dashboard CJ : URL webhook configurée
- [ ] Dashboard CJ : Événements ORDER, STOCK, LOGISTIC activés
- [ ] Dashboard CJ : Webhook marqué comme "Active"
- [ ] Serveur : Application Flask démarrée
- [ ] Serveur : Route `/webhooks/cj/message` accessible
- [ ] Serveur : HTTPS configuré (production)
- [ ] Test : Commande test créée et webhook reçu
- [ ] Test : Logs webhook visibles dans la base
- [ ] Monitoring : Statistiques webhooks fonctionnelles

---

## 🚀 CONFIGURATION PRODUCTION

### Prérequis

1. **Serveur Web** : Nginx ou Apache
2. **HTTPS** : Certificat SSL valide
3. **Application** : Flask en mode production (Gunicorn/uWSGI)
4. **Firewall** : Port 443 ouvert

### Configuration Nginx (Exemple)

```nginx
server {
    listen 443 ssl;
    server_name tonyalpha80.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /webhooks/cj/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Démarrage Production

```powershell
# Avec Gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 app:app

# Avec uWSGI
uwsgi --http 127.0.0.1:5000 --wsgi-file app.py --callable app
```

---

## 📞 SUPPORT

### Si Problème Persiste

1. **Documentation CJ** : https://developers.cjdropshipping.cn/en/api/start/webhook.html
2. **Support CJ** : Contacter le support via le dashboard
3. **Logs Application** : Vérifier les logs Flask pour erreurs détaillées

### Informations à Fournir au Support

- URL webhook : `https://tonyalpha80.com/webhooks/cj/message`
- Types d'événements : ORDER, STOCK, LOGISTIC
- Format attendu : JSON (voir documentation)
- Erreur rencontrée : (copier le message d'erreur)

---

## 🎯 PROCHAINES ÉTAPES

Une fois le webhook configuré et testé :

1. ✅ Créer des commandes réelles
2. ✅ Monitorer les webhooks pendant 24-48h
3. ✅ Vérifier que les emails clients sont envoyés
4. ✅ Ajuster les handlers si nécessaire
5. ✅ Documenter les cas particuliers rencontrés

---

**Date :** 24 Janvier 2026  
**Version :** 1.0  
**Statut :** Configuration manuelle requise
