"""
Corrections finales :
1. Les sous-vêtements femme envoyés dans "Sous-Vêtements & Détente Homme" -> créer une catégorie Femme
2. Reclasser les 22 produits restants dans L1
3. Créer les catégories manquantes si nécessaire
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    print("="*80)
    print("CORRECTIONS FINALES")
    print("="*80)
    
    # --- 1. Créer "Lingerie & Sous-Vêtements Femme" sous Mode ---
    print("\n--- 1. Créer Lingerie & Sous-Vêtements Femme ---\n")
    
    mode_id = 52  # Mode & Vêtements
    
    # Vérifier si la catégorie existe déjà
    lingerie_cat = Category.query.filter_by(
        parent_id=mode_id, name='Lingerie & Sous-Vêtements Femme'
    ).first()
    
    if not lingerie_cat:
        lingerie_cat = Category(
            name='Lingerie & Sous-Vêtements Femme',
            slug='mode-et-vetements-lingerie-sous-vetements-femme',
            parent_id=mode_id,
            level=2,
            name_fr='Lingerie & Sous-Vêtements Femme',
            visible=True,
            is_active=True,
        )
        db.session.add(lingerie_cat)
        db.session.flush()
        print(f"  Créée: {lingerie_cat.name} (ID:{lingerie_cat.id})")
    else:
        print(f"  Existe déjà: {lingerie_cat.name} (ID:{lingerie_cat.id})")
    
    # Trouver "Sous-Vêtements & Détente Homme" et récupérer les produits femme
    sv_homme = Category.query.filter_by(name='Sous-Vêtements & Détente Homme').first()
    if sv_homme:
        prods = Product.query.filter_by(category_id=sv_homme.id).filter(
            Product.cj_pid.isnot(None)
        ).all()
        
        moved = 0
        for p in prods:
            nl = p.name.lower()
            # Si c'est un produit femme (bra, lingerie, women, etc.)
            is_female = any(kw in nl for kw in [
                'women', 'woman', 'bra ', 'bra,', 'lingerie', 'shapewear',
                'bustier', 'corset', 'panties', 'female', 'lace mesh',
                'sheer', 'seamless', 'plus size', 'push-up', 'front-closure',
                'bodysuit', 'teddy', 'nightgown'
            ])
            if is_female:
                p.category_id = lingerie_cat.id
                moved += 1
        
        print(f"  Produits femme migrés de SV Homme -> Lingerie Femme: {moved}")
        
        # Vérifier ce qui reste dans SV Homme
        remaining = Product.query.filter_by(category_id=sv_homme.id).filter(
            Product.cj_pid.isnot(None)
        ).count()
        print(f"  Restant dans SV Homme: {remaining}")
    
    db.session.commit()
    
    # --- 2. Reclasser les produits restants dans L1 ---
    print("\n--- 2. Produits restants dans L1 ---\n")
    
    # Mode & Vêtements (14 restants)
    mode_prods = Product.query.filter_by(category_id=52).filter(
        Product.cj_pid.isnot(None)
    ).all()
    
    if mode_prods:
        print(f"  Mode & Vêtements: {len(mode_prods)} produits")
        
        # Chercher les catégories cibles
        robes_cat = Category.query.filter(
            Category.name == 'Robes',
            Category.level == 3,
            Category.is_active == True
        ).first()
        
        bijoux_cat = Category.query.filter(
            Category.name == 'Bijoux Fantaisie',
            Category.level == 2,
            Category.is_active == True
        ).first()
        
        maillots_cat = Category.query.filter(
            Category.name.ilike('%Maillots de Bain%'),
            Category.level == 2,
        ).first()
        
        for p in mode_prods:
            nl = p.name.lower()
            target = None
            
            if any(kw in nl for kw in ['costume', 'dinosaur', 'halloween', 'cosplay']):
                # Déguisement -> Fêtes & Événements sous Maison
                target = Category.query.filter(
                    Category.name.ilike('%Fêtes%')
                ).filter_by(level=2).first()
            elif any(kw in nl for kw in ['dress', 'robe']):
                target = robes_cat
            elif any(kw in nl for kw in ['swimsuit', 'bikini', 'swimwear']):
                target = maillots_cat
            elif any(kw in nl for kw in ['necklace', 'bracelet', 'earring', 'ring', 'pendant', 'jewelry']):
                target = bijoux_cat
            elif any(kw in nl for kw in ['bra', 'underwear', 'lingerie', 'bodysuit', 'panties', 'shapewear']):
                target = lingerie_cat
            elif any(kw in nl for kw in ['scarf', 'hat', 'cap', 'glove']):
                target = Category.query.filter(
                    Category.name == 'Accessoires Femme',
                    Category.level == 2
                ).first()
            elif any(kw in nl for kw in ['shirt', 'blouse', 'top', 'sweater', 'hoodie']):
                target = Category.query.filter(
                    Category.name == 'Hauts & Ensembles Femme',
                    Category.level == 2
                ).first()
            elif any(kw in nl for kw in ['pants', 'jeans', 'skirt', 'shorts', 'legging']):
                target = Category.query.filter(
                    Category.name == 'Bas Femme',
                    Category.level == 2
                ).first()
            elif any(kw in nl for kw in ['jacket', 'coat', 'blazer']):
                target = Category.query.filter(
                    Category.name.ilike('%Vestes%Femme%'),
                    Category.level == 2
                ).first()
            
            if target:
                print(f"    {p.name[:50]:<50} -> {target.name}")
                p.category_id = target.id
            else:
                # Fallback : Hauts & Ensembles Femme
                fallback = Category.query.filter(
                    Category.name == 'Hauts & Ensembles Femme',
                    Category.level == 2
                ).first()
                if fallback:
                    print(f"    {p.name[:50]:<50} -> {fallback.name} (fallback)")
                    p.category_id = fallback.id
                else:
                    print(f"    RESTE: {p.name[:50]}")
    
    # Santé & Beauté (6 restants)
    sante_prods = Product.query.filter_by(category_id=87).filter(
        Product.cj_pid.isnot(None)
    ).all()
    
    if sante_prods:
        print(f"\n  Santé & Beauté: {len(sante_prods)} produits")
        
        massage_cat = Category.query.filter(
            Category.name.ilike('%Massage%'),
            Category.level >= 2
        ).first()
        
        soins_cat = Category.query.filter(
            Category.name == 'Soins du Visage',
            Category.level == 3
        ).first()
        
        if not soins_cat:
            soins_cat = Category.query.filter(
                Category.name.ilike('%Soins visage%'),
                Category.level >= 2
            ).first()
        
        outils_cat = Category.query.filter(
            Category.name == 'Outils Beauté',
            Category.level == 2
        ).first()
        
        for p in sante_prods:
            nl = p.name.lower()
            target = None
            
            if any(kw in nl for kw in ['massage', 'massager', 'pillow', 'fascial gun',
                                        'infrared', 'therapeutic', 'heating waist']):
                target = massage_cat or outils_cat
            elif any(kw in nl for kw in ['skin', 'photon', 'rejuvenation', 'moisturizing',
                                          'hydrating', 'face mask']):
                target = soins_cat or outils_cat
            elif any(kw in nl for kw in ['hair', 'essential oil']):
                target = Category.query.filter(
                    Category.name.ilike('%Cheveux%'),
                    Category.level == 2
                ).first()
            
            if target:
                print(f"    {p.name[:50]:<50} -> {target.name}")
                p.category_id = target.id
            else:
                if outils_cat:
                    print(f"    {p.name[:50]:<50} -> {outils_cat.name} (fallback)")
                    p.category_id = outils_cat.id
                else:
                    print(f"    RESTE: {p.name[:50]}")
    
    # Sports & Loisirs (2 restants)
    sports_prods = Product.query.filter_by(category_id=100).filter(
        Product.cj_pid.isnot(None)
    ).all()
    
    if sports_prods:
        print(f"\n  Sports & Loisirs: {len(sports_prods)} produits")
        
        sport_acc = Category.query.filter(
            Category.name == 'Accessoires de Sport',
            Category.level == 3
        ).first()
        
        equip_cat = Category.query.filter(
            Category.name == 'Équipement Sportif',
            Category.level == 2
        ).first()
        
        for p in sports_prods:
            nl = p.name.lower()
            if any(kw in nl for kw in ['sports bra', 'yoga', 'fitness']):
                target = sport_acc or equip_cat
                if target:
                    print(f"    {p.name[:50]:<50} -> {target.name}")
                    p.category_id = target.id
            else:
                if equip_cat:
                    print(f"    {p.name[:50]:<50} -> {equip_cat.name} (fallback)")
                    p.category_id = equip_cat.id
    
    db.session.commit()
    
    # --- VÉRIFICATION ---
    print(f"\n{'='*80}")
    print("VÉRIFICATION : produits encore dans L1")
    print(f"{'='*80}\n")
    
    mps_l1 = Category.query.filter_by(level=1).filter(
        Category.cj_category_id.is_(None)
    ).all()
    
    any_remaining = False
    for l1 in mps_l1:
        count = Product.query.filter_by(category_id=l1.id).filter(
            Product.cj_pid.isnot(None)
        ).count()
        if count > 0:
            print(f"  ⚠ {l1.name}: {count} produits")
            any_remaining = True
            prods = Product.query.filter_by(category_id=l1.id).filter(
                Product.cj_pid.isnot(None)
            ).all()
            for p in prods:
                print(f"    {p.name[:60]}")
    
    if not any_remaining:
        print("  ✓ Tous les produits sont dans des sous-catégories L2/L3 !")
