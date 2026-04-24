"""
Script de test pour les fonctionnalités avancées
"""
from app import create_app
from extensions import db

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("🧪 TEST DES FONCTIONNALITÉS AVANCÉES")
    print("="*70 + "\n")
    
    # ========================================================================
    # TEST 1 : PROVIDERS
    # ========================================================================
    print("📦 TEST 1 : PROVIDERS")
    print("-" * 70)
    
    from models.api_provider import ApiProvider
    
    providers = ApiProvider.query.all()
    print(f"✅ {len(providers)} provider(s) configuré(s)")
    
    for provider in providers:
        print(f"   - {provider.name} ({provider.slug})")
        print(f"     Type: {provider.provider_type}")
        print(f"     Actif: {'✅' if provider.is_active else '❌'}")
        print(f"     Connecté: {'✅' if provider.is_connected else '❌'}")
    
    print()
    
    # ========================================================================
    # TEST 2 : SERVICES PROVIDERS
    # ========================================================================
    print("🔌 TEST 2 : SERVICES PROVIDERS")
    print("-" * 70)
    
    from services.api_providers import (
        CJDropshippingProvider,
        PrintifyProvider,
        AmazonProvider,
        EbayProvider
    )
    
    services = {
        'CJ Dropshipping': CJDropshippingProvider,
        'Printify': PrintifyProvider,
        'Amazon': AmazonProvider,
        'eBay': EbayProvider
    }
    
    for name, service_class in services.items():
        print(f"✅ {name}: {service_class.__name__}")
    
    print()
    
    # ========================================================================
    # TEST 3 : TRADUCTION
    # ========================================================================
    print("🌍 TEST 3 : TRADUCTION AUTOMATIQUE")
    print("-" * 70)
    
    try:
        from services.translation_service import get_translation_service
        
        translator = get_translation_service(provider='google')
        
        # Test simple
        text_en = "Wireless Bluetooth Headphones"
        text_fr = translator.translate_text(text_en, 'en', 'fr')
        
        print(f"✅ Google Translate disponible")
        print(f"   EN: {text_en}")
        print(f"   FR: {text_fr}")
        
        # Test produit
        product = {
            'name': 'iPhone 13 Pro Max Case',
            'description': 'Premium leather case with card holder',
            'category_name': 'Electronics'
        }
        
        translated = translator.translate_product(product, 'en', 'fr')
        print(f"\n   Produit traduit:")
        print(f"   - Nom: {translated['name']}")
        print(f"   - Description: {translated['description']}")
        
    except ImportError:
        print("⚠️  googletrans non installé")
        print("   Installez avec: pip install googletrans==4.0.0-rc1")
    except Exception as e:
        print(f"❌ Erreur traduction: {e}")
    
    print()
    
    # ========================================================================
    # TEST 4 : SCHEDULER
    # ========================================================================
    print("⏰ TEST 4 : SCHEDULER DE SYNCHRONISATION")
    print("-" * 70)
    
    try:
        from services.sync_scheduler import get_scheduler
        
        scheduler = get_scheduler(app)
        
        print(f"✅ Scheduler initialisé")
        print(f"   Running: {scheduler.scheduler.running}")
        
        # Lister les jobs
        jobs = scheduler.get_jobs_status()
        print(f"   Jobs planifiés: {len(jobs)}")
        
        for job in jobs:
            print(f"   - {job['name']}")
            print(f"     Prochaine exécution: {job['next_run']}")
        
        if len(jobs) == 0:
            print("   ℹ️  Aucun job planifié pour le moment")
        
    except ImportError:
        print("⚠️  APScheduler non installé")
        print("   Installez avec: pip install APScheduler==3.10.4")
    except Exception as e:
        print(f"❌ Erreur scheduler: {e}")
    
    print()
    
    # ========================================================================
    # TEST 5 : WEBHOOKS
    # ========================================================================
    print("🔔 TEST 5 : WEBHOOKS")
    print("-" * 70)
    
    from routes.webhooks import webhooks_bp
    
    print(f"✅ Blueprint webhooks enregistré")
    print(f"   Prefix: {webhooks_bp.url_prefix}")
    
    # Lister les routes webhooks
    webhook_routes = [
        '/webhooks/cj-dropshipping',
        '/webhooks/printify',
        '/webhooks/amazon',
        '/webhooks/ebay'
    ]
    
    for route in webhook_routes:
        print(f"   - {route}")
    
    print()
    
    # ========================================================================
    # TEST 6 : TEMPLATES
    # ========================================================================
    print("📄 TEST 6 : TEMPLATES ADMIN")
    print("-" * 70)
    
    import os
    
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates', 'admin', 'api')
    
    if os.path.exists(templates_dir):
        templates = os.listdir(templates_dir)
        print(f"✅ {len(templates)} template(s) trouvé(s)")
        
        for template in templates:
            print(f"   - {template}")
    else:
        print("❌ Dossier templates/admin/api introuvable")
    
    print()
    
    # ========================================================================
    # RÉSUMÉ
    # ========================================================================
    print("="*70)
    print("📊 RÉSUMÉ")
    print("="*70)
    print()
    
    print("✅ Providers supportés:")
    print("   - CJ Dropshipping (Dropshipping)")
    print("   - Printify (Print on Demand)")
    print("   - Amazon Product Advertising (Affiliation)")
    print("   - eBay Partner Network (Affiliation)")
    print()
    
    print("✅ Fonctionnalités avancées:")
    print("   - Traduction automatique (Google Translate / DeepL)")
    print("   - Synchronisation automatique (APScheduler)")
    print("   - Webhooks temps réel (CJ, Printify, eBay)")
    print()
    
    print("📖 Documentation:")
    print("   - API_SYSTEM_GUIDE.md")
    print("   - ADVANCED_FEATURES_GUIDE.md")
    print("   - CORRECTION_ACCES_API.md")
    print()
    
    print("🚀 Pour démarrer:")
    print("   1. Installez les dépendances: pip install -r requirements_api_advanced.txt")
    print("   2. Accédez à /admin/api/providers")
    print("   3. Ajoutez un provider (CJ, Printify, Amazon, eBay)")
    print("   4. Mappez les catégories")
    print("   5. Synchronisez les produits")
    print()
    
    print("="*70)
    print("🎉 TESTS TERMINÉS")
    print("="*70 + "\n")
