"""Script de test pour vérifier la récupération de produits CJ"""
from app import create_app
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from config import Config
from models.category import Category

app = create_app()

with app.app_context():
    print("="*70)
    print("TEST RÉCUPÉRATION PRODUITS CJ")
    print("="*70)
    
    # Initialiser l'API CJ
    cj_api = CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )
    
    # Test 1: Récupérer des produits sans filtre
    print("\n1. Test sans filtre de catégorie:")
    result = cj_api.get_products(page=1, page_size=10)
    print(f"   - Total produits: {result.get('total', 0)}")
    print(f"   - Produits récupérés: {len(result.get('products', []))}")
    
    if result.get('products'):
        print(f"   - Premier produit: {result['products'][0].get('name', 'N/A')}")
        print(f"   - PID: {result['products'][0].get('pid', 'N/A')}")
    
    # Test 2: Récupérer une catégorie CJ de la BDD
    print("\n2. Test avec catégorie CJ:")
    category = Category.query.filter(Category.cj_category_id.isnot(None)).first()
    
    if category:
        print(f"   - Catégorie: {category.name}")
        print(f"   - CJ ID: {category.cj_category_id}")
        
        result = cj_api.get_products(
            page=1, 
            page_size=10,
            filters={'categoryId': category.cj_category_id}
        )
        
        print(f"   - Total produits: {result.get('total', 0)}")
        print(f"   - Produits récupérés: {len(result.get('products', []))}")
        
        if result.get('products'):
            print(f"   - Premier produit: {result['products'][0].get('name', 'N/A')}")
    else:
        print("   - Aucune catégorie CJ trouvée dans la BDD")
    
    # Test 3: Lister quelques catégories disponibles
    print("\n3. Catégories CJ dans la BDD:")
    categories = Category.query.filter(Category.cj_category_id.isnot(None)).limit(10).all()
    for cat in categories:
        print(f"   - {cat.name} (ID: {cat.cj_category_id}, Level: {cat.level})")
    
    print("\n" + "="*70)
    print("FIN DU TEST")
    print("="*70)
