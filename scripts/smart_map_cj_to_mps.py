"""
Script intelligent de mapping des catégories CJ vers les catégories MPS françaises existantes
Ne crée PAS de nouvelles catégories, mappe uniquement vers les catégories françaises existantes
"""
import sys
import os
import sqlite3
import requests
from datetime import datetime
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')

def get_cj_credentials():
    """Récupérer les identifiants CJ depuis la DB"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, api_key, api_secret, api_endpoint
        FROM api_provider 
        WHERE slug = 'cj-dropshipping'
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    return result

def get_access_token(api_key, api_secret, endpoint):
    """Obtenir un access token CJ"""
    api_key_formatted = f"{api_key}@api@{api_secret}"
    
    url = f"{endpoint}/authentication/getAccessToken"
    
    try:
        response = requests.post(
            url,
            json={"apiKey": api_key_formatted},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                return data.get('data', {}).get('accessToken')
        
        print(f"Erreur obtention token: {response.text}")
        return None
    except Exception as e:
        print(f"Erreur: {e}")
        return None

def get_cj_categories(access_token, endpoint):
    """Récupérer toutes les catégories CJ"""
    url = f"{endpoint}/product/getCategory"
    headers = {
        'CJ-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == 200:
                raw_data = data.get('data', [])
                
                categories = []
                for first_level in raw_data:
                    first_name = first_level.get('categoryFirstName', '')
                    
                    for second_level in first_level.get('categoryFirstList', []):
                        second_name = second_level.get('categorySecondName', '')
                        
                        for category in second_level.get('categorySecondList', []):
                            categories.append({
                                'id': category.get('categoryId'),
                                'name': category.get('categoryName'),
                                'first_level': first_name,
                                'second_level': second_name,
                                'path': f"{first_name} > {second_name} > {category.get('categoryName')}"
                            })
                
                return categories
        
        print(f"Erreur API: {response.text}")
        return []
    except Exception as e:
        print(f"Erreur récupération catégories: {e}")
        return []

def get_mps_french_categories():
    """Récupérer uniquement les catégories MPS françaises (les 17 principales + leurs enfants)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Catégories françaises principales
    french_main_categories = [
        'Électronique & High-Tech',
        'Informatique',
        'Téléphonie & Tablettes',
        'Mode & Vêtements',
        'Maison & Jardin',
        'Santé & Beauté',
        'Sports & Loisirs',
        'Bébés & Puériculture',
        'Jeux & Jouets',
        'Auto & Moto',
        'Bricolage & Outillage',
        'Alimentation & Boissons',
        'Animalerie',
        'Livres & Papeterie',
        'Culture & Divertissement',
        'Services & Bons Plans',
        'Immobilier & Véhicules'
    ]
    
    cursor.execute("SELECT id, name, slug, parent_id, level FROM category")
    all_categories = cursor.fetchall()
    
    # Récupérer les IDs des catégories principales françaises
    french_ids = set()
    categories_dict = {}
    
    for row in all_categories:
        cat_id, name, slug, parent_id, level = row
        if name in french_main_categories:
            french_ids.add(cat_id)
        categories_dict[cat_id] = {
            'id': cat_id,
            'name': name,
            'slug': slug,
            'parent_id': parent_id,
            'level': level
        }
    
    # Ajouter tous les enfants des catégories françaises
    def add_children(parent_id):
        for cat_id, cat_data in categories_dict.items():
            if cat_data['parent_id'] == parent_id and cat_id not in french_ids:
                french_ids.add(cat_id)
                add_children(cat_id)
    
    for french_id in list(french_ids):
        add_children(french_id)
    
    # Créer le dictionnaire final avec seulement les catégories françaises
    french_categories = {}
    for cat_id in french_ids:
        cat_data = categories_dict[cat_id]
        french_categories[cat_data['name'].lower()] = cat_data
    
    conn.close()
    return french_categories

def find_best_match(cj_category, mps_categories):
    """Trouver la meilleure correspondance entre une catégorie CJ et les catégories MPS"""
    
    # Dictionnaire de mapping manuel pour les catégories principales
    manual_mappings = {
        # Électronique
        'consumer electronics': 'électronique & high-tech',
        'electronics': 'électronique & high-tech',
        'phone': 'téléphonie & tablettes',
        'phones & accessories': 'téléphonie & tablettes',
        'mobile phone': 'téléphonie & tablettes',
        'computer & office': 'informatique',
        'computer': 'informatique',
        'laptop': 'informatique',
        'tablet': 'téléphonie & tablettes',
        
        # Mode
        "women's clothing": 'mode & vêtements',
        "men's clothing": 'mode & vêtements',
        'clothing': 'mode & vêtements',
        'bags & shoes': 'mode & vêtements',
        'jewelry & watches': 'mode & vêtements',
        'accessories': 'mode & vêtements',
        
        # Maison
        'home improvement': 'maison & jardin',
        'home, garden & furniture': 'maison & jardin',
        'furniture': 'maison & jardin',
        'garden': 'maison & jardin',
        'kitchen': 'maison & jardin',
        
        # Santé & Beauté
        'health, beauty & hair': 'santé & beauté',
        'beauty': 'santé & beauté',
        'health': 'santé & beauté',
        'makeup': 'santé & beauté',
        
        # Sports
        'sports & outdoors': 'sports & loisirs',
        'sports': 'sports & loisirs',
        'outdoor': 'sports & loisirs',
        'fitness': 'sports & loisirs',
        
        # Enfants
        'toys, kids & babies': 'bébés & puériculture',
        'baby': 'bébés & puériculture',
        'toys': 'jeux & jouets',
        
        # Auto
        'automobiles & motorcycles': 'auto & moto',
        'automotive': 'auto & moto',
        'motorcycle': 'auto & moto',
        
        # Animaux
        'pet supplies': 'animalerie',
        'pet': 'animalerie',
        
        # Bricolage
        'tools': 'bricolage & outillage',
        'hardware': 'bricolage & outillage',
    }
    
    # Essayer le mapping manuel d'abord
    cj_name_lower = cj_category['name'].lower()
    cj_first_lower = cj_category['first_level'].lower()
    cj_second_lower = cj_category['second_level'].lower()
    
    # Vérifier dans l'ordre: nom complet, second level, first level
    for cj_key in [cj_name_lower, cj_second_lower, cj_first_lower]:
        if cj_key in manual_mappings:
            target_name = manual_mappings[cj_key]
            if target_name in mps_categories:
                return mps_categories[target_name]['id']
    
    # Recherche par mots-clés
    keywords_mapping = {
        'phone': 'téléphonie & tablettes',
        'mobile': 'téléphonie & tablettes',
        'computer': 'informatique',
        'laptop': 'informatique',
        'tablet': 'téléphonie & tablettes',
        'clothing': 'mode & vêtements',
        'fashion': 'mode & vêtements',
        'dress': 'mode & vêtements',
        'shirt': 'mode & vêtements',
        'shoe': 'mode & vêtements',
        'bag': 'mode & vêtements',
        'watch': 'mode & vêtements',
        'jewelry': 'mode & vêtements',
        'home': 'maison & jardin',
        'garden': 'maison & jardin',
        'furniture': 'maison & jardin',
        'kitchen': 'maison & jardin',
        'beauty': 'santé & beauté',
        'health': 'santé & beauté',
        'makeup': 'santé & beauté',
        'skin': 'santé & beauté',
        'hair': 'santé & beauté',
        'sport': 'sports & loisirs',
        'fitness': 'sports & loisirs',
        'outdoor': 'sports & loisirs',
        'baby': 'bébés & puériculture',
        'toy': 'jeux & jouets',
        'game': 'jeux & jouets',
        'car': 'auto & moto',
        'auto': 'auto & moto',
        'motorcycle': 'auto & moto',
        'pet': 'animalerie',
        'animal': 'animalerie',
        'tool': 'bricolage & outillage',
    }
    
    full_text = f"{cj_first_lower} {cj_second_lower} {cj_name_lower}"
    
    for keyword, target_name in keywords_mapping.items():
        if keyword in full_text:
            if target_name in mps_categories:
                return mps_categories[target_name]['id']
    
    # Par défaut, retourner la catégorie "Électronique & High-Tech"
    default_cat = 'électronique & high-tech'
    if default_cat in mps_categories:
        return mps_categories[default_cat]['id']
    
    return None

def create_mapping(provider_id, external_cat_id, external_cat_name, external_cat_path, mps_cat_id):
    """Créer un mapping catégorie"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vérifier si le mapping existe déjà
    cursor.execute("""
        SELECT id FROM category_mapping 
        WHERE provider_id = ? AND external_category_id = ?
    """, (provider_id, external_cat_id))
    
    if cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute("""
        INSERT INTO category_mapping 
        (provider_id, external_category_id, external_category_name, external_category_path, 
         mps_category_id, auto_import, apply_markup, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 1, 1.3, ?, ?)
    """, (provider_id, external_cat_id, external_cat_name, external_cat_path, 
          mps_cat_id, datetime.utcnow(), datetime.utcnow()))
    
    conn.commit()
    conn.close()
    return True

def main():
    """Mapper intelligemment les catégories CJ vers MPS"""
    
    print("\n" + "="*80)
    print("MAPPING INTELLIGENT DES CATÉGORIES CJ VERS MPS FRANÇAIS")
    print("="*80)
    
    # 1. Récupérer les identifiants CJ
    print("\n1. Récupération des identifiants CJ...")
    cj_creds = get_cj_credentials()
    
    if not cj_creds:
        print("✗ Provider CJ Dropshipping non trouvé")
        return False
    
    provider_id, api_key, api_secret, endpoint = cj_creds
    print(f"✓ Provider ID: {provider_id}")
    
    # 2. Obtenir un access token
    print("\n2. Obtention de l'access token...")
    access_token = get_access_token(api_key, api_secret, endpoint)
    
    if not access_token:
        print("✗ Impossible d'obtenir l'access token")
        return False
    
    print("✓ Access token obtenu")
    
    # 3. Récupérer les catégories CJ
    print("\n3. Récupération des catégories CJ...")
    cj_categories = get_cj_categories(access_token, endpoint)
    
    if not cj_categories:
        print("✗ Aucune catégorie CJ récupérée")
        return False
    
    print(f"✓ {len(cj_categories)} catégories CJ récupérées")
    
    # 4. Récupérer les catégories MPS françaises
    print("\n4. Récupération des catégories MPS françaises...")
    mps_categories = get_mps_french_categories()
    print(f"✓ {len(mps_categories)} catégories MPS françaises")
    
    # 5. Créer les mappings
    print("\n5. Création des mappings intelligents...")
    print("-" * 80)
    
    created_mappings = 0
    skipped_mappings = 0
    mapping_stats = {}
    
    for cj_cat in cj_categories:
        # Trouver la meilleure correspondance
        mps_cat_id = find_best_match(cj_cat, mps_categories)
        
        if not mps_cat_id:
            print(f"  ⚠ Pas de correspondance pour: {cj_cat['name']}")
            continue
        
        # Récupérer le nom de la catégorie MPS
        mps_cat_name = None
        for name, data in mps_categories.items():
            if data['id'] == mps_cat_id:
                mps_cat_name = data['name']
                break
        
        # Créer le mapping
        if create_mapping(provider_id, cj_cat['id'], cj_cat['name'], cj_cat['path'], mps_cat_id):
            created_mappings += 1
            
            # Statistiques
            if mps_cat_name not in mapping_stats:
                mapping_stats[mps_cat_name] = 0
            mapping_stats[mps_cat_name] += 1
            
            if created_mappings <= 20:  # Afficher les 20 premiers
                print(f"  ✓ {cj_cat['name']:40} -> {mps_cat_name}")
        else:
            skipped_mappings += 1
    
    # 6. Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ DES MAPPINGS")
    print("="*80)
    print(f"\n✓ Catégories CJ récupérées: {len(cj_categories)}")
    print(f"✓ Mappings créés: {created_mappings}")
    print(f"✓ Mappings existants (ignorés): {skipped_mappings}")
    
    print("\n📊 Répartition par catégorie MPS:")
    print("-" * 80)
    for cat_name, count in sorted(mapping_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat_name:40} : {count:4} catégories CJ")
    
    print("\n✅ Mapping intelligent terminé avec succès!")
    print("\n💡 Les produits CJ seront automatiquement assignés aux catégories françaises")
    print("   lors de la synchronisation des produits.\n")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
