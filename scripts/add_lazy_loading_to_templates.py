"""
Script pour ajouter automatiquement loading="lazy" et decoding="async" 
à toutes les balises <img> dans les templates
"""
import os
import re
from pathlib import Path

def add_lazy_loading_to_img(content):
    """Ajoute loading="lazy" et decoding="async" aux balises img qui ne les ont pas"""
    
    # Pattern pour trouver les balises img
    pattern = r'<img\s+([^>]*?)>'
    
    def process_img(match):
        attrs = match.group(1)
        
        # Vérifier si les attributs sont déjà présents
        has_loading = 'loading=' in attrs
        has_decoding = 'decoding=' in attrs
        
        # Ajouter les attributs manquants
        if not has_loading:
            attrs += ' loading="lazy"'
        if not has_decoding:
            attrs += ' decoding="async"'
        
        return f'<img {attrs}>'
    
    return re.sub(pattern, process_img, content)

def process_template_file(file_path):
    """Traite un fichier template"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier s'il y a des images
        if '<img' not in content:
            return False
        
        # Ajouter lazy loading
        new_content = add_lazy_loading_to_img(content)
        
        # Vérifier si des changements ont été faits
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
    except Exception as e:
        print(f"❌ Erreur avec {file_path}: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("AJOUT DU LAZY LOADING SUR TOUTES LES IMAGES")
    print("="*70 + "\n")
    
    templates_dir = Path(__file__).parent.parent / 'templates'
    
    if not templates_dir.exists():
        print("❌ Dossier templates introuvable")
        return
    
    # Parcourir tous les fichiers HTML
    html_files = list(templates_dir.rglob('*.html'))
    total_files = len(html_files)
    modified_files = 0
    
    print(f"📁 {total_files} fichiers HTML trouvés\n")
    
    for file_path in html_files:
        relative_path = file_path.relative_to(templates_dir)
        
        if process_template_file(file_path):
            print(f"✅ {relative_path}")
            modified_files += 1
    
    print("\n" + "="*70)
    print(f"✅ TERMINÉ : {modified_files}/{total_files} fichiers modifiés")
    print("="*70)
    print("\n📊 Gains attendus:")
    print("   - Chargement initial: 30-40% plus rapide")
    print("   - Images chargées à la demande")
    print("   - Meilleure expérience utilisateur\n")

if __name__ == '__main__':
    main()
