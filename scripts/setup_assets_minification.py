"""
Script pour configurer la minification des assets CSS et JS
Utilise flask-assets pour combiner et minifier automatiquement
"""
import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_dependencies():
    """Vérifier si les dépendances sont installées"""
    try:
        import flask_assets
        import cssmin
        import jsmin
        return True
    except ImportError as e:
        print("\n" + "="*70)
        print("DÉPENDANCES MANQUANTES")
        print("="*70 + "\n")
        print("❌ Certaines dépendances ne sont pas installées")
        print("\n📦 Installez-les avec:")
        print("   pip install flask-assets cssmin jsmin")
        print("\nOu ajoutez dans requirements.txt:")
        print("   flask-assets==2.1.0")
        print("   cssmin==0.2.0")
        print("   jsmin==3.0.1")
        return False

def create_assets_config():
    """Créer le fichier de configuration des assets"""
    
    assets_content = '''"""
Configuration des assets pour MultiProShop
Minification et bundling automatique des CSS et JS
"""
from flask_assets import Bundle, Environment

def init_assets(app):
    """Initialiser les assets avec minification"""
    assets = Environment(app)
    assets.url = app.static_url_path
    assets.directory = app.static_folder
    
    # Bundle CSS
    css = Bundle(
        'css/styles.css',
        'css/layout_modern.css',
        filters='cssmin',
        output='gen/packed.css'
    )
    
    # Bundle JS
    js = Bundle(
        'js/cart.js',
        filters='jsmin',
        output='gen/packed.js'
    )
    
    # Enregistrer les bundles
    assets.register('css_all', css)
    assets.register('js_all', js)
    
    print("✅ Assets configurés avec minification")
    
    return assets
'''
    
    assets_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'assets.py'
    )
    
    # Vérifier si le fichier existe déjà
    if os.path.exists(assets_file):
        print(f"ℹ️  {assets_file} existe déjà")
        
        with open(assets_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'cssmin' in content and 'jsmin' in content:
            print("✅ La minification est déjà configurée")
            return True
        else:
            print("⚠️  Le fichier existe mais sans minification")
            backup = assets_file + '.backup'
            os.rename(assets_file, backup)
            print(f"📁 Backup créé: {backup}")
    
    # Créer le nouveau fichier
    with open(assets_file, 'w', encoding='utf-8') as f:
        f.write(assets_content)
    
    print(f"✅ {assets_file} créé avec minification")
    return True

def update_base_template():
    """Instructions pour mettre à jour le template de base"""
    print("\n" + "="*70)
    print("MISE À JOUR DU TEMPLATE BASE.HTML")
    print("="*70 + "\n")
    print("📝 Remplacez dans templates/base.html:")
    print("\nAVANT:")
    print("    <link rel='stylesheet' href=\"{{ url_for('static', filename='css/styles.css') }}\">")
    print("    <link rel='stylesheet' href=\"{{ url_for('static', filename='css/layout_modern.css') }}\">")
    print("\nAPRÈS:")
    print("    {% assets 'css_all' %}")
    print("        <link rel='stylesheet' href='{{ ASSET_URL }}'>")
    print("    {% endassets %}")
    print("\nPour le JS:")
    print("AVANT:")
    print("    <script src=\"{{ url_for('static', filename='js/cart.js') }}\"></script>")
    print("\nAPRÈS:")
    print("    {% assets 'js_all' %}")
    print("        <script src='{{ ASSET_URL }}'></script>")
    print("    {% endassets %}")

def main():
    print("\n" + "="*70)
    print("CONFIGURATION DE LA MINIFICATION DES ASSETS")
    print("="*70 + "\n")
    
    # Vérifier les dépendances
    if not check_dependencies():
        return
    
    # Créer la configuration
    if create_assets_config():
        print("\n✅ Configuration créée avec succès")
    
    # Instructions pour le template
    update_base_template()
    
    print("\n" + "="*70)
    print("✅ CONFIGURATION TERMINÉE")
    print("="*70)
    print("\n📊 Gains attendus:")
    print("   - Taille CSS: 40-50% de réduction")
    print("   - Taille JS: 30-40% de réduction")
    print("   - Temps de chargement: 20-30% plus rapide")
    print("\n💡 Les fichiers minifiés seront créés dans static/gen/\n")

if __name__ == '__main__':
    main()
