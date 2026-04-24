"""
Script de synchronisation complète des catégories CJ avec création automatique des mappings
- Synchronise les catégories CJ depuis l'API (pour affichage admin)
- Crée/met à jour les mappings vers les catégories MPS françaises
- Les catégories CJ sont marquées comme non visibles sur le site (visible=False)
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models.category import Category
from models.api_provider import ApiProvider, CategoryMapping
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from datetime import datetime
from slugify import slugify

def get_french_category_id(category_name):
    """Récupérer l'ID d'une catégorie française par son nom"""
    category = Category.query.filter_by(name=category_name).first()
    return category.id if category else None

def find_best_mps_match(cj_category_name, cj_first_level, cj_second_level):
    """Trouver la meilleure correspondance MPS pour une catégorie CJ"""
    
    # Dictionnaire de mapping manuel
    manual_mappings = {
        'consumer electronics': 'Électronique & High-Tech',
        'electronics': 'Électronique & High-Tech',
        'phone': 'Téléphonie & Tablettes',
        'phones & accessories': 'Téléphonie & Tablettes',
        'mobile phone': 'Téléphonie & Tablettes',
        'computer & office': 'Informatique',
        'computer': 'Informatique',
        'laptop': 'Informatique',
        'tablet': 'Téléphonie & Tablettes',
        "women's clothing": 'Mode & Vêtements',
        "men's clothing": 'Mode & Vêtements',
        'clothing': 'Mode & Vêtements',
        'bags & shoes': 'Mode & Vêtements',
        'jewelry & watches': 'Mode & Vêtements',
        'accessories': 'Mode & Vêtements',
        'home improvement': 'Maison & Jardin',
        'home, garden & furniture': 'Maison & Jardin',
        'furniture': 'Maison & Jardin',
        'garden': 'Maison & Jardin',
        'kitchen': 'Maison & Jardin',
        'health, beauty & hair': 'Santé & Beauté',
        'beauty': 'Santé & Beauté',
        'health': 'Santé & Beauté',
        'makeup': 'Santé & Beauté',
        'sports & outdoors': 'Sports & Loisirs',
        'sports': 'Sports & Loisirs',
        'outdoor': 'Sports & Loisirs',
        'fitness': 'Sports & Loisirs',
        'toys, kids & babies': 'Bébés & Puériculture',
        'baby': 'Bébés & Puériculture',
        'toys': 'Jeux & Jouets',
        'automobiles & motorcycles': 'Auto & Moto',
        'automotive': 'Auto & Moto',
        'motorcycle': 'Auto & Moto',
        'pet supplies': 'Animalerie',
        'pet': 'Animalerie',
        'tools': 'Bricolage & Outillage',
        'hardware': 'Bricolage & Outillage',
    }
    
    # Essayer le mapping manuel
    for cj_key in [cj_category_name.lower(), cj_second_level.lower(), cj_first_level.lower()]:
        if cj_key in manual_mappings:
            mps_name = manual_mappings[cj_key]
            mps_id = get_french_category_id(mps_name)
            if mps_id:
                return mps_id, mps_name
    
    # Par défaut, retourner Électronique & High-Tech
    default_name = 'Électronique & High-Tech'
    default_id = get_french_category_id(default_name)
    return default_id, default_name

def generate_unique_slug(base_name, cj_category_id):
    """Générer un slug unique pour une catégorie CJ"""
    base_slug = slugify(base_name)
    
    # Vérifier si le slug existe déjà
    existing = Category.query.filter_by(slug=base_slug).first()
    
    # Si le slug n'existe pas, ou s'il appartient à cette catégorie CJ, l'utiliser
    if not existing or existing.cj_category_id == cj_category_id:
        return base_slug
    
    # Si le slug existe, ajouter un suffixe avec l'ID CJ
    suffix = cj_category_id[:8].lower()
    unique_slug = f"{base_slug}-cj-{suffix}"
    
    # Vérifier que ce slug unique n'existe pas non plus
    counter = 1
    final_slug = unique_slug
    while Category.query.filter_by(slug=final_slug).first():
        final_slug = f"{unique_slug}-{counter}"
        counter += 1
    
    return final_slug

def sync_cj_categories_with_mappings():
    """Synchroniser les catégories CJ et créer les mappings"""
    
    with app.app_context():
        print("\n" + "="*80)
        print("SYNCHRONISATION COMPLÈTE CJ : CATÉGORIES + MAPPINGS")
        print("="*80)
        
        # 1. Récupérer le provider CJ
        print("\n1. Récupération du provider CJ...")
        provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
        
        if not provider:
            print("❌ Provider CJ Dropshipping non trouvé")
            return False
        
        print(f"✓ Provider ID: {provider.id}")
        
        # 2. Initialiser l'API CJ
        print("\n2. Initialisation de l'API CJ...")
        try:
            # L'API CJ utilise email/password, pas api_key/api_secret
            # Les credentials sont stockés dans api_key (format: email) et api_secret (format: password)
            cj_api = CJDropshippingApiOptimized(
                email=provider.api_key,
                password=provider.api_secret
            )
            print("✓ API CJ initialisée")
        except Exception as e:
            print(f"❌ Erreur initialisation API: {e}")
            return False
        
        # 3. Récupérer les catégories depuis l'API CJ
        print("\n3. Récupération des catégories CJ depuis l'API...")
        try:
            cj_categories = cj_api.get_categories()
            print(f"✓ {len(cj_categories)} catégories CJ récupérées")
        except Exception as e:
            print(f"❌ Erreur récupération catégories: {e}")
            return False
        
        # 4. Synchroniser les catégories CJ
        print("\n4. Synchronisation des catégories CJ...")
        print("-" * 80)
        
        synced_categories = 0
        created_categories = 0
        updated_categories = 0
        
        for cj_cat in cj_categories:
            cj_id = cj_cat.get('cj_category_id')
            cj_name = cj_cat.get('name', '')
            
            if not cj_id:
                continue
            
            # Chercher si la catégorie CJ existe déjà
            category = Category.query.filter_by(cj_category_id=cj_id).first()
            
            if category:
                # Mettre à jour
                category.name = cj_name
                category.level = cj_cat.get('level', 1)
                category.product_count = cj_cat.get('product_count', 0)
                category.last_sync = datetime.utcnow()
                category.visible = False  # Non visible sur le site
                updated_categories += 1
            else:
                # Créer nouvelle catégorie CJ
                unique_slug = generate_unique_slug(cj_name, cj_id)
                
                category = Category(
                    name=cj_name,
                    slug=unique_slug,
                    cj_category_id=cj_id,
                    level=cj_cat.get('level', 1),
                    product_count=cj_cat.get('product_count', 0),
                    visible=False,  # Non visible sur le site (uniquement pour admin)
                    is_active=True,
                    last_sync=datetime.utcnow()
                )
                db.session.add(category)
                created_categories += 1
            
            synced_categories += 1
            
            if synced_categories <= 20:  # Afficher les 20 premières
                status = "MAJ" if category.id else "CRÉÉ"
                print(f"  {status:4} {cj_name:50} (Niveau {cj_cat.get('level', 1)})")
        
        db.session.commit()
        print(f"\n✓ {synced_categories} catégories CJ synchronisées")
        print(f"  - Créées: {created_categories}")
        print(f"  - Mises à jour: {updated_categories}")
        
        # 5. Créer les mappings vers les catégories MPS françaises
        print("\n5. Création des mappings CJ → MPS...")
        print("-" * 80)
        
        created_mappings = 0
        skipped_mappings = 0
        mapping_stats = {}
        
        for cj_cat in cj_categories:
            cj_id = cj_cat.get('cj_category_id')
            cj_name = cj_cat.get('name', '')
            cj_first = cj_cat.get('first_level', '')
            cj_second = cj_cat.get('second_level', '')
            cj_path = cj_cat.get('path', cj_name)
            
            if not cj_id:
                continue
            
            # Vérifier si le mapping existe déjà
            existing_mapping = CategoryMapping.query.filter_by(
                provider_id=provider.id,
                external_category_id=cj_id
            ).first()
            
            if existing_mapping:
                skipped_mappings += 1
                continue
            
            # Trouver la meilleure correspondance MPS
            mps_cat_id, mps_cat_name = find_best_mps_match(cj_name, cj_first, cj_second)
            
            if not mps_cat_id:
                continue
            
            # Créer le mapping
            mapping = CategoryMapping(
                provider_id=provider.id,
                external_category_id=cj_id,
                external_category_name=cj_name,
                external_category_path=cj_path,
                mps_category_id=mps_cat_id,
                auto_import=True,
                apply_markup=1.3,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(mapping)
            created_mappings += 1
            
            # Statistiques
            if mps_cat_name not in mapping_stats:
                mapping_stats[mps_cat_name] = 0
            mapping_stats[mps_cat_name] += 1
            
            if created_mappings <= 20:  # Afficher les 20 premiers
                print(f"  ✓ {cj_name:40} → {mps_cat_name}")
        
        db.session.commit()
        
        # 6. Résumé
        print("\n" + "="*80)
        print("RÉSUMÉ DE LA SYNCHRONISATION")
        print("="*80)
        print(f"\n📁 Catégories CJ:")
        print(f"  - Total synchronisées: {synced_categories}")
        print(f"  - Nouvelles créées: {created_categories}")
        print(f"  - Mises à jour: {updated_categories}")
        
        print(f"\n🔗 Mappings CJ → MPS:")
        print(f"  - Nouveaux mappings: {created_mappings}")
        print(f"  - Mappings existants: {skipped_mappings}")
        print(f"  - Total mappings: {created_mappings + skipped_mappings}")
        
        print("\n📊 Répartition par catégorie MPS:")
        print("-" * 80)
        for cat_name, count in sorted(mapping_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat_name:40} : {count:4} catégories CJ")
        
        print("\n✅ Synchronisation terminée avec succès!")
        print("\n💡 Prochaines étapes:")
        print("   1. Vérifier les catégories CJ dans: http://multiproshop.local/admin/cj/categories")
        print("   2. Vérifier les mappings dans l'admin")
        print("   3. Lancer la synchronisation des produits")
        print("   4. Les produits CJ seront automatiquement dans les catégories françaises\n")
        
        return True

if __name__ == '__main__':
    try:
        success = sync_cj_categories_with_mappings()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
