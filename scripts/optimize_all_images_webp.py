"""
Script avancé pour optimiser TOUTES les images en WebP
"""
import os
import sys
from pathlib import Path
from PIL import Image

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

def optimize_image_to_webp(image_path, quality=85):
    """
    Convertir une image en WebP et optimiser l'originale
    
    Args:
        image_path: Chemin de l'image
        quality: Qualité WebP (1-100)
    
    Returns:
        tuple: (success, original_size, webp_size, savings_percent)
    """
    try:
        # Ouvrir l'image
        img = Image.open(image_path)
        
        # Taille originale
        original_size = os.path.getsize(image_path)
        
        # Créer le chemin WebP
        webp_path = image_path.rsplit('.', 1)[0] + '.webp'
        
        # Convertir en WebP
        img.save(webp_path, 'WEBP', quality=quality, method=6)
        
        # Taille WebP
        webp_size = os.path.getsize(webp_path)
        
        # Économies
        savings = original_size - webp_size
        savings_percent = (savings / original_size * 100) if original_size > 0 else 0
        
        # Optimiser l'originale aussi
        if image_path.lower().endswith(('.jpg', '.jpeg')):
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
        elif image_path.lower().endswith('.png'):
            img.save(image_path, 'PNG', optimize=True)
        
        return True, original_size, webp_size, savings_percent
        
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        return False, 0, 0, 0


def find_all_images(directory):
    """Trouver toutes les images dans un répertoire"""
    extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    images = []
    
    for root, dirs, files in os.walk(directory):
        # Ignorer certains dossiers
        dirs[:] = [d for d in dirs if d not in ['venv', 'node_modules', '__pycache__', '.git']]
        
        for file in files:
            if file.lower().endswith(extensions):
                images.append(os.path.join(root, file))
    
    return images


def optimize_all_images():
    """Optimiser toutes les images du projet"""
    print("="*70)
    print("🖼️  OPTIMISATION COMPLÈTE DES IMAGES EN WEBP")
    print("="*70)
    print()
    
    # Répertoires à scanner
    directories = [
        'static/images',
        'static/img',
        'static/assets',
        'templates',
    ]
    
    all_images = []
    
    print("📁 Recherche des images...")
    for directory in directories:
        if os.path.exists(directory):
            images = find_all_images(directory)
            all_images.extend(images)
            print(f"  {directory:30} : {len(images)} images")
    
    print()
    print(f"📊 Total : {len(all_images)} images trouvées")
    print()
    
    if not all_images:
        print("⚠️  Aucune image à optimiser")
        return
    
    # Optimiser chaque image
    print("🔄 Optimisation en cours...")
    print("-"*70)
    
    total_original = 0
    total_webp = 0
    success_count = 0
    error_count = 0
    
    for i, image_path in enumerate(all_images, 1):
        # Ignorer les images déjà en WebP
        if image_path.lower().endswith('.webp'):
            continue
        
        relative_path = os.path.relpath(image_path)
        print(f"  [{i}/{len(all_images)}] {relative_path:50}", end=" ")
        
        success, orig_size, webp_size, savings = optimize_image_to_webp(image_path)
        
        if success:
            total_original += orig_size
            total_webp += webp_size
            success_count += 1
            
            # Afficher les économies
            if savings > 0:
                print(f"✅ -{savings:.1f}%")
            else:
                print(f"✅ +{abs(savings):.1f}%")
        else:
            error_count += 1
            print()
    
    print()
    print("="*70)
    print("📊 RÉSUMÉ DE L'OPTIMISATION")
    print("="*70)
    
    if total_original > 0:
        total_savings = total_original - total_webp
        total_savings_percent = (total_savings / total_original * 100)
        
        print(f"  Images traitées    : {success_count}")
        print(f"  Erreurs            : {error_count}")
        print(f"  Taille originale   : {total_original / 1024:.2f} KB")
        print(f"  Taille WebP        : {total_webp / 1024:.2f} KB")
        print(f"  Économies          : {total_savings / 1024:.2f} KB ({total_savings_percent:.1f}%)")
        print()
        
        if total_savings_percent > 0:
            print(f"🎉 Vous avez économisé {total_savings_percent:.1f}% d'espace !")
        else:
            print(f"ℹ️  Les images WebP sont légèrement plus grandes dans ce cas")
    
    print()
    print("="*70)
    print("✅ Optimisation terminée !")
    print("="*70)
    print()
    print("📝 PROCHAINES ÉTAPES :")
    print("  1. Utiliser les images .webp dans les templates")
    print("  2. Ajouter un fallback pour les navigateurs anciens")
    print("  3. Profiter de -50% de taille d'images !")
    print()
    print("💡 EXEMPLE D'UTILISATION :")
    print('  <picture>')
    print('    <source srcset="image.webp" type="image/webp">')
    print('    <img src="image.jpg" alt="Description">')
    print('  </picture>')
    print()


if __name__ == '__main__':
    optimize_all_images()
