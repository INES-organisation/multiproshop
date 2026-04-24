"""
Script de mapping ROBUSTE avec exclusions explicites
pour éviter TOUS les faux positifs
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from models.category import Category

# VRAIS IDs des catégories MPS principales
CATEGORY_IDS = {
    'electronique': 1,
    'informatique': 22,
    'telephonie': 38,
    'mode': 52,
    'maison': 67,
    'beaute': 87,
    'sport': 100,
    'bebe': 113,
    'jouets': 126,
    'auto': 139,
    'animaux': 178,
}

def get_robust_category(product_name):
    """
    Déterminer la catégorie avec une logique ROBUSTE
    Priorité: exclusions explicites > mots-clés spécifiques > catégorie par défaut
    """
    name_lower = product_name.lower()
    
    # ============================================================================
    # EXCLUSIONS EXPLICITES - Vérifier EN PREMIER
    # ============================================================================
    
    # Exclure TOUS les capteurs/senseurs auto (de toutes catégories)
    auto_sensor_keywords = [
        'abs sensor', 'wheel speed sensor', 'brake pad wear sensor',
        'speed sensor', 'odometer sensor', 'tire sensor', 'car sensor',
        'automotive sensor', 'vehicle sensor', 'oxygen sensor', 'temperature sensor',
        'maf sensor', 'air flow sensor', 'o2 sensor', 'fuel ratio sensor',
        'oil pressure sensor', 'knock sensor', 'brake oil', 'map sensor',
        'manifold pressure sensor', 'cadence sensor ant'
    ]
    for keyword in auto_sensor_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['auto']
    
    # Exclure les accessoires auto de Mode
    auto_accessory_keywords = [
        'car key', 'key shell', 'remote control key',
        'carplay', 'car charger', 'car wash', 'car cover',
        'dash cam', 'parking sensor', 'diagnostic scan',
        'obd2', 'elm327', 'car bluetooth'
    ]
    for keyword in auto_accessory_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['auto']
    
    # Exclure les notebooks/cahiers de Sport
    if 'notebook' in name_lower or 'exercise book' in name_lower or 'notepad' in name_lower:
        return CATEGORY_IDS['electronique']  # Papeterie -> Électronique par défaut
    
    # Exclure les alarmes/horloges de Sport
    if 'alarm clock' in name_lower or 'clock' in name_lower:
        return CATEGORY_IDS['maison']
    
    # Exclure les souris gaming/informatique de Sport et Électronique
    if 'gaming mouse' in name_lower or 'esports' in name_lower:
        return CATEGORY_IDS['informatique']
    
    if 'mouse' in name_lower and any(kw in name_lower for kw in ['wireless', 'car mouse', 'notebook', 'desktop']):
        return CATEGORY_IDS['informatique']
    
    # Jouets sensoriels -> Jouets (pas Électronique)
    if 'fidget toy' in name_lower or 'sensory toy' in name_lower or 'stress-relief toy' in name_lower:
        return CATEGORY_IDS['jouets']
    
    # Exclure les supports de téléphone de Sport
    if 'phone holder' in name_lower or 'phone case' in name_lower:
        if 'gym' in name_lower or 'treadmill' in name_lower:
            return CATEGORY_IDS['sport']
        return CATEGORY_IDS['telephonie']
    
    # Exclure les accessoires téléphone/câbles avec motifs animaux de Animalerie
    if any(kw in name_lower for kw in ['phone', 'cable', 'charger', 'charging']):
        if any(kw in name_lower for kw in ['puppy', 'kitten', 'dog', 'cat']):
            # C'est un accessoire téléphone avec motif animal, pas un produit pour animaux
            return CATEGORY_IDS['telephonie']
    
    # Exclure les vêtements/accessoires mode avec motifs animaux de Animalerie
    if 'scarf' in name_lower:
        return CATEGORY_IDS['mode']
    
    # Pendentifs de voiture -> Auto, autres pendentifs -> Mode
    if 'pendant' in name_lower:
        if 'car ' in name_lower or 'rearview mirror' in name_lower:
            return CATEGORY_IDS['auto']
        return CATEGORY_IDS['mode']
    
    # ============================================================================
    # CATÉGORIES PAR PRIORITÉ
    # ============================================================================
    
    # 1. BEAUTÉ & SANTÉ (priorité maximale)
    beauty_keywords = [
        'makeup', 'cosmetic', 'lipstick', 'mascara', 'eyeshadow', 'foundation',
        'skincare', 'cream', 'serum', 'moisturizer', 'facial',
        'perfume', 'fragrance', 'nail polish',
        'shampoo', 'conditioner', 'hair care'
    ]
    for keyword in beauty_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['beaute']
    
    # 2. AUTO & MOTO (haute priorité pour capturer tous les produits auto)
    auto_keywords = [
        'car ', 'auto ', 'vehicle', 'automotive', 'motorcycle',
        'tire', 'wheel', 'engine', 'motor ',
        'mercedes', 'bmw', 'audi', 'volkswagen', 'toyota', 'honda',
        'abs ', 'brake pad', 'intake manifold',
        'fits vw', 'fits civic', 'fits chrysler', 'fits buick',
        'electric bicycle speed', 'bicycle speed power sensor'
    ]
    for keyword in auto_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['auto']
    
    # Doorbell/Alarm/Détecteurs maison -> Maison (pas Auto)
    if 'doorbell' in name_lower or 'welcome device' in name_lower:
        return CATEGORY_IDS['maison']
    
    if 'alarm' in name_lower or 'detector' in name_lower:
        # Alarmes/détecteurs pour la maison (CO, overflow, motion, etc.)
        if any(kw in name_lower for kw in ['carbon monoxide', 'overflow', 'motion', 'pir', 'smoke']):
            return CATEGORY_IDS['maison']
    
    # Capteurs génériques (non-auto) -> Électronique
    if 'sensor' in name_lower:
        # Si c'est un capteur domestique/électronique
        if any(kw in name_lower for kw in ['tds', 'water', 'humidity', 'temperature', 'rfid', 'soap dispenser']):
            return CATEGORY_IDS['electronique']
    
    # 3. MAISON & JARDIN (haute priorité)
    home_keywords = [
        'furniture', 'chair', 'table', 'sofa', 'couch', 'bed',
        'lamp', 'light', 'chandelier', 'ceiling light',
        'curtain', 'rug', 'carpet', 'pillow', 'cushion',
        'vase', 'candle', 'decoration',
        'kitchen', 'cookware', 'pot', 'pan', 'plate', 'bowl', 'cup',
        'garden', 'plant', 'planter', 'raised bed', 'trellis'
    ]
    for keyword in home_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['maison']
    
    # 4. MODE & VÊTEMENTS (vérifier APRÈS Auto pour éviter les capteurs)
    fashion_keywords = [
        # Vêtements femme/homme
        'womens ', 'women ', 'mens ', 'ladies ',
        'dress', 'blouse', 'skirt', 'shirt', 'top',
        'pants', 'trousers', 'jeans', 'shorts',
        'jacket', 'coat', 'sweater', 'hoodie', 'cardigan',
        'romper', 'jumpsuit', 'pajama',
        # Chaussures (mais pas "brake pad")
        'shoes', 'boots', 'sneakers', 'sandals', 'slippers', 'heels', 'flats',
        # Accessoires mode
        'handbag', 'purse', 'wallet', 'scarf', 'glove', 'hat', 'cap',
        'jewelry', 'necklace', 'bracelet', 'ring', 'earring',
        'watch', 'watches'
    ]
    # Vérifier qu'il ne s'agit pas d'un produit auto
    is_auto_product = any(kw in name_lower for kw in ['sensor', 'brake', 'abs', 'car', 'vehicle', 'automotive'])
    if not is_auto_product:
        for keyword in fashion_keywords:
            if keyword in name_lower:
                return CATEGORY_IDS['mode']
    
    # 5. BÉBÉS & PUÉRICULTURE
    baby_keywords = [
        'baby clothes', 'baby romper', 'baby onesie',
        'newborn', 'infant',
        'stroller', 'crib', 'high chair',
        'pacifier', 'teether', 'baby bottle'
    ]
    for keyword in baby_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['bebe']
    
    # 6. JEUX & JOUETS
    toys_keywords = [
        'plush toy', 'stuffed toy', 'toy doll',
        'lego', 'building blocks', 'magnetic tiles',
        'rocking horse', 'ride-on toy',
        'cat toy', 'dog toy', 'pet toy',
        'kids toy', 'children toy'
    ]
    for keyword in toys_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['jouets']
    
    # 7. SPORTS & LOISIRS (vérifier APRÈS exclusions)
    sport_keywords = [
        'fitness', 'gym equipment', 'workout',
        'dumbbell', 'barbell', 'kettlebell', 'resistance band',
        'foam roller', 'yoga mat',
        'camping tent', 'sleeping bag',
        'fishing rod', 'fishing reel',
        'basketball', 'football', 'soccer ball'
    ]
    for keyword in sport_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['sport']
    
    # 8. ANIMALERIE
    pet_keywords = [
        'dog collar', 'cat collar', 'dog leash', 'pet leash',
        'dog food', 'cat food', 'pet food',
        'puppy', 'kitten'
    ]
    for keyword in pet_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['animaux']
    
    # 9. TÉLÉPHONIE & TABLETTES
    phone_keywords = [
        'phone', 'smartphone', 'iphone', 'samsung',
        'tablet', 'ipad',
        'phone case', 'screen protector'
    ]
    for keyword in phone_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['telephonie']
    
    # 10. INFORMATIQUE
    computer_keywords = [
        'laptop', 'computer', 'pc', 'macbook',
        'keyboard', 'mouse', 'monitor',
        'processor', 'cpu', 'gpu', 'ram', 'ssd',
        'motherboard', 'graphics card'
    ]
    for keyword in computer_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['informatique']
    
    # 11. ÉLECTRONIQUE & HIGH-TECH (par défaut)
    electronics_keywords = [
        'camera', 'lens', 'drone',
        'headphone', 'earphone', 'speaker',
        'charger', 'cable', 'adapter', 'power bank',
        'gaming', 'console', 'controller',
        'bluetooth', 'wireless'
    ]
    for keyword in electronics_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['electronique']
    
    # Par défaut: Électronique & High-Tech
    return CATEGORY_IDS['electronique']

def robust_remapping():
    """Remapping ROBUSTE de tous les produits CJ"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("REMAPPING ROBUSTE AVEC EXCLUSIONS EXPLICITES")
        print("="*80 + "\n")
        
        # Récupérer tous les produits CJ
        cj_products = Product.query.filter(Product.cj_pid.isnot(None)).all()
        print(f"Produits CJ à remapper: {len(cj_products)}")
        
        # Statistiques
        remapped_count = 0
        category_stats = {}
        changes = {}
        
        # Remapper chaque produit
        for product in cj_products:
            old_category_id = product.category_id
            
            # Déterminer la nouvelle catégorie
            new_category_id = get_robust_category(product.name)
            
            # Mettre à jour si différent
            if old_category_id != new_category_id:
                product.category_id = new_category_id
                
                # Tracker les changements
                if old_category_id not in changes:
                    changes[old_category_id] = {}
                if new_category_id not in changes[old_category_id]:
                    changes[old_category_id][new_category_id] = 0
                changes[old_category_id][new_category_id] += 1
                
                remapped_count += 1
            
            # Stats
            if new_category_id not in category_stats:
                category_stats[new_category_id] = 0
            category_stats[new_category_id] += 1
            
            if remapped_count % 1000 == 0 and remapped_count > 0:
                print(f"  Remappé: {remapped_count} produits...")
                db.session.commit()
        
        # Commit final
        db.session.commit()
        
        print(f"\n✅ Remapping terminé: {remapped_count} produits modifiés sur {len(cj_products)}")
        
        # Afficher les statistiques
        print("\n" + "="*80)
        print("RÉPARTITION FINALE PAR CATÉGORIE MPS")
        print("="*80 + "\n")
        
        for cat_id, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            cat = Category.query.get(cat_id)
            if cat:
                print(f"  {cat.name:50} : {count:6} produits")
        
        print("\n" + "="*80)
        print("✅ REMAPPING ROBUSTE TERMINÉ")
        print("="*80 + "\n")

if __name__ == '__main__':
    robust_remapping()
