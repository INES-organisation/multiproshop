"""
Script pour re-mapper les produits 'Non classé' vers leur vraie catégorie.
Phase 2 : mapper via category_name (N3 CJ) et category_id (UUID CJ ou ID local).
"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from models.category import Category

app = create_app()

# Mapping category_name CJ (N3) -> catégorie locale N1
CJ_N3_TO_LOCAL = {
    "Bras": "Mode & Vêtements",
    "Panties": "Mode & Vêtements",
    "Intimates": "Mode & Vêtements",
    "Sleep & Lounge": "Mode & Vêtements",
    "Swimwear": "Mode & Vêtements",
    "Lingerie": "Mode & Vêtements",
    "Massage & Relaxation": "Santé & Beauté",
    "Skin Care": "Santé & Beauté",
    "Hair Care": "Santé & Beauté",
    "Makeup": "Santé & Beauté",
    "Nail Art": "Santé & Beauté",
    "Packaging": "Maison, Jardin & Mobilier",
    "Storage Boxes": "Maison, Jardin & Mobilier",
    "Office & School Supplies": "Informatique",
    "Labels & Stickers": "Informatique",
}

# Mapping categoryName CJ (N1 anglais) -> catégorie locale N1
CJ_N1_TO_LOCAL = {
    "Women's Clothing": "Mode & Vêtements",
    "Men's Clothing": "Mode & Vêtements",
    "Shoes & Accessories": "Mode & Vêtements",
    "Computer & Office": "Informatique",
    "Phones & Telecommunications": "Téléphonie & Tablettes",
    "Consumer Electronics": "Électronique & High-Tech",
    "Home & Garden": "Maison, Jardin & Mobilier",
    "Home Improvement": "Maison, Jardin & Mobilier",
    "Jewelry & Accessories": "Bijoux & Montres",
    "Beauty & Health": "Santé & Beauté",
    "Sports & Entertainment": "Sports & Loisirs",
    "Mother & Kids": "Bébés & Puériculture",
    "Toys & Hobbies": "Jeux & Jouets",
    "Automobiles & Motorcycles": "Auto & Moto",
    "Tools": "Bricolage & Outillage",
    "Lights & Lighting": "Maison, Jardin & Mobilier",
    "Pet Products": "Maison, Jardin & Mobilier",
    "packing material": "Maison, Jardin & Mobilier",
    "Food": "Santé & Beauté",
    "Luggage & Bags": "Mode & Vêtements",
    "Furniture": "Maison, Jardin & Mobilier",
    "Education & Office Supplies": "Informatique",
    "Novelty & Special Use": "Jeux & Jouets",
    "Weddings & Events": "Mode & Vêtements",
    "Security & Protection": "Électronique & High-Tech",
    "Electronic Components & Supplies": "Électronique & High-Tech",
    "Hair Extensions & Wigs": "Santé & Beauté",
    "Apparel Accessories": "Mode & Vêtements",
}

# Mots-clés dans le nom du produit -> catégorie locale N1
KEYWORD_TO_LOCAL = {
    "bra": "Mode & Vêtements",
    "underwear": "Mode & Vêtements",
    "lingerie": "Mode & Vêtements",
    "panties": "Mode & Vêtements",
    "swimsuit": "Mode & Vêtements",
    "bikini": "Mode & Vêtements",
    "pajama": "Mode & Vêtements",
    "nightgown": "Mode & Vêtements",
    "robe": "Mode & Vêtements",
    "sleepwear": "Mode & Vêtements",
    "dress": "Mode & Vêtements",
    "shirt": "Mode & Vêtements",
    "jacket": "Mode & Vêtements",
    "massage": "Santé & Beauté",
    "skin": "Santé & Beauté",
    "beauty": "Santé & Beauté",
    "jewelry": "Bijoux & Montres",
    "necklace": "Bijoux & Montres",
    "ring": "Bijoux & Montres",
    "watch": "Bijoux & Montres",
    "phone": "Téléphonie & Tablettes",
    "tablet": "Téléphonie & Tablettes",
    "computer": "Informatique",
    "laptop": "Informatique",
    "packaging": "Maison, Jardin & Mobilier",
    "storage": "Maison, Jardin & Mobilier",
    "label": "Informatique",
    "sticker": "Informatique",
    "toy": "Jeux & Jouets",
    "baby": "Bébés & Puériculture",
    "car": "Auto & Moto",
}

with app.app_context():
    non_classe = Category.query.filter(Category.name.like('%Non class%')).first()
    if not non_classe:
        print("Catégorie 'Non classé' non trouvée")
        sys.exit(1)
    
    print(f"Catégorie 'Non classé': id={non_classe.id}")
    
    # Charger les catégories locales N1
    local_cats = {}
    for cat in Category.query.filter_by(level=1, is_active=True).all():
        local_cats[cat.name] = cat
    
    # Charger les catégories CJ par cj_category_id
    cj_cats = {}
    for cat in Category.query.filter(Category.cj_category_id.isnot(None)).all():
        cj_cats[cat.cj_category_id] = cat
    
    prods = Product.query.filter_by(category_id=non_classe.id).all()
    print(f"Produits à re-mapper: {len(prods)}")
    
    counters = {'mapped': 0}
    stats = {}
    
    def assign_cat(product, local_name):
        if local_name in local_cats:
            product.category_id = local_cats[local_name].id
            counters['mapped'] += 1
            stats[local_name] = stats.get(local_name, 0) + 1
            return True
        return False
    
    for p in prods:
        raw = json.loads(p.cj_raw_data) if p.cj_raw_data else {}
        
        # 1. Essayer par cj_category_id exact (UUID CJ)
        cj_cat_id = raw.get('categoryId') or raw.get('category_id') or ''
        if isinstance(cj_cat_id, str) and len(cj_cat_id) > 10 and cj_cat_id in cj_cats:
            target = cj_cats[cj_cat_id]
            while target.parent_id:
                parent = db.session.get(Category, target.parent_id)
                if parent:
                    target = parent
                else:
                    break
            # Vérifier que c'est une catégorie FR visible
            if target.visible:
                p.category_id = target.id
                counters['mapped'] += 1
                stats[target.name] = stats.get(target.name, 0) + 1
                continue
        
        # 2. Essayer par category_name (N3 ou chemin complet)
        cat_name = raw.get('categoryName') or raw.get('category_name') or ''
        if cat_name:
            # Si chemin complet (N1 > N2 > N3)
            if '>' in cat_name:
                first_level = cat_name.split('>')[0].strip()
                local_name = CJ_N1_TO_LOCAL.get(first_level)
                if local_name and assign_cat(p, local_name):
                    continue
            # Si juste N3
            local_name = CJ_N3_TO_LOCAL.get(cat_name.strip())
            if local_name and assign_cat(p, local_name):
                continue
        
        # 3. Essayer par mots-clés dans le nom du produit
        name_lower = p.name.lower()
        found = False
        for keyword, local_name in KEYWORD_TO_LOCAL.items():
            if keyword in name_lower:
                if assign_cat(p, local_name):
                    found = True
                    break
        if found:
            continue
        
        # 4. Fallback : "Mode & Vêtements" (la majorité des produits CJ non classés)
        assign_cat(p, "Mode & Vêtements")
    
    mapped = counters['mapped']
    print(f"\nRésultat:")
    print(f"  Mappés: {mapped}")
    print(f"\nPar catégorie:")
    for name, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {count} -> {name}")
    
    if mapped > 0:
        confirm = input(f"\nAppliquer {mapped} changements ? (o/N) ")
        if confirm.lower() == 'o':
            db.session.commit()
            print("Changements appliqués !")
        else:
            db.session.rollback()
            print("Annulé.")
