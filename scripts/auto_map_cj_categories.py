"""
Script de mapping automatique des catégories CJ Dropshipping vers MPS
Crée les catégories MPS manquantes et établit les mappings automatiquement
"""
import sys
import os
import sqlite3
import requests
from datetime import datetime
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')

def slugify(text):
    """Convertir un texte en slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

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

def get_existing_mps_categories():
    """Récupérer les catégories MPS existantes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, slug, parent_id, level FROM category")
    categories = {}
    
    for row in cursor.fetchall():
        categories[row[1].lower()] = {
            'id': row[0],
            'name': row[1],
            'slug': row[2],
            'parent_id': row[3],
            'level': row[4]
        }
    
    conn.close()
    return categories

def create_mps_category(name, parent_id=None, level=1, icon='fa-box'):
    """Créer une catégorie MPS"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    slug = slugify(name)
    
    # Vérifier si le slug existe déjà
    cursor.execute("SELECT id FROM category WHERE slug = ?", (slug,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return existing[0]
    
    # Créer la catégorie
    cursor.execute("""
        INSERT INTO category (name, slug, parent_id, level, icon, is_active, "order")
        VALUES (?, ?, ?, ?, ?, 1, 0)
    """, (name, slug, parent_id, level, icon))
    
    category_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return category_id

def get_existing_mappings(provider_id):
    """Récupérer les mappings existants"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT external_category_id, mps_category_id
        FROM category_mapping
        WHERE provider_id = ?
    """, (provider_id,))
    
    mappings = {}
    for row in cursor.fetchall():
        mappings[row[0]] = row[1]
    
    conn.close()
    return mappings

def create_mapping(provider_id, external_cat_id, external_cat_name, external_cat_path, mps_cat_id):
    """Créer un mapping catégorie"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO category_mapping 
        (provider_id, external_category_id, external_category_name, external_category_path, 
         mps_category_id, auto_import, apply_markup, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 1, 1.3, ?, ?)
    """, (provider_id, external_cat_id, external_cat_name, external_cat_path, 
          mps_cat_id, datetime.utcnow(), datetime.utcnow()))
    
    conn.commit()
    conn.close()

def auto_map_categories():
    """Mapper automatiquement les catégories CJ vers MPS"""
    
    print("="*80)
    print("MAPPING AUTOMATIQUE DES CATÉGORIES CJ DROPSHIPPING")
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
        print("   Attendez 5 minutes si vous avez un rate limit")
        return False
    
    print("✓ Access token obtenu")
    
    # 3. Récupérer les catégories CJ
    print("\n3. Récupération des catégories CJ...")
    cj_categories = get_cj_categories(access_token, endpoint)
    
    if not cj_categories:
        print("✗ Aucune catégorie CJ récupérée")
        return False
    
    print(f"✓ {len(cj_categories)} catégories CJ récupérées")
    
    # 4. Récupérer les catégories MPS existantes
    print("\n4. Récupération des catégories MPS existantes...")
    mps_categories = get_existing_mps_categories()
    print(f"✓ {len(mps_categories)} catégories MPS existantes")
    
    # 5. Récupérer les mappings existants
    print("\n5. Récupération des mappings existants...")
    existing_mappings = get_existing_mappings(provider_id)
    print(f"✓ {len(existing_mappings)} mappings existants")
    
    # 6. Créer les catégories MPS manquantes et les mappings
    print("\n6. Création des catégories MPS et mappings...")
    print("-" * 80)
    
    created_categories = 0
    created_mappings = 0
    skipped_mappings = 0
    
    # Dictionnaire pour stocker les IDs des catégories de niveau 1 et 2
    level1_cache = {}
    level2_cache = {}
    
    for cj_cat in cj_categories:
        # Vérifier si le mapping existe déjà
        if cj_cat['id'] in existing_mappings:
            skipped_mappings += 1
            continue
        
        # Créer ou récupérer la catégorie de niveau 1
        first_level_name = cj_cat['first_level']
        if first_level_name not in level1_cache:
            if first_level_name.lower() in mps_categories:
                level1_cache[first_level_name] = mps_categories[first_level_name.lower()]['id']
            else:
                level1_id = create_mps_category(first_level_name, parent_id=None, level=1, icon='fa-folder')
                level1_cache[first_level_name] = level1_id
                mps_categories[first_level_name.lower()] = {
                    'id': level1_id,
                    'name': first_level_name,
                    'level': 1
                }
                created_categories += 1
                print(f"  ✓ Créé niveau 1: {first_level_name}")
        
        # Créer ou récupérer la catégorie de niveau 2
        second_level_name = cj_cat['second_level']
        second_level_key = f"{first_level_name}|{second_level_name}"
        
        if second_level_key not in level2_cache:
            if second_level_name.lower() in mps_categories:
                level2_cache[second_level_key] = mps_categories[second_level_name.lower()]['id']
            else:
                level2_id = create_mps_category(
                    second_level_name, 
                    parent_id=level1_cache[first_level_name], 
                    level=2, 
                    icon='fa-folder-open'
                )
                level2_cache[second_level_key] = level2_id
                mps_categories[second_level_name.lower()] = {
                    'id': level2_id,
                    'name': second_level_name,
                    'level': 2
                }
                created_categories += 1
                print(f"    ✓ Créé niveau 2: {second_level_name}")
        
        # Créer ou récupérer la catégorie de niveau 3
        cat_name = cj_cat['name']
        
        if cat_name.lower() in mps_categories:
            mps_cat_id = mps_categories[cat_name.lower()]['id']
        else:
            mps_cat_id = create_mps_category(
                cat_name, 
                parent_id=level2_cache[second_level_key], 
                level=3, 
                icon='fa-tag'
            )
            mps_categories[cat_name.lower()] = {
                'id': mps_cat_id,
                'name': cat_name,
                'level': 3
            }
            created_categories += 1
            print(f"      ✓ Créé niveau 3: {cat_name}")
        
        # Créer le mapping
        create_mapping(
            provider_id,
            cj_cat['id'],
            cj_cat['name'],
            cj_cat['path'],
            mps_cat_id
        )
        created_mappings += 1
    
    # 7. Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ")
    print("="*80)
    print(f"✓ Catégories CJ récupérées: {len(cj_categories)}")
    print(f"✓ Catégories MPS créées: {created_categories}")
    print(f"✓ Mappings créés: {created_mappings}")
    print(f"✓ Mappings existants (ignorés): {skipped_mappings}")
    print(f"\n✓ Total mappings: {created_mappings + skipped_mappings}/{len(cj_categories)}")
    print("\n✅ Mapping automatique terminé avec succès!")
    
    return True

if __name__ == '__main__':
    try:
        success = auto_map_categories()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
