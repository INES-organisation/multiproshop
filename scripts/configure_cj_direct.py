"""
Script pour configurer le provider CJ Dropshipping directement dans la base de données
"""
import sqlite3
import os

def configure_cj_dropshipping():
    """Configurer CJ Dropshipping avec les identifiants"""
    
    # Chemin vers la base de données
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')
    
    if not os.path.exists(db_path):
        print(f"Erreur: Base de données non trouvée à {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier si le provider existe déjà
    cursor.execute("SELECT id, name FROM api_provider WHERE slug = 'cj-dropshipping'")
    existing = cursor.fetchone()
    
    if existing:
        provider_id = existing[0]
        print(f"Provider CJ Dropshipping trouvé (ID: {provider_id})")
        print("Mise à jour des identifiants...")
        
        # Mettre à jour les identifiants
        cursor.execute("""
            UPDATE api_provider 
            SET api_key = ?,
                api_secret = ?,
                api_endpoint = ?,
                api_version = ?,
                auth_type = ?,
                is_active = 1,
                updated_at = datetime('now')
            WHERE slug = 'cj-dropshipping'
        """, (
            'CJ3088897',
            'd0b2a7aa79024a149fd37128ccef9603',
            'https://developers.cjdropshipping.com/api2.0/v1',
            'v1',
            'signature'
        ))
        
    else:
        print("Création du provider CJ Dropshipping...")
        
        # Créer le provider
        cursor.execute("""
            INSERT INTO api_provider (
                name, slug, description, provider_type,
                api_endpoint, api_version, auth_type,
                api_key, api_secret,
                is_active, is_connected,
                requests_today, total_products_imported, total_orders_placed, total_revenue,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            'CJ Dropshipping',
            'cj-dropshipping',
            'Plateforme de dropshipping avec des millions de produits',
            'dropshipping',
            'https://developers.cjdropshipping.com/api2.0/v1',
            'v1',
            'signature',
            'CJ3088897',
            'd0b2a7aa79024a149fd37128ccef9603',
            1,  # is_active
            0,  # is_connected
            0,  # requests_today
            0,  # total_products_imported
            0,  # total_orders_placed
            0.0  # total_revenue
        ))
        
        provider_id = cursor.lastrowid
    
    conn.commit()
    
    # Vérifier la configuration
    cursor.execute("""
        SELECT id, name, api_key, api_secret, api_endpoint, is_active 
        FROM api_provider 
        WHERE slug = 'cj-dropshipping'
    """)
    provider = cursor.fetchone()
    
    conn.close()
    
    if provider:
        print(f"\n✓ Provider configuré avec succès!")
        print(f"  - ID: {provider[0]}")
        print(f"  - Nom: {provider[1]}")
        print(f"  - Email: {provider[2]}")
        print(f"  - API Key: {provider[3][:10]}...")
        print(f"  - Endpoint: {provider[4]}")
        print(f"  - Actif: {'Oui' if provider[5] else 'Non'}")
        print(f"\nVous pouvez maintenant tester la connexion depuis l'interface admin.")
        print(f"URL: http://localhost:5000/admin/api/providers")
    else:
        print("Erreur lors de la configuration")

if __name__ == '__main__':
    configure_cj_dropshipping()
