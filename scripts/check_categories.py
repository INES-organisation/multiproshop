import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.api_provider import CategoryMapping
from models.category import Category

with app.app_context():
    print("\n" + "="*80)
    print("VERIFICATION DES CATEGORIES")
    print("="*80 + "\n")
    
    # Categories MPS
    print("Categories MPS (affichees sur le site):")
    mps_cats = Category.query.limit(15).all()
    for c in mps_cats:
        print(f"  {c.id}: {c.name}")
    
    print("\n" + "-"*80 + "\n")
    
    # Mappings CJ
    print("Mappings CJ -> MPS:")
    mappings = CategoryMapping.query.filter_by(provider_id=1).limit(15).all()
    for m in mappings:
        mps_name = m.mps_category.name if m.mps_category else "Aucune"
        print(f"  CJ: {m.external_category_name:40} -> MPS: {mps_name}")
    
    print("\n" + "="*80 + "\n")
