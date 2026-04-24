# 🔧 GUIDE DE CONFIGURATION - STRIPE & EMAILS

## 📋 TABLE DES MATIÈRES

1. [Configuration Stripe](#1-configuration-stripe)
2. [Configuration Email Gmail](#2-configuration-email-gmail)
3. [Configuration Email Autre (SendGrid, etc.)](#3-configuration-email-autre)
4. [Vérification Configuration](#4-vérification-configuration)
5. [Tests](#5-tests)
6. [Dépannage](#6-dépannage)

---

## 1. CONFIGURATION STRIPE

### Étape 1.1 : Créer un compte Stripe

1. Allez sur : **https://dashboard.stripe.com/register**
2. Créez votre compte (gratuit)
3. Vérifiez votre email

### Étape 1.2 : Activer le mode Test

Par défaut, vous êtes en **mode Test** (parfait pour le développement).

Vous verrez un toggle en haut à droite :
```
🔴 Mode Test | Mode Production
```

Restez en **Mode Test** pour l'instant.

### Étape 1.3 : Récupérer les clés API

1. Allez sur : **https://dashboard.stripe.com/test/apikeys**
2. Vous verrez deux clés :

   **Clé publique (Publishable key)** :
   ```
   pk_test_51Abc123...
   ```
   ✅ Cette clé peut être visible côté client

   **Clé secrète (Secret key)** :
   ```
   sk_test_51Abc123...
   ```
   ⚠️ Cette clé doit rester SECRÈTE (serveur uniquement)

3. Cliquez sur "Reveal test key" pour voir la clé secrète

### Étape 1.4 : Ajouter les clés dans .env

Ouvrez le fichier `.env` et remplacez :

```env
STRIPE_PUBLIC_KEY=pk_test_VOTRE_CLE_PUBLIQUE_ICI
STRIPE_SECRET_KEY=sk_test_VOTRE_CLE_SECRETE_ICI
```

Par vos vraies clés :

```env
STRIPE_PUBLIC_KEY=pk_test_51Abc123DEF456...
STRIPE_SECRET_KEY=sk_test_51Abc123DEF456...
```

### Étape 1.5 : Webhook (Optionnel pour l'instant)

Le webhook permet à Stripe de notifier votre serveur des événements.

**Pour le développement local** :
1. Installez Stripe CLI : https://stripe.com/docs/stripe-cli
2. Lancez : `stripe listen --forward-to localhost:5000/cart/webhook`
3. Copiez le webhook secret qui s'affiche
4. Ajoutez-le dans `.env` :
   ```env
   STRIPE_WEBHOOK_SECRET=whsec_abc123...
   ```

**Pour la production** :
1. Allez sur : https://dashboard.stripe.com/webhooks
2. Créez un endpoint : `https://votre-domaine.com/cart/webhook`
3. Sélectionnez les événements : `checkout.session.completed`, `payment_intent.succeeded`
4. Copiez le signing secret

### Étape 1.6 : Cartes de test Stripe

Pour tester les paiements, utilisez ces cartes :

| Carte | Numéro | Résultat |
|-------|--------|----------|
| **Succès** | `4242 4242 4242 4242` | ✅ Paiement réussi |
| **Échec** | `4000 0000 0000 0002` | ❌ Paiement refusé |
| **3D Secure** | `4000 0027 6000 3184` | 🔐 Authentification requise |

- **Date d'expiration** : N'importe quelle date future (ex: 12/25)
- **CVC** : N'importe quel 3 chiffres (ex: 123)
- **Code postal** : N'importe quel code (ex: 75001)

---

## 2. CONFIGURATION EMAIL GMAIL

### Étape 2.1 : Activer l'authentification à 2 facteurs

1. Allez sur : **https://myaccount.google.com/security**
2. Cliquez sur "Validation en deux étapes"
3. Suivez les instructions pour l'activer

### Étape 2.2 : Générer un mot de passe d'application

1. Allez sur : **https://myaccount.google.com/apppasswords**
2. Sélectionnez :
   - **Application** : Mail
   - **Appareil** : Autre (nom personnalisé) → "MultiProShop"
3. Cliquez sur "Générer"
4. Copiez le mot de passe de 16 caractères (format : `xxxx xxxx xxxx xxxx`)

### Étape 2.3 : Ajouter dans .env

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre_email@gmail.com
MAIL_PASSWORD=abcd efgh ijkl mnop
MAIL_DEFAULT_SENDER=votre_email@gmail.com
```

**Remplacez** :
- `votre_email@gmail.com` par votre vraie adresse Gmail
- `abcd efgh ijkl mnop` par le mot de passe d'application (sans espaces)

**Exemple** :
```env
MAIL_USERNAME=anthony.shop@gmail.com
MAIL_PASSWORD=abcdefghijklmnop
MAIL_DEFAULT_SENDER=noreply@multiproshop.com
```

---

## 3. CONFIGURATION EMAIL AUTRE

### Option A : SendGrid (Recommandé pour production)

1. Créez un compte : https://signup.sendgrid.com/
2. Vérifiez votre domaine
3. Créez une clé API
4. Configuration :

```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=votre_cle_api_sendgrid
MAIL_DEFAULT_SENDER=noreply@votre-domaine.com
```

### Option B : Mailgun

```env
MAIL_SERVER=smtp.mailgun.org
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=postmaster@votre-domaine.mailgun.org
MAIL_PASSWORD=votre_mot_de_passe_mailgun
MAIL_DEFAULT_SENDER=noreply@votre-domaine.com
```

### Option C : Office 365 / Outlook

```env
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre_email@outlook.com
MAIL_PASSWORD=votre_mot_de_passe
MAIL_DEFAULT_SENDER=votre_email@outlook.com
```

---

## 4. VÉRIFICATION CONFIGURATION

### Vérifier que les variables sont chargées

Créez un fichier `test_config.py` :

```python
from app import create_app

app = create_app()

with app.app_context():
    print("=== CONFIGURATION STRIPE ===")
    print(f"Public Key: {app.config['STRIPE_PUBLIC_KEY'][:20]}...")
    print(f"Secret Key: {app.config['STRIPE_SECRET_KEY'][:20]}...")
    
    print("\n=== CONFIGURATION EMAIL ===")
    print(f"Server: {app.config['MAIL_SERVER']}")
    print(f"Port: {app.config['MAIL_PORT']}")
    print(f"Username: {app.config['MAIL_USERNAME']}")
    print(f"Sender: {app.config['MAIL_DEFAULT_SENDER']}")
```

Lancez :
```bash
python test_config.py
```

Vous devriez voir vos configurations (partiellement masquées).

---

## 5. TESTS

### Test 1 : Tester l'envoi d'email

Créez `test_email.py` :

```python
from app import create_app
from extensions import mail
from flask_mail import Message

app = create_app()

with app.app_context():
    msg = Message(
        subject="Test Email MultiProShop",
        recipients=["votre_email@gmail.com"],  # Remplacez par votre email
        body="Ceci est un email de test. Si vous le recevez, la configuration fonctionne ! ✅"
    )
    
    try:
        mail.send(msg)
        print("✅ Email envoyé avec succès !")
    except Exception as e:
        print(f"❌ Erreur : {e}")
```

Lancez :
```bash
python test_email.py
```

### Test 2 : Tester Stripe

1. Lancez le serveur : `python app.py`
2. Allez sur : http://multiproshop.local/products
3. Ajoutez un produit au panier
4. Allez au checkout
5. Utilisez la carte de test : `4242 4242 4242 4242`
6. Vérifiez dans le dashboard Stripe : https://dashboard.stripe.com/test/payments

### Test 3 : Tester l'email de confirmation

1. Passez une commande complète
2. Vérifiez votre boîte email
3. Vous devriez recevoir un email de confirmation

---

## 6. DÉPANNAGE

### Problème : "SMTPAuthenticationError"

**Cause** : Mot de passe incorrect ou authentification 2FA non activée

**Solution** :
1. Vérifiez que l'authentification 2FA est activée
2. Générez un nouveau mot de passe d'application
3. Copiez-le sans espaces dans `.env`

### Problème : "Connection refused" (Email)

**Cause** : Port bloqué ou serveur incorrect

**Solution** :
1. Vérifiez le port (587 pour TLS, 465 pour SSL)
2. Essayez avec `MAIL_USE_SSL=True` et `MAIL_PORT=465`
3. Vérifiez votre pare-feu

### Problème : Stripe "Invalid API Key"

**Cause** : Clé incorrecte ou mode Test/Production mélangé

**Solution** :
1. Vérifiez que vous utilisez les clés **test** (commencent par `pk_test_` et `sk_test_`)
2. Copiez à nouveau les clés depuis le dashboard
3. Redémarrez le serveur après modification du `.env`

### Problème : Email non reçu

**Vérifications** :
1. ✅ Vérifiez les spams
2. ✅ Vérifiez que l'email est correct dans la commande
3. ✅ Regardez les logs du serveur pour voir les erreurs
4. ✅ Testez avec `test_email.py`

### Problème : Webhook Stripe ne fonctionne pas

**En développement local** :
- Utilisez Stripe CLI : `stripe listen --forward-to localhost:5000/cart/webhook`

**En production** :
- Vérifiez que l'URL est accessible publiquement
- Vérifiez le signing secret dans `.env`

---

## 📝 CHECKLIST FINALE

Avant de passer en production, vérifiez :

### Stripe
- [ ] Compte Stripe créé
- [ ] Clés de test fonctionnelles
- [ ] Paiement test réussi
- [ ] Webhook configuré (optionnel)
- [ ] Clés de production prêtes (pour plus tard)

### Email
- [ ] Authentification 2FA activée (Gmail)
- [ ] Mot de passe d'application généré
- [ ] Configuration dans `.env`
- [ ] Email de test envoyé et reçu
- [ ] Email de confirmation commande reçu

### Sécurité
- [ ] `.env` dans `.gitignore`
- [ ] Clés secrètes jamais commitées
- [ ] HTTPS activé en production
- [ ] Variables d'environnement sécurisées

---

## 🚀 PASSAGE EN PRODUCTION

Quand vous serez prêt pour la production :

### Stripe Production
1. Activez votre compte Stripe (vérification identité)
2. Passez en mode Production
3. Récupérez les clés de production (`pk_live_...` et `sk_live_...`)
4. Mettez à jour `.env` sur le serveur de production

### Email Production
1. Utilisez un service professionnel (SendGrid, Mailgun)
2. Configurez votre propre domaine
3. Configurez SPF, DKIM, DMARC pour la délivrabilité

---

## 📞 SUPPORT

### Documentation officielle
- **Stripe** : https://stripe.com/docs
- **Flask-Mail** : https://pythonhosted.org/Flask-Mail/
- **Gmail App Passwords** : https://support.google.com/accounts/answer/185833

### Communauté
- Stack Overflow
- Discord Flask
- Forum Stripe

---

*Guide créé le 23/11/2025*
