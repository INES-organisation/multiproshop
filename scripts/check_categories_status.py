"""
Vérifier l'état des catégories dans la base de données
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("ÉTAT DES CATÉGORIES")
    print("="*70 + "\n")
    
    # Compter les catégories
    total = Category.query.count()
    cj_categories = Category.query.filter(Category.cj_category_id.isnot(None)).count()
    non_cj = total - cj_categories
    
    print(f"Total catégories: {total}")
    print(f"Catégories CJ: {cj_categories}")
    print(f"Catégories non-CJ: {non_cj}")
    
    # Catégories par niveau
    print("\nPar niveau:")
    for level in [1, 2, 3]:
        count = Category.query.filter_by(level=level).filter(Category.cj_category_id.isnot(None)).count()
        print(f"  Niveau {level}: {count} catégories")
    
    # Exemples de catégories CJ
    print("\nExemples de catégories CJ:")
    examples = Category.query.filter(Category.cj_category_id.isnot(None)).limit(5).all()
    for cat in examples:
        print(f"  - {cat.name} (niveau {cat.level}, slug: {cat.slug})")
    
    # Vérifier les slugs dupliqués
    print("\nVérification slugs dupliqués:")
    from sqlalchemy import func
    duplicates = db.session.query(
        Category.slug, 
        func.count(Category.id)
    ).group_by(Category.slug).having(func.count(Category.id) > 1).all()
    
    if duplicates:
        print(f"  ⚠️  {len(duplicates)} slugs dupliqués trouvés:")
        for slug, count in duplicates[:5]:
            print(f"    - {slug}: {count} fois")
    else:
        print("  ✓ Aucun slug dupliqué")
    
    print("\n" + "="*70 + "\n")
