import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.api_provider import CategoryMapping

with app.app_context():
    mappings = CategoryMapping.query.filter_by(provider_id=1).all()
    
    english_words = ['Woman', 'Man', 'Shoes', 'Bags', 'Tops', 'Bottoms', 'Hats', 'Caps', 
                     'Scarves', 'Gloves', 'Socks', 'Watches', 'Jewelry', 'Baby', 'Kids']
    
    still_english = []
    
    for m in mappings:
        name = m.external_category_name
        for word in english_words:
            if word in name:
                still_english.append(name)
                break
    
    print(f"\nTotal mappings CJ: {len(mappings)}")
    print(f"Mappings encore en anglais: {len(still_english)}")
    
    if still_english:
        print("\nExemples de categories encore en anglais:")
        for name in still_english[:20]:
            print(f"  - {name}")
    else:
        print("\n✓ Toutes les categories principales sont traduites!")
    
    print("\nExemples de categories traduites:")
    for m in mappings[:15]:
        print(f"  - {m.external_category_name}")
