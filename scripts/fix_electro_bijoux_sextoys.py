"""
Corrections :
1. Électroménagers : fusionner doublons, renommer en Gros Électroménager + Petit Électroménager
2. Cuisine & Arts de la Table : petits électros -> Petit Électroménager, déplacer sous-cat dans Maison & Jardin
3. Sex toy (ID:2398) -> nouvelle sous-cat Jeux pour Adultes dans Jeux & Jouets
4. Traduire L3 encore en anglais (Cleaning Appliances, Kitchen Appliances)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

def count_prods(cat_id):
    total = Product.query.filter_by(category_id=cat_id).count()
    for c in Category.query.filter_by(parent_id=cat_id).all():
        total += count_prods(c.id)
    return total

with app.app_context():
    electro = Category.query.filter_by(name='Électroménagers', level=1).first()
    maison = Category.query.filter_by(name='Maison & Jardin', level=1).first()
    jeux = Category.query.filter_by(name='Jeux & Jouets', level=1).first()
    
    # ================================================================
    # 1. ÉLECTROMÉNAGERS : réorganiser
    # ================================================================
    print("="*70)
    print("1. ÉLECTROMÉNAGERS - Réorganisation")
    print("="*70)
    
    # Les 3 sous-cat actuelles sous Électroménagers :
    # ID:78  "Électroménager" (vide, visible=False) - ancienne pré-existante
    # ID:354 "Petit électroménager" (vide, visible=False) - ancienne pré-existante
    # ID:1920 "Électroménager" (35 prods, visible=True) - créée par CJ mapping
    # ID:1967 "Cuisine & Arts de la Table" (46 prods) - créée par CJ mapping
    
    # a) Renommer ID:1920 en "Gros Électroménager"
    cat_1920 = db.session.get(Category, 1920)
    if cat_1920:
        cat_1920.name = 'Gros Électroménager'
        cat_1920.name_fr = 'Gros Électroménager'
        cat_1920.slug = 'electromenagers-gros-electromenager'
        print(f"  Renommé ID:1920 -> 'Gros Électroménager'")
    
    # b) Traduire les L3 en anglais sous Gros Électroménager
    translations = {
        'Cleaning Appliances': 'Appareils de Nettoyage',
        'Kitchen Appliances': 'Appareils de Cuisine',
    }
    for old_name, new_name in translations.items():
        cat = Category.query.filter_by(name=old_name).first()
        if cat:
            cat.name = new_name
            cat.name_fr = new_name
            print(f"  Traduit: {old_name} -> {new_name}")
    
    # c) Activer et renommer ID:354 "Petit électroménager" -> "Petit Électroménager"
    cat_354 = db.session.get(Category, 354)
    if cat_354:
        cat_354.name = 'Petit Électroménager'
        cat_354.name_fr = 'Petit Électroménager'
        cat_354.visible = True
        cat_354.is_active = True
        cat_354.slug = 'electromenagers-petit-electromenager'
        print(f"  Activé et renommé ID:354 -> 'Petit Électroménager'")
    
    # d) Masquer l'ancien doublon ID:78
    cat_78 = db.session.get(Category, 78)
    if cat_78:
        cat_78.visible = False
        cat_78.is_active = False
        print(f"  Masqué ID:78 (ancien doublon vide)")
    
    db.session.commit()
    
    # ================================================================
    # 2. CUISINE & ARTS DE LA TABLE : séparer petits électros, déplacer
    # ================================================================
    print(f"\n{'='*70}")
    print("2. CUISINE & ARTS DE LA TABLE - Séparation et déplacement")
    print("="*70)
    
    cuisine = db.session.get(Category, 1967)  # Cuisine & Arts de la Table
    
    if cuisine and cat_354:
        # a) Identifier les petits électroménagers dans "Ustensiles de Cuisine"
        ustensiles = db.session.get(Category, 1968)  # Ustensiles de Cuisine
        if ustensiles:
            prods = Product.query.filter_by(category_id=ustensiles.id).all()
            moved = 0
            for p in prods:
                nl = p.name.lower()
                is_petit_electro = any(kw in nl for kw in [
                    'electric', 'mincer', 'grinder', 'blender', 'mixer',
                    'juicer', 'toaster', 'kettle', 'coffee maker', 'rice cooker',
                    'food warmer', 'heated', 'plug-in', 'rechargeable',
                    'fryer', 'steamer', 'processor', 'machine', 'maker',
                    'whisk', 'chopper'
                ])
                if is_petit_electro:
                    p.category_id = cat_354.id
                    print(f"  Petit électro: {p.name[:55]} -> Petit Électroménager")
                    moved += 1
            print(f"  Total petits électros déplacés: {moved}")
        
        # b) Vérifier aussi les produits directs dans Cuisine & Arts de la Table
        direct_prods = Product.query.filter_by(category_id=cuisine.id).all()
        for p in direct_prods:
            nl = p.name.lower()
            is_petit_electro = any(kw in nl for kw in [
                'electric', 'mincer', 'grinder', 'blender', 'mixer',
                'juicer', 'toaster', 'kettle', 'coffee maker', 'rice cooker',
                'food warmer', 'heated', 'plug-in', 'rechargeable',
                'fryer', 'steamer', 'processor', 'machine', 'maker'
            ])
            if is_petit_electro:
                p.category_id = cat_354.id
                print(f"  Petit électro (direct): {p.name[:55]} -> Petit Électroménager")
        
        # c) Aussi dans "Appareils de Cuisine" (ID:1923) -> Petit Électroménager
        app_cuisine = db.session.get(Category, 1923)
        if app_cuisine:
            prods_app = Product.query.filter_by(category_id=app_cuisine.id).all()
            for p in prods_app:
                p.category_id = cat_354.id
                print(f"  Appareils Cuisine: {p.name[:55]} -> Petit Électroménager")
        
        # d) Déplacer Cuisine & Arts de la Table sous Maison & Jardin
        if maison:
            cuisine.parent_id = maison.id
            print(f"\n  Déplacé 'Cuisine & Arts de la Table' -> Maison & Jardin")
    
    db.session.commit()
    
    # ================================================================
    # 3. SEX TOY -> Jeux pour Adultes dans Jeux & Jouets
    # ================================================================
    print(f"\n{'='*70}")
    print("3. SEX TOY -> Jeux pour Adultes")
    print("="*70)
    
    if jeux:
        # Créer la sous-catégorie "Jeux pour Adultes"
        adultes = Category.query.filter_by(name='Jeux pour Adultes', parent_id=jeux.id).first()
        if not adultes:
            adultes = Category(
                name='Jeux pour Adultes',
                slug='jeux-et-jouets-jeux-pour-adultes',
                parent_id=jeux.id,
                level=2,
                name_fr='Jeux pour Adultes',
                visible=True,
                is_active=True,
            )
            db.session.add(adultes)
            db.session.flush()
            print(f"  Créée: Jeux pour Adultes (ID:{adultes.id})")
        
        # Déplacer le produit sex toy
        sextoy = db.session.get(Product, 2398)
        if sextoy:
            sextoy.category_id = adultes.id
            print(f"  Déplacé: {sextoy.name[:55]} -> Jeux pour Adultes")
        
        # Chercher d'autres sex toys dans toute la BDD
        keywords_adult = ['ejaculation', 'vibrating ring', 'sex toy', 'adult toy',
                          'dildo', 'erotic', 'masturbat', 'penis ring', 'cock ring',
                          'prostate', 'butt plug', 'bondage']
        
        all_suspects = Product.query.filter(
            db.or_(*[Product.name.ilike(f'%{kw}%') for kw in keywords_adult])
        ).all()
        
        for p in all_suspects:
            if p.category_id != adultes.id:
                old_cat = db.session.get(Category, p.category_id) if p.category_id else None
                p.category_id = adultes.id
                print(f"  Déplacé: {p.name[:55]} (était dans {old_cat.name if old_cat else 'N/A'})")
    
    db.session.commit()
    
    # ================================================================
    # RÉSUMÉ FINAL
    # ================================================================
    print(f"\n{'='*70}")
    print("RÉSUMÉ FINAL")
    print("="*70)
    
    if electro:
        print(f"\nÉlectroménagers:")
        l2s = Category.query.filter_by(parent_id=electro.id, is_active=True, visible=True).all()
        for l2 in l2s:
            total = count_prods(l2.id)
            print(f"  {l2.name} : {total} produits")
            l3s = Category.query.filter_by(parent_id=l2.id, is_active=True, visible=True).all()
            for l3 in l3s:
                cnt = Product.query.filter_by(category_id=l3.id).count()
                if cnt > 0:
                    print(f"    {l3.name} : {cnt} produits")
    
    if maison:
        cuisine_check = Category.query.filter_by(name='Cuisine & Arts de la Table', parent_id=maison.id).first()
        if cuisine_check:
            total = count_prods(cuisine_check.id)
            print(f"\nMaison & Jardin > Cuisine & Arts de la Table : {total} produits")
    
    if jeux:
        adultes_check = Category.query.filter_by(name='Jeux pour Adultes', parent_id=jeux.id).first()
        if adultes_check:
            total = count_prods(adultes_check.id)
            print(f"\nJeux & Jouets > Jeux pour Adultes : {total} produits")
