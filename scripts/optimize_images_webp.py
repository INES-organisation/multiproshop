"""
Script pour optimiser et convertir les images en WebP
"""
from PIL import Image
import os
from pathlib import Path

def optimize_image(image_path):
    """Optimiser une image et créer version WebP"""
    try:
        img = Image.open(image_path)
        
        # Obtenir les dimensions
        width, height = img.size
        
        # Créer version WebP
        webp_path = image_path.with_suffix('.webp')
        
        # Convertir en RGB si nécessaire (pour PNG avec transparence)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Garder la transparence pour WebP
            img.save(webp_path, 'WebP', quality=85, method=6)
        else:
            img.save(webp_path, 'WebP', quality=85, method=6)
        
        # Optimiser l'image originale aussi
        if image_path.suffix.lower() in ['.jpg', '.jpeg']:
            img.save(image_path, 'JPEG', quality=85, optimize=True)
        elif image_path.suffix.lower() == '.png':
            img.save(image_path, 'PNG', optimize=True)
        
        # Calculer la réduction
        original_size = os.path.getsize(image_path)
        webp_size = os.path.getsize(webp_path)
        reduction = ((original_size - webp_size) / original_size) * 100
        
        return True, original_size, webp_size, reduction
    except Exception as e:
        return False, 0, 0, 0

def process_images():
    """Traiter toutes les images du dossier static"""
    static_dir = Path('static')
    
    print("="*70)
    print("🖼️  OPTIMISATION IMAGES EN WEBP")
    print("="*70)
    print()
    
    total_original = 0
    total_webp = 0
    count_success = 0
    count_error = 0
    
    # Extensions à traiter
    extensions = ['.jpg', '.jpeg', '.png']
    
    for ext in extensions:
        for img_path in static_dir.rglob(f'*{ext}'):
            # Ignorer les fichiers déjà traités
            if img_path.stem.endswith('_optimized'):
                continue
            
            success, orig_size, webp_size, reduction = optimize_image(img_path)
            
            if success:
                print(f"✅ {img_path.name}")
                print(f"   Original: {orig_size/1024:.1f} KB → WebP: {webp_size/1024:.1f} KB ({reduction:.1f}% réduction)")
                total_original += orig_size
                total_webp += webp_size
                count_success += 1
            else:
                print(f"❌ Erreur: {img_path.name}")
                count_error += 1
    
    print()
    print("="*70)
    print("📊 RÉSUMÉ")
    print("="*70)
    print(f"✅ Images optimisées: {count_success}")
    print(f"❌ Erreurs: {count_error}")
    if total_original > 0:
        total_reduction = ((total_original - total_webp) / total_original) * 100
        print(f"📦 Taille originale: {total_original/1024/1024:.2f} MB")
        print(f"📦 Taille WebP: {total_webp/1024/1024:.2f} MB")
        print(f"💾 Économie: {(total_original - total_webp)/1024/1024:.2f} MB ({total_reduction:.1f}%)")
    print()
    print("🎉 Optimisation terminée !")
    print("="*70)

if __name__ == '__main__':
    process_images()
