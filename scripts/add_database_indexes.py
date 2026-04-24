"""
Script pour ajouter des indexes à la base de données
Améliore les performances des requêtes fréquentes
"""
from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

def add_indexes():
    """Ajouter les indexes manquants"""
    with app.app_context():
        print("="*70)
        print("🔧 AJOUT DES INDEXES À LA BASE DE DONNÉES")
        print("="*70)
        print()
        
        indexes = [
            # Table product
            ("idx_product_name", "product", "name"),
            ("idx_product_sku", "product", "sku"),
            ("idx_product_category", "product", "category_id"),
            ("idx_product_is_active", "product", "is_active"),
            ("idx_product_created_at", "product", "created_at"),
            ("idx_product_price", "product", "price"),
            ("idx_product_stock", "product", "stock"),
            
            # Table category
            ("idx_category_slug", "category", "slug"),
            ("idx_category_parent", "category", "parent_id"),
            ("idx_category_level", "category", "level"),
            
            # Table order
            ("idx_order_user", '"order"', "user_id"),
            ("idx_order_status", '"order"', "status"),
            ("idx_order_payment_status", '"order"', "payment_status"),
            ("idx_order_created_at", '"order"', "created_at"),
            ("idx_order_number", '"order"', "order_number"),
            
            # Table user
            ("idx_user_email", "user", "email"),
            ("idx_user_username", "user", "username"),
            ("idx_user_role", "user", "role_id"),
            
            # Table order_item
            ("idx_order_item_order", "order_item", "order_id"),
            ("idx_order_item_product", "order_item", "product_id"),
            
            # Table api_provider
            ("idx_api_provider_slug", "api_provider", "slug"),
            ("idx_api_provider_is_active", "api_provider", "is_active"),
            
            # Table product_source
            ("idx_product_source_product", "product_source", "product_id"),
            ("idx_product_source_provider", "product_source", "provider_id"),
            ("idx_product_source_external_id", "product_source", "external_product_id"),
        ]
        
        created_count = 0
        skipped_count = 0
        
        for index_name, table_name, column_name in indexes:
            try:
                # Vérifier si l'index existe déjà
                check_query = text(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name=:index_name
                """)
                result = db.session.execute(check_query, {"index_name": index_name})
                
                if result.fetchone():
                    print(f"⏭️  Index {index_name} existe déjà")
                    skipped_count += 1
                else:
                    # Créer l'index
                    create_query = text(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table_name}({column_name})
                    """)
                    db.session.execute(create_query)
                    db.session.commit()
                    print(f"✅ Index {index_name} créé sur {table_name}({column_name})")
                    created_count += 1
                    
            except Exception as e:
                print(f"❌ Erreur lors de la création de {index_name}: {e}")
                db.session.rollback()
        
        print()
        print("="*70)
        print("📊 RÉSUMÉ")
        print("="*70)
        print(f"✅ Indexes créés: {created_count}")
        print(f"⏭️  Indexes existants: {skipped_count}")
        print(f"📊 Total: {created_count + skipped_count}")
        print()
        print("🎉 Optimisation terminée !")
        print("="*70)


if __name__ == '__main__':
    add_indexes()
