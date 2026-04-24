"""
Corrections post-mapping par nom de produit.
Corrige les cas où la catégorie CJ est correcte mais le produit est mal classé :
- Camping & Hiking : tentes/chaises camping -> Sports, gazebos/lounge -> Maison
- Home > Furniture : kids bikes, ride-on, rocking horse -> Jeux & Jouets
- Pet Toy Set : playset médical enfant -> Jeux & Jouets
- Plush toys dans Maison -> Jeux & Jouets
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# (source_mps_ids, mots_clés_nom, target_mps_id, description)
FIXES = [
    # Camping & Hiking dans Maison -> Sports (vrais produits camping)
    ([67], ['canopy tent', 'camping chair', 'camping stool', 'foldable camping',
            'oversized foldable camping'], 100, 'Camping -> Sports'),

    # Kids bikes / ride-on / rocking horse dans Maison -> Jeux & Jouets
    ([67], ['kids ride', 'ride on', 'ride-on', 'rocking horse',
            'kids bike', 'kids mountain bike', 'kids sporty bike',
            'toddler slide', 'kids slide',
            'kids toy storage', 'toy organizer',
            'toy for home use', 'insertion toy',
            'plush toy', 'border collie plush', 'turtledove plush',
            'silicone pagoda-shaped toy'], 126, 'Jouets enfants -> Jouets'),

    # Kids bikes dans Maison (FKZNPJ pattern)
    ([67], ['fkznpj'], 126, 'FKZNPJ bikes -> Jouets'),

    # Playset médical dans Animalerie -> Jeux & Jouets
    ([178], ['kids simulated', 'playset toy', 'medical examination playset'], 126, 'Playset -> Jouets'),

    # Porch swing dans Sports -> Maison
    ([100], ['porch swing'], 67, 'Porch swing -> Maison'),

    # Garden cart dans Sports -> Maison
    ([100], ['garden cart'], 67, 'Garden cart -> Maison'),

    # Bicycle velcro dans Maison -> Sports
    ([67], ['bicycle fastening velcro'], 100, 'Bicycle velcro -> Sports'),

    # Garage creeper dans Sports -> Bricolage
    ([100], ['garage creeper', 'creeper garage'], 152, 'Garage creeper -> Bricolage'),

    # Safety gloves dans Sports -> Bricolage
    ([100], ['safety gloves', 'work safety gloves'], 152, 'Safety gloves -> Bricolage'),

    # Folding pendant cervical massager dans Maison -> Santé
    ([67], ['cervical massager', 'neck massager', 'massage gun',
            'fascial gun', 'massage pillow', 'shiatsu massage',
            'infrared sauna', 'uv nail light', 'nail lamp',
            'hair mask', 'shampoo brush', 'bristle travel brush',
            'hair care', 'moroccan nut oil'], 87, 'Santé/Beauté -> Santé'),

    # Ashtray dans Maison -> Auto
    ([67], ['car ashtray'], 139, 'Car ashtray -> Auto'),

    # Sealing ring bumper dans Mode -> Auto
    ([52], ['sealing ring suitable for front and rear bump'], 139, 'Bumper ring -> Auto'),
]


with app.app_context():
    print("\n" + "="*80)
    print("CORRECTIONS POST-MAPPING PAR NOM")
    print("="*80 + "\n")
    
    total_fixed = 0
    
    for source_ids, keywords, target_id, desc in FIXES:
        fixed = 0
        for src_id in source_ids:
            prods = Product.query.filter_by(category_id=src_id).filter(
                Product.cj_pid.isnot(None)
            ).all()
            
            for p in prods:
                nl = p.name.lower()
                if any(kw in nl for kw in keywords):
                    old = db.session.get(Category, p.category_id)
                    new = db.session.get(Category, target_id)
                    print(f"  [{desc}] {p.name[:50]:<50} | {old.name if old else '?'} -> {new.name if new else '?'}")
                    p.category_id = target_id
                    fixed += 1
        
        if fixed:
            print(f"    -> {fixed} corrigés\n")
        total_fixed += fixed
    
    db.session.commit()
    print(f"\nTotal corrigés: {total_fixed}")
    
    # Distribution finale
    print(f"\n{'='*80}")
    print("DISTRIBUTION FINALE")
    print(f"{'='*80}\n")
    
    from sqlalchemy import func
    dist = Product.query.filter(Product.cj_pid.isnot(None)).with_entities(
        Product.category_id, func.count(Product.id)
    ).group_by(Product.category_id).all()
    
    for cat_id, count in sorted(dist, key=lambda x: x[1], reverse=True):
        cat = db.session.get(Category, cat_id) if cat_id else None
        print(f"  {cat.name if cat else 'AUCUNE':<35} : {count:>6}")
    print(f"\n  {'TOTAL':<35} : {sum(c for _,c in dist):>6}")
    
    # Vérification rapide des catégories sensibles
    print(f"\n{'='*80}")
    print("VÉRIFICATION RAPIDE")
    print(f"{'='*80}")
    
    checks = [
        (100, 'Sports', ['garden', 'planter', 'greenhouse', 'gazebo', 'porch swing', 'lounge chair']),
        (67, 'Maison', ['kids ride', 'ride on', 'rocking horse', 'kids bike', 'fkznpj', 'canopy tent']),
        (178, 'Animalerie', ['playset', 'medical examination']),
        (52, 'Mode', ['laptop', 'computer', 'monitor', 'phone case', 'bluetooth']),
    ]
    
    all_clean = True
    for cat_id, cat_name, bad_kw in checks:
        prods = Product.query.filter_by(category_id=cat_id).filter(Product.cj_pid.isnot(None)).all()
        suspects = []
        for p in prods:
            nl = p.name.lower()
            for kw in bad_kw:
                if kw in nl:
                    suspects.append(f"    {p.name[:60]} (kw: {kw})")
                    break
        if suspects:
            all_clean = False
            print(f"\n  ⚠ {cat_name} ({cat_id}) - {len(suspects)} suspects:")
            for s in suspects[:5]:
                print(s)
        else:
            print(f"\n  OK {cat_name} ({cat_id})")
    
    if all_clean:
        print("\n  TOUT EST PROPRE !")
