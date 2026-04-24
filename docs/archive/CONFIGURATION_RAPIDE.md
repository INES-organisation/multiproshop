# ⚡ CONFIGURATION RAPIDE - 5 MINUTES

## 🎯 OBJECTIF

Configurer Stripe et les emails en 5 minutes chrono !

---

## 📝 ÉTAPE 1 : STRIPE (2 minutes)

### 1️⃣ Créer un compte Stripe

👉 https://dashboard.stripe.com/register

### 2️⃣ Récupérer les clés de test

👉 https://dashboard.stripe.com/test/apikeys

Vous verrez :
```
Publishable key: pk_test_51Abc...
Secret key: sk_test_51Abc... (cliquez "Reveal")
```

### 3️⃣ Copier dans .env

Ouvrez le fichier `.env` et remplacez :

```env
STRIPE_PUBLIC_KEY=pk_test_51Abc123DEF456GHI789...
STRIPE_SECRET_KEY=sk_test_51Abc123DEF456GHI789...
```

✅ **C'est tout pour Stripe !**

---

## 📧 ÉTAPE 2 : EMAIL GMAIL (3 minutes)

### 1️⃣ Activer l'authentification 2FA

👉 https://myaccount.google.com/security

Cliquez sur "Validation en deux étapes" et activez-la.

### 2️⃣ Générer un mot de passe d'application

👉 https://myaccount.google.com/apppasswords

- Sélectionnez "Mail" et "Autre"
- Nommez-le "MultiProShop"
- Cliquez "Générer"
- Copiez le mot de passe (16 caractères)

### 3️⃣ Copier dans .env

Ouvrez le fichier `.env` et remplacez :

```env
MAIL_USERNAME=votre_email@gmail.com
MAIL_PASSWORD=abcdefghijklmnop
```

**Exemple** :
```env
MAIL_USERNAME=anthony.shop@gmail.com
MAIL_PASSWORD=xyzw abcd efgh ijkl
```

✅ **C'est tout pour l'email !**

---

## ✅ ÉTAPE 3 : VÉRIFIER (30 secondes)

Lancez :
```bash
python test_config.py
```

Vous devriez voir :
```
✅ Stripe: CONFIGURÉ
✅ Email: CONFIGURÉ
🎉 TOUT EST CONFIGURÉ !
```

---

## 🧪 ÉTAPE 4 : TESTER (1 minute)

### Test Email
```bash
python test_email.py
```

Entrez votre email et vérifiez la réception.

### Test Stripe

1. Lancez le serveur :
   ```bash
   python app.py
   ```

2. Allez sur : http://multiproshop.local/products

3. Ajoutez un produit au panier

4. Allez au checkout

5. Utilisez la carte de test :
   ```
   Numéro: 4242 4242 4242 4242
   Date: 12/25
   CVC: 123
   ```

6. Validez et vérifiez l'email de confirmation !

---

## 🎉 TERMINÉ !

Votre système est maintenant configuré et fonctionnel !

### Prochaines étapes :

1. ✅ Testez plusieurs commandes
2. ✅ Vérifiez le dashboard Stripe : https://dashboard.stripe.com/test/payments
3. ✅ Testez l'admin : http://multiproshop.local/admin/orders
4. ✅ Changez le statut d'une commande et vérifiez l'email

---

## 🆘 PROBLÈMES ?

### Stripe ne fonctionne pas
- Vérifiez que les clés commencent par `pk_test_` et `sk_test_`
- Redémarrez le serveur après modification du `.env`

### Email ne fonctionne pas
- Vérifiez les spams
- Vérifiez que l'authentification 2FA est activée
- Générez un nouveau mot de passe d'application
- Copiez-le SANS espaces dans `.env`

### Plus d'aide ?
Consultez : **GUIDE_CONFIGURATION.md** (guide complet)

---

## 📊 RÉCAPITULATIF

| Étape | Temps | Statut |
|-------|-------|--------|
| Stripe | 2 min | ⏳ |
| Email | 3 min | ⏳ |
| Vérification | 30 sec | ⏳ |
| Tests | 1 min | ⏳ |
| **TOTAL** | **~7 min** | 🎯 |

---

*Guide rapide créé le 23/11/2025*
