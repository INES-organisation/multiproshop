"""
Script de création manuelle des mappings CJ vers catégories MPS françaises
Utilise une liste prédéfinie des catégories CJ les plus courantes
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models.category import Category
from models.api_provider import ApiProvider, CategoryMapping
from datetime import datetime

def get_french_category_id(category_name):
    """Récupérer l'ID d'une catégorie française par son nom"""
    category = Category.query.filter_by(name=category_name).first()
    return category.id if category else None

def create_manual_mappings():
    """Créer les mappings manuels des catégories CJ vers MPS"""
    
    with app.app_context():
        # Récupérer le provider CJ
        provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
        
        if not provider:
            print("❌ Provider CJ Dropshipping non trouvé")
            return False
        
        print("\n" + "="*80)
        print("CRÉATION MANUELLE DES MAPPINGS CJ -> MPS FRANÇAIS")
        print("="*80)
        
        # Définition des mappings manuels
        # Format: (cj_category_id, cj_name, cj_path, mps_category_name)
        manual_mappings = [
            # Électronique & High-Tech
            ("D9E66BF8-4E81-4CAB-A425-AEDEC5FBFBF2", "Consumer Electronics", "Consumer Electronics", "Électronique & High-Tech"),
            ("1126E280-CB7D-418A-90AB-7118E2D97CCC", "Computer & Office", "Computer & Office", "Informatique"),
            ("E9FDC79A-8365-4CA6-AC23-64D971F08B8B", "Phones & Accessories", "Phones & Accessories", "Téléphonie & Tablettes"),
            
            # Mode & Vêtements
            ("2FE8A083-5E7B-4179-896D-561EA116F730", "Women's Clothing", "Women's Clothing", "Mode & Vêtements"),
            ("B8302697-CF47-4211-9BD0-DFE8995AEB30", "Men's Clothing", "Men's Clothing", "Mode & Vêtements"),
            ("2415A90C-5D7B-4CC7-BA8C-C0949F9FF5D8", "Bags & Shoes", "Bags & Shoes", "Mode & Vêtements"),
            ("2837816E-2FEA-4455-845C-6F40C6D70D1E", "Jewelry & Watches", "Jewelry & Watches", "Mode & Vêtements"),
            
            # Maison & Jardin
            ("52FC6CA5-669B-4D0B-B1AC-415675931399", "Home, Garden & Furniture", "Home, Garden & Furniture", "Maison & Jardin"),
            ("6A5D2EB4-13BD-462E-A627-78CFED11B2A2", "Home Improvement", "Home Improvement", "Maison & Jardin"),
            
            # Santé & Beauté
            ("2C7D4A0B-1AB2-41EC-8F9E-13DC31B1C902", "Health, Beauty & Hair", "Health, Beauty & Hair", "Santé & Beauté"),
            
            # Sports & Loisirs
            ("4B397425-26C1-4D0E-B6D2-96B0B03689DB", "Sports & Outdoors", "Sports & Outdoors", "Sports & Loisirs"),
            
            # Bébés & Puériculture / Jeux & Jouets
            ("A50A92FA-BCB3-4716-9BD9-BEC629BEE735", "Toys, Kids & Babies", "Toys, Kids & Babies", "Bébés & Puériculture"),
            
            # Auto & Moto
            ("A2F799BE-FB59-428E-A953-296AA2673FCF", "Automobiles & Motorcycles", "Automobiles & Motorcycles", "Auto & Moto"),
            
            # Animalerie
            ("2409110611570657700", "Pet Supplies", "Pet Supplies", "Animalerie"),
        ]
        
        print(f"\n📋 {len(manual_mappings)} mappings à créer\n")
        
        created = 0
        skipped = 0
        errors = 0
        
        for cj_id, cj_name, cj_path, mps_name in manual_mappings:
            # Vérifier si le mapping existe déjà
            existing = CategoryMapping.query.filter_by(
                provider_id=provider.id,
                external_category_id=cj_id
            ).first()
            
            if existing:
                print(f"⏭️  {cj_name:40} -> Déjà mappé")
                skipped += 1
                continue
            
            # Récupérer la catégorie MPS
            mps_cat_id = get_french_category_id(mps_name)
            
            if not mps_cat_id:
                print(f"❌ {cj_name:40} -> Catégorie '{mps_name}' non trouvée")
                errors += 1
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
            print(f"✅ {cj_name:40} -> {mps_name}")
            created += 1
        
        # Sauvegarder
        db.session.commit()
        
        print("\n" + "="*80)
        print("RÉSUMÉ")
        print("="*80)
        print(f"✅ Mappings créés: {created}")
        print(f"⏭️  Mappings existants (ignorés): {skipped}")
        print(f"❌ Erreurs: {errors}")
        print(f"\n📊 Total mappings actifs: {created + skipped}")
        
        if created > 0:
            print("\n✅ Mappings créés avec succès!")
            print("\n💡 Prochaines étapes:")
            print("   1. Les produits CJ seront automatiquement assignés à ces catégories")
            print("   2. Lancez la synchronisation des produits CJ")
            print("   3. Les produits apparaîtront dans les catégories françaises correspondantes")
        
        return True

if __name__ == '__main__':
    try:
        create_manual_mappings()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
