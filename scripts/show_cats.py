import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.category import Category

with app.app_context():
    cats = Category.query.all()
    print(f"\nTotal categories MPS: {len(cats)}")
    print("\nPremieres 20 categories:")
    for c in cats[:20]:
        print(f"  {c.id}: {c.name}")
