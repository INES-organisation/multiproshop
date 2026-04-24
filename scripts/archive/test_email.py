"""
Script pour tester l'envoi d'emails
"""
from app import create_app
from extensions import mail
from flask_mail import Message
import sys

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("📧 TEST ENVOI EMAIL")
    print("="*70 + "\n")
    
    # Vérifier la configuration
    mail_username = app.config.get('MAIL_USERNAME', '')
    
    if not mail_username or mail_username == 'votre_email@gmail.com':
        print("❌ Email non configuré dans .env")
        print("\nÉditez le fichier .env et configurez:")
        print("  MAIL_USERNAME=votre_email@gmail.com")
        print("  MAIL_PASSWORD=votre_mot_de_passe_application")
        print("\nPuis relancez: python test_email.py")
        sys.exit(1)
    
    # Demander l'email destinataire
    print(f"📤 Expéditeur configuré: {mail_username}")
    print(f"📨 Serveur: {app.config.get('MAIL_SERVER')}")
    print(f"🔌 Port: {app.config.get('MAIL_PORT')}\n")
    
    recipient = input("Entrez l'email destinataire (ou appuyez sur Entrée pour utiliser l'expéditeur): ").strip()
    
    if not recipient:
        recipient = mail_username
    
    print(f"\n📬 Envoi d'un email de test à: {recipient}")
    print("-" * 70)
    
    # Créer et envoyer le message
    msg = Message(
        subject="✅ Test Email - MultiProShop",
        recipients=[recipient],
        body="""
Bonjour,

Ceci est un email de test envoyé depuis MultiProShop.

Si vous recevez cet email, cela signifie que la configuration email fonctionne correctement ! ✅

Détails de configuration:
- Serveur: {}
- Port: {}
- Expéditeur: {}

Vous pouvez maintenant:
1. Tester une commande complète
2. Vérifier la réception des emails de confirmation
3. Passer en production

Cordialement,
L'équipe MultiProShop

---
Cet email a été envoyé automatiquement par le script test_email.py
        """.format(
            app.config.get('MAIL_SERVER'),
            app.config.get('MAIL_PORT'),
            app.config.get('MAIL_DEFAULT_SENDER')
        ),
        html="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .info { background: #e7f3ff; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0; }
        .footer { text-align: center; color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Test Email</h1>
            <p>MultiProShop</p>
        </div>
        <div class="content">
            <p>Bonjour,</p>
            
            <div class="success">
                <strong>✅ Succès !</strong><br>
                Si vous recevez cet email, la configuration fonctionne correctement !
            </div>
            
            <p>Ceci est un email de test envoyé depuis MultiProShop.</p>
            
            <div class="info">
                <strong>📋 Détails de configuration:</strong><br>
                <ul>
                    <li><strong>Serveur:</strong> {}</li>
                    <li><strong>Port:</strong> {}</li>
                    <li><strong>Expéditeur:</strong> {}</li>
                </ul>
            </div>
            
            <h3>🎯 Prochaines étapes:</h3>
            <ol>
                <li>Tester une commande complète</li>
                <li>Vérifier la réception des emails de confirmation</li>
                <li>Configurer Stripe pour les paiements</li>
                <li>Passer en production</li>
            </ol>
            
            <p>Cordialement,<br>
            <strong>L'équipe MultiProShop</strong></p>
            
            <div class="footer">
                <p>Cet email a été envoyé automatiquement par le script test_email.py</p>
            </div>
        </div>
    </div>
</body>
</html>
        """.format(
            app.config.get('MAIL_SERVER'),
            app.config.get('MAIL_PORT'),
            app.config.get('MAIL_DEFAULT_SENDER')
        )
    )
    
    try:
        mail.send(msg)
        print("✅ Email envoyé avec succès !")
        print("\n📬 Vérifiez votre boîte de réception:")
        print(f"   → {recipient}")
        print("\n💡 Conseil: Si vous ne le voyez pas, vérifiez les spams/courrier indésirable")
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}\n")
        print("🔍 Vérifications:")
        print("  1. Avez-vous activé l'authentification 2FA sur Gmail ?")
        print("  2. Avez-vous généré un mot de passe d'application ?")
        print("  3. Le mot de passe dans .env est-il correct (sans espaces) ?")
        print("  4. Votre pare-feu bloque-t-il le port 587 ?")
        print("\n📖 Consultez: GUIDE_CONFIGURATION.md section 6 (Dépannage)")
        print("\n" + "="*70 + "\n")
        sys.exit(1)
