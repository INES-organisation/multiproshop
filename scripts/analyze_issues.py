"""Analyser les problèmes signalés"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models.product import Product
from models.category import Category
app = create_app()

def count_prods(cat_id):
    total = Product.query.filter_by(category_id=cat_id).count()
    for c in Category.query.filter_by(parent_id=cat_id).all():
        total += count_prods(c.id)
    return total

with app.app_context():
    # 1. Électroménagers : sous-catégories
    print("="*70)
    print("ÉLECTROMÉNAGERS - sous-catégories")
    print("="*70)
    electro = Category.query.filter_by(name='Électroménagers', level=1).first()
    if electro:
        l2s = Category.query.filter_by(parent_id=electro.id).all()
        for l2 in l2s:
            total = count_prods(l2.id)
            print(f"\n  L2: {l2.name} (ID:{l2.id}, visible={l2.visible}, {total} prods)")
            l3s = Category.query.filter_by(parent_id=l2.id).all()
            for l3 in l3s:
                cnt = Product.query.filter_by(category_id=l3.id).count()
                if cnt > 0 or l3.visible:
                    print(f"    L3: {l3.name} (ID:{l3.id}, visible={l3.visible}, {cnt} prods)")
            # Produits directs dans L2
            direct = Product.query.filter_by(category_id=l2.id).all()
            if direct:
                print(f"    --- Produits directs dans L2 ({len(direct)}) ---")
                for p in direct[:5]:
                    print(f"      {p.name[:60]}")
                if len(direct) > 5:
                    print(f"      ... et {len(direct)-5} de plus")

    # 2. Cuisine & Arts de la Table : contenu
    print(f"\n{'='*70}")
    print("CUISINE & ARTS DE LA TABLE - produits")
    print("="*70)
    cuisine = Category.query.filter(Category.name.ilike('%Cuisine%Arts%Table%')).first()
    if cuisine:
        print(f"  ID:{cuisine.id}, parent_id:{cuisine.parent_id}, level:{cuisine.level}")
        l3s = Category.query.filter_by(parent_id=cuisine.id).all()
        for l3 in l3s:
            cnt = Product.query.filter_by(category_id=l3.id).count()
            if cnt > 0 or l3.visible:
                print(f"  L3: {l3.name} (ID:{l3.id}, {cnt} prods)")
                if cnt > 0:
                    prods = Product.query.filter_by(category_id=l3.id).limit(3).all()
                    for p in prods:
                        print(f"    -> {p.name[:60]}")
        direct = Product.query.filter_by(category_id=cuisine.id).all()
        if direct:
            print(f"  --- Produits directs ({len(direct)}) ---")
            for p in direct:
                print(f"    -> {p.name[:60]}")

    # 3. Bijoux & Montres : sex toys
    print(f"\n{'='*70}")
    print("BIJOUX & MONTRES - produits suspects (sex toys)")
    print("="*70)
    bijoux = Category.query.filter_by(name='Bijoux & Montres', level=1).first()
    if bijoux:
        # Chercher dans toute la branche
        def find_suspects(cat_id, path=""):
            prods = Product.query.filter_by(category_id=cat_id).all()
            for p in prods:
                nl = p.name.lower()
                if any(kw in nl for kw in ['sex', 'vibrat', 'dildo', 'erotic', 'adult',
                    'ejaculation', 'masturbat', 'penis', 'vagina', 'clitor', 'orgasm',
                    'egg-shaped', 'cock', 'prostate', 'butt plug', 'anal', 'bondage',
                    'fetish', 'intimate', 'stimulat']):
                    print(f"  [{path}] {p.name[:70]} (ID:{p.id})")
            for c in Category.query.filter_by(parent_id=cat_id).all():
                find_suspects(c.id, f"{path} > {c.name}" if path else c.name)
        
        find_suspects(bijoux.id)
    
    # 4. Vérifier aussi dans d'autres catégories
    print(f"\n{'='*70}")
    print("AUTRES CATÉGORIES - sex toys potentiels")
    print("="*70)
    suspects = Product.query.filter(
        Product.name.ilike('%ejaculation%') |
        Product.name.ilike('%vibrating ring%') |
        Product.name.ilike('%sex toy%') |
        Product.name.ilike('%adult toy%')
    ).all()
    for p in suspects:
        cat = Category.query.get(p.category_id) if p.category_id else None
        print(f"  {p.name[:60]} -> {cat.full_path if cat else 'AUCUNE'}")
