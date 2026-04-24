from app import app
from models.product import Product
from extensions import db

with app.app_context():
    pid = '1471485216202821632'
    
    # Recherche exacte
    p = Product.query.filter_by(cj_pid=pid).first()
    print(f"Recherche exacte par PID '{pid}':")
    if p:
        print(f"  ✓ Produit trouvé: {p.name}")
        print(f"  - ID: {p.id}")
        print(f"  - PID: {p.cj_pid}")
        print(f"  - SKU: {p.sku}")
        print(f"  - Catégorie ID: {p.category_id}")
    else:
        print(f"  ✗ Aucun produit trouvé")
    
    # Recherche avec ilike
    p2 = Product.query.filter(Product.cj_pid.ilike(f'%{pid}%')).first()
    print(f"\nRecherche avec ilike '%{pid}%':")
    if p2:
        print(f"  ✓ Produit trouvé: {p2.name}")
    else:
        print(f"  ✗ Aucun produit trouvé")
    
    # Compter tous les produits CJ
    total_cj = Product.query.filter(Product.cj_pid.isnot(None)).count()
    print(f"\nTotal produits CJ dans la base: {total_cj}")
    
    # Afficher quelques PIDs pour comparaison
    print("\nExemples de PIDs dans la base:")
    samples = Product.query.filter(Product.cj_pid.isnot(None)).limit(5).all()
    for s in samples:
        print(f"  - {s.cj_pid} ({s.name[:50]}...)")
