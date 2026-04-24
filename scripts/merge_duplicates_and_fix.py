"""
Nettoyage complet :
1. Fusionner les doublons (garder la nouvelle catégorie CJ, migrer les enfants de l'ancienne)
2. Reclasser les produits directement dans L1 vers des sous-catégories
3. Traduire les dernières catégories en anglais
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# ============================================================
# DOUBLONS : (ancien_id_à_supprimer, nouveau_id_à_garder)
# On migre les enfants et produits de l'ancien vers le nouveau
# ============================================================
DUPLICATES = [
    # Maquillage : ancien ID:92 (0 prod, 3 enfants) -> nouveau ID:1898 (0 prod, 6 enfants)
    (92, 1898),
    # Chaussures Homme : ancien ID:227 (0 prod, 21 enfants) -> nouveau ID:1810 (0 prod, 6 enfants)
    (227, 1810),
    # Chaussures Femme : ancien ID:249 (0 prod, 23 enfants) -> nouveau ID:1825 (0 prod, 7 enfants)
    (249, 1825),
    # Cyclisme : ancien ID:431 (0 prod, 27 enfants) -> nouveau ID:2104 (0 prod, 4 enfants)
    (431, 2104),
    # Manches Courtes Femme : ID:2173 (35 prod) -> ID:2165 (26 prod) - fusionner les produits
    (2173, 2165),
]

# ============================================================
# TRADUCTIONS L3 encore en anglais
# ============================================================
TRANSLATIONS = {
    # Santé & Beauté
    'Eyebrow Pencil': 'Crayons Sourcils',
    'Eyeshadow': 'Fards à Paupières',
    'False Eyelashes': 'Faux Cils',
    'Lipstick': 'Rouges à Lèvres',
    'Makeup Brushes': 'Pinceaux Maquillage',
    'Makeup Set': 'Coffrets Maquillage',
    'Nail Art Kits': 'Kits Nail Art',
    'Nail Decorations': 'Décorations Ongles',
    'Nail Glitters': 'Paillettes Ongles',
    'Body Care': 'Soins du Corps',
    'Face Masks': 'Masques Visage',
    'Facial Care': 'Soins du Visage',
    'Razor': 'Rasoirs',
    'Human Hair Wigs': 'Perruques Naturelles',
    'Synthetic Wigs': 'Perruques Synthétiques',
    'Hair Weaving': 'Tissage Cheveux',
    'Hair Weaves': 'Tissages',
    'Food & Health': 'Alimentation & Santé',
    'Curling Iron': 'Fer à Boucler',
    'Straightening Irons': 'Lisseurs',
    'Wigs & Extensions': 'Perruques & Extensions',
    # Mode
    "Men's Long-Sleeved": 'Manches Longues Homme',
    'Geometric': 'Géométrique',
    'Striped': 'Rayé',
    'Solid': 'Uni',
    '3D': '3D',
    'Print': 'Imprimé',
}

# ============================================================
# PRODUITS DANS L1 -> sous-catégorie appropriée
# (mots_clés, target_mps_l2_or_l3_id)
# On les déterminera dynamiquement après avoir vu les catégories disponibles
# ============================================================

with app.app_context():
    print("="*80)
    print("NETTOYAGE COMPLET")
    print("="*80)
    
    # --- 1. TRADUCTIONS ---
    print("\n--- 1. Traductions ---\n")
    translated = 0
    all_cats = Category.query.all()
    for cat in all_cats:
        if cat.name in TRANSLATIONS:
            old = cat.name
            cat.name = TRANSLATIONS[cat.name]
            cat.name_fr = cat.name
            print(f"  {old} -> {cat.name}")
            translated += 1
    db.session.commit()
    print(f"  Total traduit: {translated}")
    
    # --- 2. FUSION DES DOUBLONS ---
    print("\n--- 2. Fusion des doublons ---\n")
    
    for old_id, new_id in DUPLICATES:
        old_cat = db.session.get(Category, old_id)
        new_cat = db.session.get(Category, new_id)
        
        if not old_cat or not new_cat:
            print(f"  SKIP: ID:{old_id} ou ID:{new_id} non trouvé")
            continue
        
        print(f"  Fusion: '{old_cat.name}' (ID:{old_id}) -> '{new_cat.name}' (ID:{new_id})")
        
        # Migrer les produits
        prods = Product.query.filter_by(category_id=old_id).all()
        for p in prods:
            p.category_id = new_id
        print(f"    Produits migrés: {len(prods)}")
        
        # Migrer les enfants (sous-catégories)
        children = Category.query.filter_by(parent_id=old_id).all()
        for child in children:
            # Vérifier si un enfant avec le même nom existe déjà sous new_id
            existing = Category.query.filter_by(parent_id=new_id, name=child.name).first()
            if existing:
                # Migrer les produits de l'enfant doublon vers l'existant
                child_prods = Product.query.filter_by(category_id=child.id).all()
                for p in child_prods:
                    p.category_id = existing.id
                # Migrer les petits-enfants
                grandchildren = Category.query.filter_by(parent_id=child.id).all()
                for gc in grandchildren:
                    gc_existing = Category.query.filter_by(parent_id=existing.id, name=gc.name).first()
                    if gc_existing:
                        gc_prods = Product.query.filter_by(category_id=gc.id).all()
                        for p in gc_prods:
                            p.category_id = gc_existing.id
                        print(f"    Petit-enfant fusionné: {gc.name} -> {gc_existing.id}")
                    else:
                        gc.parent_id = existing.id
                        print(f"    Petit-enfant déplacé: {gc.name} -> sous {existing.name}")
                print(f"    Enfant fusionné: {child.name} ({len(child_prods)} prods)")
            else:
                child.parent_id = new_id
                print(f"    Enfant déplacé: {child.name}")
        
        # Marquer l'ancienne catégorie comme inactive
        old_cat.is_active = False
        old_cat.visible = False
    
    db.session.commit()
    
    # --- 3. RECLASSER LES PRODUITS DANS L1 ---
    print("\n--- 3. Reclassement des produits dans L1 ---\n")
    
    # Trouver les catégories L2/L3 appropriées pour chaque type de produit
    # On cherche par nom de catégorie
    def find_cat_by_name_under(parent_id, name_fragment):
        """Trouver une sous-catégorie par fragment de nom"""
        cats = Category.query.filter_by(parent_id=parent_id).filter(
            Category.name.ilike(f'%{name_fragment}%')
        ).first()
        return cats
    
    def find_any_cat_by_name(name_fragment, level=None):
        """Trouver une catégorie par fragment de nom"""
        q = Category.query.filter(Category.name.ilike(f'%{name_fragment}%'))
        if level:
            q = q.filter_by(level=level)
        return q.first()
    
    # Règles pour reclasser les produits dans L1
    # Format: (mps_l1_id, mots_clés_produit, catégorie_cible_nom_fragment)
    L1_RECLASSIFY = [
        # Mode & Vêtements (74 produits)
        (52, ['bra', 'underwear', 'lingerie', 'bodysuit', 'panties'], 'Sous-Vêtements'),
        (52, ['swimsuit', 'bikini', 'swimwear'], 'Maillots de Bain'),
        (52, ['dress'], 'Robes'),
        (52, ['shirt', 'blouse', 'top'], 'Blouses'),
        (52, ['necklace', 'bracelet', 'earring', 'ring', 'pendant'], 'Bijoux Fantaisie'),
        # Maison & Jardin (11 produits)
        (67, ['packaging', 'express bag', 'sticker', 'label', 'card', 'hang tag', 'biodegradable'], 'Rangement'),
        (67, ['jewelry storage', 'velvet'], 'Rangement'),
        (67, ['towel bra'], None),  # Sera traité par Mode
        # Santé & Beauté (8 produits)
        (87, ['massage', 'massager', 'pillow'], 'Massage'),
        (87, ['photon skin', 'rejuvenation', 'moisturizing', 'hydrating'], 'Soins'),
        (87, ['infrared', 'therapeutic', 'lumbar'], 'Massage'),
        # Sports & Loisirs (2 produits)
        (100, ['sports bra', 'yoga'], 'Accessoires de Sport'),
        # Bébés & Puériculture (3 produits)
        (113, ['nursing bra', 'maternity', 'pregnancy'], 'Soins Bébé'),
        # Informatique (1 produit)
        (22, ['heated', 'vibrating', 'shoulder', 'knee', 'elbow'], None),  # Santé
    ]
    
    mps_l1_ids = [52, 67, 87, 100, 113, 22]
    total_reclassed = 0
    
    for l1_id in mps_l1_ids:
        prods = Product.query.filter_by(category_id=l1_id).filter(
            Product.cj_pid.isnot(None)
        ).all()
        
        if not prods:
            continue
        
        l1 = db.session.get(Category, l1_id)
        print(f"\n  {l1.name} ({len(prods)} produits dans L1):")
        
        for p in prods:
            nl = p.name.lower()
            moved = False
            
            for rule_l1_id, keywords, target_name in L1_RECLASSIFY:
                if rule_l1_id != l1_id:
                    continue
                if not any(kw in nl for kw in keywords):
                    continue
                
                if target_name is None:
                    # Cas spécial : reclasser dans une autre catégorie L1
                    if 'towel bra' in nl or 'halter towel' in nl:
                        # C'est Mode
                        target = find_any_cat_by_name('Sous-Vêtements', level=None)
                    elif 'heated' in nl and 'vibrating' in nl:
                        target = find_any_cat_by_name('Massage', level=None)
                    else:
                        continue
                else:
                    # Chercher la sous-catégorie sous le L1
                    target = None
                    l2s = Category.query.filter_by(parent_id=l1_id, level=2, is_active=True).all()
                    for l2 in l2s:
                        if target_name.lower() in l2.name.lower():
                            target = l2
                            break
                        # Chercher dans les L3
                        l3s = Category.query.filter_by(parent_id=l2.id, level=3).all()
                        for l3 in l3s:
                            if target_name.lower() in l3.name.lower():
                                target = l3
                                break
                        if target:
                            break
                
                if target and target.id != p.category_id:
                    print(f"    {p.name[:50]:<50} -> {target.full_path}")
                    p.category_id = target.id
                    total_reclassed += 1
                    moved = True
                    break
            
            if not moved:
                # Essayer de trouver via la catégorie CJ originale
                if p.cj_raw_data:
                    try:
                        raw = json.loads(p.cj_raw_data)
                        cid = str(raw.get('categoryId') or raw.get('category_id') or '')
                        if cid:
                            cj = Category.query.filter_by(cj_category_id=cid).first()
                            if cj:
                                print(f"    RESTE L1: {p.name[:45]} | CJ: {cj.full_path}")
                            else:
                                print(f"    RESTE L1: {p.name[:45]} | CJ: NOT_FOUND")
                        else:
                            print(f"    RESTE L1: {p.name[:45]} | CJ: NO_CID")
                    except:
                        print(f"    RESTE L1: {p.name[:45]} | CJ: ERROR")
                else:
                    print(f"    RESTE L1: {p.name[:45]} | NO_RAW")
    
    db.session.commit()
    print(f"\n  Total reclassés: {total_reclassed}")
    
    # --- RÉSUMÉ ---
    print(f"\n{'='*80}")
    print("RÉSUMÉ")
    print(f"{'='*80}")
    
    from sqlalchemy import func
    
    # Produits encore dans L1
    for l1_id in mps_l1_ids:
        count = Product.query.filter_by(category_id=l1_id).filter(
            Product.cj_pid.isnot(None)
        ).count()
        if count > 0:
            l1 = db.session.get(Category, l1_id)
            print(f"  ⚠ {l1.name}: encore {count} produits dans L1")
    
    # Distribution top 20
    print(f"\nDistribution (top 20):")
    dist = Product.query.filter(Product.cj_pid.isnot(None)).with_entities(
        Product.category_id, func.count(Product.id)
    ).group_by(Product.category_id).all()
    
    for cat_id, count in sorted(dist, key=lambda x: x[1], reverse=True)[:20]:
        cat = db.session.get(Category, cat_id) if cat_id else None
        print(f"  {count:>6} | {cat.full_path if cat else 'AUCUNE'}")
