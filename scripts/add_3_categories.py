"""
Ajouter 3 nouvelles catégories L1 et déplacer les sous-catégories pertinentes.
Objectif : 20 catégories principales au total.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

def count_products_recursive(cat_id):
    total = Product.query.filter_by(category_id=cat_id).count()
    children = Category.query.filter_by(parent_id=cat_id).all()
    for child in children:
        total += count_products_recursive(child.id)
    return total

with app.app_context():
    # --- ÉTAT ACTUEL ---
    print("="*70)
    print("ÉTAT ACTUEL - Catégories L1 MPS")
    print("="*70)
    
    l1s = Category.query.filter_by(level=1, is_active=True).filter(
        Category.cj_category_id.is_(None)
    ).order_by(Category.name).all()
    
    print(f"\n{len(l1s)} catégories L1 actuelles:\n")
    for l1 in l1s:
        print(f"  ID:{l1.id:<5} {l1.name}")
    
    # --- ANALYSE : sous-catégories à déplacer ---
    print(f"\n{'='*70}")
    print("ANALYSE - Sous-catégories candidates au déplacement")
    print(f"{'='*70}\n")
    
    # Bijoux & Montres : chercher dans Mode & Vêtements, Santé & Beauté
    print(">> Bijoux & Montres :")
    bijoux_keywords = ['bijoux', 'montre', 'bague', 'collier', 'bracelet', 'pendentif',
                       'boucle', 'jewelry', 'watch', 'ring', 'necklace', 'earring']
    for l1 in l1s:
        l2s = Category.query.filter_by(parent_id=l1.id, is_active=True, visible=True).all()
        for l2 in l2s:
            nl = l2.name.lower()
            if any(kw in nl for kw in bijoux_keywords):
                count = count_products_recursive(l2.id)
                print(f"  [{l1.name}] {l2.name} (ID:{l2.id}, {count} prods)")
            # Chercher aussi dans les L3
            l3s = Category.query.filter_by(parent_id=l2.id, is_active=True, visible=True).all()
            for l3 in l3s:
                nl3 = l3.name.lower()
                if any(kw in nl3 for kw in bijoux_keywords):
                    count = Product.query.filter_by(category_id=l3.id).count()
                    print(f"  [{l1.name} > {l2.name}] {l3.name} (ID:{l3.id}, {count} prods)")
    
    # Électroménagers : chercher dans Maison & Jardin, Informatique
    print("\n>> Électroménagers :")
    electro_keywords = ['électroménager', 'cuisine', 'aspirateur', 'lave', 'réfrigérateur',
                        'four', 'micro-onde', 'cafetière', 'robot', 'mixeur', 'blender',
                        'grille-pain', 'bouilloire', 'friteuse', 'appareil cuisine',
                        'kitchen', 'appliance', 'ustensile']
    for l1 in l1s:
        l2s = Category.query.filter_by(parent_id=l1.id, is_active=True, visible=True).all()
        for l2 in l2s:
            nl = l2.name.lower()
            if any(kw in nl for kw in electro_keywords):
                count = count_products_recursive(l2.id)
                print(f"  [{l1.name}] {l2.name} (ID:{l2.id}, {count} prods)")
    
    # Produits Numériques : chercher dans Informatique, Électronique
    print("\n>> Produits Numériques :")
    num_keywords = ['logiciel', 'software', 'licence', 'abonnement', 'e-book',
                    'numérique', 'digital', 'téléchargement', 'streaming',
                    'carte cadeau', 'gift card']
    for l1 in l1s:
        l2s = Category.query.filter_by(parent_id=l1.id, is_active=True, visible=True).all()
        for l2 in l2s:
            nl = l2.name.lower()
            if any(kw in nl for kw in num_keywords):
                count = count_products_recursive(l2.id)
                print(f"  [{l1.name}] {l2.name} (ID:{l2.id}, {count} prods)")
    
    # --- CRÉATION DES 3 NOUVELLES CATÉGORIES L1 ---
    print(f"\n{'='*70}")
    print("CRÉATION DES 3 NOUVELLES CATÉGORIES L1")
    print(f"{'='*70}\n")
    
    new_cats = [
        {
            'name': 'Bijoux & Montres',
            'slug': 'bijoux-et-montres',
            'icon': 'fa-gem',
        },
        {
            'name': 'Électroménagers',
            'slug': 'electromenagers',
            'icon': 'fa-blender',
        },
        {
            'name': 'Produits Numériques',
            'slug': 'produits-numeriques',
            'icon': 'fa-cloud-download-alt',
        },
    ]
    
    created_l1 = {}
    for nc in new_cats:
        existing = Category.query.filter_by(name=nc['name'], level=1).first()
        if existing:
            print(f"  Existe déjà: {nc['name']} (ID:{existing.id})")
            created_l1[nc['name']] = existing
        else:
            cat = Category(
                name=nc['name'],
                slug=nc['slug'],
                level=1,
                parent_id=None,
                icon=nc['icon'],
                name_fr=nc['name'],
                visible=True,
                is_active=True,
            )
            db.session.add(cat)
            db.session.flush()
            print(f"  Créée: {nc['name']} (ID:{cat.id})")
            created_l1[nc['name']] = cat
    
    db.session.commit()
    
    # --- DÉPLACEMENT DES SOUS-CATÉGORIES ---
    print(f"\n{'='*70}")
    print("DÉPLACEMENT DES SOUS-CATÉGORIES")
    print(f"{'='*70}\n")
    
    bijoux_l1 = created_l1['Bijoux & Montres']
    electro_l1 = created_l1['Électroménagers']
    numerique_l1 = created_l1['Produits Numériques']
    
    # Bijoux & Montres : déplacer depuis Mode & Vêtements
    bijoux_l2_names = ['bijoux', 'montre', 'bague', 'collier', 'bracelet', 'pendentif',
                       'boucle d\'oreille', 'jewelry', 'watch']
    
    moved_count = 0
    for l1 in l1s:
        if l1.id == bijoux_l1.id:
            continue
        l2s = Category.query.filter_by(parent_id=l1.id, is_active=True).all()
        for l2 in l2s:
            nl = l2.name.lower()
            if any(kw in nl for kw in bijoux_l2_names):
                old_parent = l1.name
                l2.parent_id = bijoux_l1.id
                count = count_products_recursive(l2.id)
                print(f"  {old_parent} -> Bijoux & Montres : {l2.name} ({count} prods)")
                moved_count += 1
    
    # Électroménagers : déplacer depuis Maison & Jardin
    electro_l2_names = ['cuisine', 'électroménager', 'appareils', 'ustensile']
    
    for l1 in l1s:
        if l1.id == electro_l1.id:
            continue
        l2s = Category.query.filter_by(parent_id=l1.id, is_active=True).all()
        for l2 in l2s:
            nl = l2.name.lower()
            if any(kw in nl for kw in electro_l2_names):
                old_parent = l1.name
                l2.parent_id = electro_l1.id
                count = count_products_recursive(l2.id)
                print(f"  {old_parent} -> Électroménagers : {l2.name} ({count} prods)")
                moved_count += 1
    
    print(f"\n  Total déplacées: {moved_count}")
    
    db.session.commit()
    
    # --- RÉSULTAT FINAL ---
    print(f"\n{'='*70}")
    print("RÉSULTAT FINAL - 20 catégories L1")
    print(f"{'='*70}\n")
    
    all_l1 = Category.query.filter_by(level=1, is_active=True, visible=True).filter(
        Category.cj_category_id.is_(None)
    ).order_by(Category.name).all()
    
    for l1 in all_l1:
        total = count_products_recursive(l1.id)
        l2_count = Category.query.filter_by(parent_id=l1.id, is_active=True, visible=True).count()
        print(f"  {l1.name:<35} : {total:>6} produits, {l2_count:>2} sous-cat")
    
    print(f"\n  TOTAL L1: {len(all_l1)}")
