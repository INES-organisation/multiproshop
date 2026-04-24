"""
Script pour convertir toutes les images JPEG/PNG en WebP
Optimise la taille des images de 50-70%
"""
import os
from pathlib import Path
from PIL import Image

def convert_to_webp(input_path, quality=85):
    """
    Convertit une image en WebP
    
    Args:
        input_path: Chemin de l'image source
        quality: Qualité de compression (0-100)
    
    Returns:
        str: Chemin de l'image WebP créée
    """
    try:
        # Ouvrir l'image
        img = Image.open(input_path)
        
        # Convertir en RGB si nécessaire (pour les PNG avec transparence)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Créer le chemin de sortie
        output_path = str(input_path).rsplit('.', 1)[0] + '.webp'
        
        # Sauvegarder en WebP
        img.save(output_path, 'webp', quality=quality, method=6)
        
        # Calculer la réduction de taille
        original_size = os.path.getsize(input_path)
        webp_size = os.path.getsize(output_path)
        reduction = ((original_size - webp_size) / original_size) * 100
        
        return output_path, reduction
    
    except Exception as e:
        print(f"❌ Erreur avec {input_path}: {e}")
        return None, 0

def main():
    print("\n" + "="*70)
    print("CONVERSION DES IMAGES EN WEBP")
    print("="*70 + "\n")
    
    # Vérifier si PIL est installé
    try:
        from PIL import Image
    except ImportError:
        print("❌ Pillow n'est pas installé")
        print("📦 Installez-le avec: pip install Pillow")
        return
    
    static_dir = Path(__file__).parent.parent / 'static'
    
    if not static_dir.exists():
        print("❌ Dossier static introuvable")
        return
    
    # Extensions à convertir
    extensions = ['.jpg', '.jpeg', '.png']
    
    # Trouver toutes les images
    images = []
    for ext in extensions:
        images.extend(static_dir.rglob(f'*{ext}'))
    
    total_images = len(images)
    converted = 0
    total_reduction = 0
    
    print(f"📁 {total_images} images trouvées\n")
    
    if total_images == 0:
        print("ℹ️  Aucune image à convertir")
        return
    
    for img_path in images:
        relative_path = img_path.relative_to(static_dir)
        
        # Vérifier si le WebP existe déjà
        webp_path = str(img_path).rsplit('.', 1)[0] + '.webp'
        if os.path.exists(webp_path):
            print(f"⏭️  {relative_path} (WebP existe déjà)")
            continue
        
        # Convertir
        result, reduction = convert_to_webp(img_path)
        
        if result:
            print(f"✅ {relative_path} → {reduction:.1f}% de réduction")
            converted += 1
            total_reduction += reduction
    
    print("\n" + "="*70)
    print(f"✅ TERMINÉ : {converted} images converties")
    if converted > 0:
        avg_reduction = total_reduction / converted
        print(f"📊 Réduction moyenne : {avg_reduction:.1f}%")
    print("="*70)
    print("\n💡 Prochaines étapes:")
    print("   1. Mettre à jour les templates pour utiliser WebP")
    print("   2. Utiliser <picture> avec fallback pour compatibilité")
    print("   3. Exemple:")
    print("      <picture>")
    print("        <source srcset='image.webp' type='image/webp'>")
    print("        <img src='image.jpg' alt='...' loading='lazy'>")
    print("      </picture>\n")

if __name__ == '__main__':
    main()
