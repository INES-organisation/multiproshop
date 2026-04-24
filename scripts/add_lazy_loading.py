"""
Script pour ajouter loading="lazy" à toutes les images
"""
import os
import re
from pathlib import Path

def add_lazy_loading_to_file(file_path):
    """Ajouter loading="lazy" aux balises img qui ne l'ont pas"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern pour trouver les <img> sans loading="lazy"
        # Cherche <img qui n'a pas déjà loading=
        pattern = r'<img\s+(?![^>]*loading=)([^>]*)>'
        
        def add_lazy(match):
            attrs = match.group(1).strip()
            # Ajouter loading="lazy" après src si présent, sinon au début
            if 'src=' in attrs:
                return f'<img {attrs} loading="lazy">'
            else:
                return f'<img loading="lazy" {attrs}>'
        
        content = re.sub(pattern, add_lazy, content, flags=re.IGNORECASE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"❌ Erreur {file_path}: {e}")
        return False

def process_templates():
    """Traiter tous les templates HTML"""
    templates_dir = Path('templates')
    modified_count = 0
    
    print("="*70)
    print("🖼️  AJOUT LAZY LOADING AUX IMAGES")
    print("="*70)
    print()
    
    for html_file in templates_dir.rglob('*.html'):
        if add_lazy_loading_to_file(html_file):
            print(f"✅ {html_file.relative_to(templates_dir)}")
            modified_count += 1
        else:
            print(f"⏭️  {html_file.relative_to(templates_dir)} (déjà optimisé)")
    
    print()
    print("="*70)
    print(f"📊 RÉSUMÉ")
    print("="*70)
    print(f"✅ Fichiers modifiés: {modified_count}")
    print()
    print("🎉 Lazy loading ajouté !")
    print("="*70)

if __name__ == '__main__':
    process_templates()
