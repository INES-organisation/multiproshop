"""
Script pour vérifier la configuration Stripe et Email
"""
from app import create_app

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("🔍 VÉRIFICATION CONFIGURATION")
    print("="*70 + "\n")
    
    # Stripe
    print("📊 STRIPE CONFIGURATION")
    print("-" * 70)
    stripe_public = app.config.get('STRIPE_PUBLIC_KEY', '')
    stripe_secret = app.config.get('STRIPE_SECRET_KEY', '')
    stripe_webhook = app.config.get('STRIPE_WEBHOOK_SECRET', '')
    
    if stripe_public and stripe_public != '':
        if stripe_public.startswith('pk_test_'):
            print(f"✅ Public Key (Test): {stripe_public[:20]}...{stripe_public[-4:]}")
        elif stripe_public.startswith('pk_live_'):
            print(f"⚠️  Public Key (LIVE): {stripe_public[:20]}...{stripe_public[-4:]}")
        else:
            print(f"❌ Public Key: Format invalide")
    else:
        print("❌ Public Key: NON CONFIGURÉE")
    
    if stripe_secret and stripe_secret != '':
        if stripe_secret.startswith('sk_test_'):
            print(f"✅ Secret Key (Test): {stripe_secret[:20]}...{stripe_secret[-4:]}")
        elif stripe_secret.startswith('sk_live_'):
            print(f"⚠️  Secret Key (LIVE): {stripe_secret[:20]}...{stripe_secret[-4:]}")
        else:
            print(f"❌ Secret Key: Format invalide")
    else:
        print("❌ Secret Key: NON CONFIGURÉE")
    
    if stripe_webhook and stripe_webhook != '':
        print(f"✅ Webhook Secret: {stripe_webhook[:20]}...{stripe_webhook[-4:]}")
    else:
        print("⚠️  Webhook Secret: NON CONFIGURÉ (optionnel)")
    
    # Email
    print("\n📧 EMAIL CONFIGURATION")
    print("-" * 70)
    mail_server = app.config.get('MAIL_SERVER', '')
    mail_port = app.config.get('MAIL_PORT', '')
    mail_username = app.config.get('MAIL_USERNAME', '')
    mail_password = app.config.get('MAIL_PASSWORD', '')
    mail_sender = app.config.get('MAIL_DEFAULT_SENDER', '')
    
    if mail_server:
        print(f"✅ Server: {mail_server}")
    else:
        print("❌ Server: NON CONFIGURÉ")
    
    if mail_port:
        print(f"✅ Port: {mail_port}")
    else:
        print("❌ Port: NON CONFIGURÉ")
    
    if mail_username and mail_username != 'votre_email@gmail.com':
        print(f"✅ Username: {mail_username}")
    else:
        print("❌ Username: NON CONFIGURÉ")
    
    if mail_password and mail_password != 'votre_mot_de_passe_application_16_caracteres':
        print(f"✅ Password: {'*' * len(mail_password[:16])}")
    else:
        print("❌ Password: NON CONFIGURÉ")
    
    if mail_sender:
        print(f"✅ Sender: {mail_sender}")
    else:
        print("❌ Sender: NON CONFIGURÉ")
    
    # Résumé
    print("\n" + "="*70)
    print("📋 RÉSUMÉ")
    print("="*70)
    
    stripe_ok = bool(stripe_public and stripe_secret and 
                     stripe_public.startswith('pk_') and 
                     stripe_secret.startswith('sk_'))
    
    email_ok = bool(mail_server and mail_port and mail_username and mail_password and
                    mail_username != 'votre_email@gmail.com' and
                    mail_password != 'votre_mot_de_passe_application_16_caracteres')
    
    if stripe_ok:
        print("✅ Stripe: CONFIGURÉ")
    else:
        print("❌ Stripe: À CONFIGURER")
        print("   → Suivez le guide: GUIDE_CONFIGURATION.md")
    
    if email_ok:
        print("✅ Email: CONFIGURÉ")
    else:
        print("❌ Email: À CONFIGURER")
        print("   → Suivez le guide: GUIDE_CONFIGURATION.md")
    
    print("\n" + "="*70)
    
    if stripe_ok and email_ok:
        print("🎉 TOUT EST CONFIGURÉ ! Vous pouvez tester.")
        print("\nProchaines étapes:")
        print("1. Testez l'envoi d'email: python test_email.py")
        print("2. Lancez le serveur: python app.py")
        print("3. Testez un paiement avec la carte: 4242 4242 4242 4242")
    else:
        print("⚠️  CONFIGURATION INCOMPLÈTE")
        print("\nÉditez le fichier .env avec vos vraies clés:")
        print("1. Stripe: https://dashboard.stripe.com/test/apikeys")
        print("2. Email: https://myaccount.google.com/apppasswords")
        print("\nPuis relancez: python test_config.py")
    
    print("="*70 + "\n")
