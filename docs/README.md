# Boutique E-Commerce Multi-Produits

## Description
Une plateforme e-commerce complète permettant la gestion et la vente de produits dans différentes catégories.

## Fonctionnalités
- Inscription et authentification des utilisateurs
- Catalogue de produits multi-catégories
- Panier d'achat
- Processus de paiement
- Gestion des commandes

## Installation

1. Cloner le repository
2. Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

4. Configurer la base de données
```bash
flask db upgrade
```

5. Lancer l'application
```bash
flask run
```
