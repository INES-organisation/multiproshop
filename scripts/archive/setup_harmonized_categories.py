"""
Configuration finale des 17 catégories harmonisées
Fusion intelligente entre sidebar et BD
"""
import sqlite3
import os

db_path = "instance/boutique.db"

if not os.path.exists(db_path):
    print(f"❌ {db_path} n'existe pas !")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Supprimer toutes les catégories existantes
cursor.execute("DELETE FROM category")
conn.commit()
print("🗑️  Anciennes catégories supprimées\n")

# 17 CATÉGORIES HARMONISÉES - Fusion optimale des deux listes
categories = [
    (1, 'Électronique', 'TV, Audio, Vidéo, Home cinéma, Appareils photo, Casques audio, Jeux vidéo, Enceintes'),
    (2, 'Informatique', 'Ordinateurs, PC portables, Tablettes, Moniteurs, Réseaux, Composants, Stockage, PC Gamer'),
    (3, 'Téléphones & Accessoires', 'Smartphones iOS, Android, Coques, Casques, Câbles de charge, Cartes mémoire'),
    (4, 'Vêtements & Mode', 'Mode Homme, Femme, Enfant, Chaussures, Accessoires vestimentaires'),
    (5, 'Maison & Jardin', 'Meubles, Décoration, Électroménager, Cuisine, Jardin, Plantes'),
    (6, 'Santé & Beauté', 'Soins, Bien-être, Cosmétiques, Parfums, Produits de beauté, Hygiène'),
    (7, 'Bijoux & Montres', 'Bijoux, Montres, Joaillerie, Accessoires de luxe'),
    (8, 'Bébés & Puériculture', 'Articles pour bébés, Poussettes, Vêtements bébé, Jouets premier âge, Maternité'),
    (9, 'Sports & Loisirs', 'Équipements sportifs, Fitness, Camping, Randonnée, Vélo, Sports nautiques'),
    (10, 'Livres & Papeterie', 'Livres, Romans, BD, Fournitures de bureau, Papeterie, Carterie'),
    (11, 'Jeux & Jouets', 'Jeux vidéo, Consoles, Jouets enfants, Jeux de société, Figurines, Loisirs créatifs'),
    (12, 'Auto & Moto', 'Pièces automobiles, Accessoires auto, Moto, Équipements, Entretien véhicules'),
    (13, 'Bricolage & Outillage', 'Outils, Outillage électroportatif, Quincaillerie, Matériaux, Rénovation'),
    (14, 'Alimentation & Boissons', 'Épicerie, Produits frais, Boissons, Vins, Produits du terroir, Gourmandises'),
    (15, 'Animalerie', 'Nourriture animaux, Accessoires chiens, chats, Aquariophilie, Oiseaux, Rongeurs'),
    (16, 'Culture & Divertissement', 'Musique, Films, Séries, Instruments de musique, Billetterie spectacles'),
    (17, 'Services & Cartes Cadeaux', 'Cartes cadeaux, Services, Abonnements, Bons plans, Offres spéciales')
]

print("✅ AJOUT DES 17 CATÉGORIES HARMONISÉES :\n")
print("="*70)

for cat_id, name, description in categories:
    cursor.execute(
        "INSERT INTO category (id, name, description) VALUES (?, ?, ?)",
        (cat_id, name, description)
    )
    print(f"   {cat_id:2d}. {name:<30} | {description[:40]}...")

conn.commit()

# Vérification finale
cursor.execute("SELECT COUNT(*) FROM category")
final_count = cursor.fetchone()[0]

print("="*70)
print(f"\n✅ {final_count} catégories harmonisées créées avec succès !")
print("\n📋 CATÉGORIES FINALES :")

cursor.execute("SELECT id, name FROM category ORDER BY id")
for row in cursor.fetchall():
    print(f"   {row[0]:2d}. {row[1]}")

conn.close()

print("\n" + "="*70)
print("🎯 PROCHAINES ÉTAPES :")
print("   1. Redémarrer le serveur Flask")
print("   2. Mettre à jour la sidebar pour refléter ces 17 catégories")
print("   3. Vérifier l'affichage dans l'admin")
print("="*70)
