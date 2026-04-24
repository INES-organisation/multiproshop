# 💰 SYSTÈME DE TARIFICATION CJ DROPSHIPPING
## Analyse Complète des Prix et Marges

---

## 📊 TYPES DE PRIX DANS LE SYSTÈME

### 1. **Prix CJ (API CJ Dropshipping)**

#### A. `sellPrice` - Prix de Vente CJ
- **Source** : API CJ Dropshipping
- **Description** : Prix auquel CJ vend le produit (coût d'achat pour le vendeur)
- **Utilisation** : Prix de base pour calculer le prix de vente final
- **Champ BDD** : `cost_price` (prix de revient)
- **Exemple** : $5.50

#### B. `suggestSellPrice` - Prix Suggéré CJ
- **Source** : API CJ Dropshipping
- **Description** : Prix de vente suggéré par CJ pour le marché
- **Utilisation** : Prix de référence pour le prix barré (compare_price)
- **Champ BDD** : `suggested_price` ET `compare_price`
- **Exemple** : $12.99

### 2. **Prix MultiProShop (Notre Système)**

#### A. `price` - Prix de Vente Affiché
- **Source** : Calculé automatiquement
- **Description** : Prix final affiché au client
- **Calcul** : `sellPrice × (1 + marge)`
- **Champ BDD** : `price`
- **Exemple** : $8.99 (avec marge 63%)

#### B. `compare_price` - Prix Barré
- **Source** : `suggestSellPrice` de CJ
- **Description** : Prix de référence pour montrer la réduction
- **Utilisation** : Affichage "Prix barré" pour effet promo
- **Champ BDD** : `compare_price`
- **Exemple** : $12.99

#### C. `cost_price` - Prix de Revient
- **Source** : `sellPrice` de CJ
- **Description** : Coût réel du produit
- **Utilisation** : Calcul des marges et bénéfices
- **Champ BDD** : `cost_price`
- **Exemple** : $5.50

---

## 🔢 LOGIQUE DE CALCUL DES PRIX

### Formule de Base
```python
# Prix CJ (API)
cj_sell_price = 5.50        # Prix d'achat CJ
cj_suggested_price = 12.99  # Prix suggéré CJ

# Configuration Marge (par catégorie ou global)
markup_percentage = 63      # Marge de 63%

# Calcul Prix de Vente
price = cj_sell_price × (1 + markup_percentage/100)
price = 5.50 × 1.63 = 8.97 ≈ 8.99

# Prix Barré
compare_price = cj_suggested_price = 12.99

# Bénéfice
profit = price - cj_sell_price
profit = 8.99 - 5.50 = 3.49

# Marge Réelle
margin = (profit / price) × 100
margin = (3.49 / 8.99) × 100 = 38.8%
```

### Exemple Concret
```
Produit : "Rabbit Plush Sofa Cushion"

API CJ retourne :
├─ sellPrice: $5.50
├─ suggestSellPrice: $12.99
└─ stock: 100

MultiProShop calcule :
├─ cost_price: $5.50 (prix CJ)
├─ price: $8.99 (prix de vente avec marge 63%)
├─ compare_price: $12.99 (prix suggéré CJ)
├─ profit: $3.49 par vente
└─ discount_display: -31% (par rapport au prix barré)

Client voit :
├─ Prix barré: $12.99
├─ Prix actuel: $8.99
└─ Badge: "PROMO -31%"
```

---

## 🎯 STRATÉGIES DE TARIFICATION

### 1. **Stratégie par Défaut (Recommandée)**
```python
# Configuration globale
DEFAULT_MARKUP = 60  # 60% de marge

price = cj_sell_price × 1.60
compare_price = cj_suggested_price

# Avantages :
✓ Marge confortable
✓ Prix compétitif vs prix suggéré CJ
✓ Effet promo automatique
```

### 2. **Stratégie par Catégorie**
```python
CATEGORY_MARKUPS = {
    'Electronics': 50,      # Marge faible, volume élevé
    'Fashion': 80,          # Marge élevée, valeur perçue
    'Home & Garden': 70,    # Marge moyenne
    'Jewelry': 100,         # Marge très élevée
    'Toys': 60,             # Marge standard
}

price = cj_sell_price × (1 + CATEGORY_MARKUPS[category]/100)
```

### 3. **Stratégie Dynamique (Avancée)**
```python
# Ajustement selon le prix CJ
if cj_sell_price < 5:
    markup = 100  # Marge élevée pour petits prix
elif cj_sell_price < 20:
    markup = 70   # Marge moyenne
else:
    markup = 50   # Marge faible pour prix élevés

price = cj_sell_price × (1 + markup/100)
```

---

## 💾 STRUCTURE BASE DE DONNÉES

### Modèle Product (Actuel)
```python
class Product(db.Model):
    # Prix
    price = db.Column(db.Float)              # Prix de vente affiché
    compare_price = db.Column(db.Float)      # Prix barré (suggéré CJ)
    cost_price = db.Column(db.Float)         # Prix de revient (CJ)
    suggested_price = db.Column(db.Float)    # Prix suggéré CJ (doublon)
    
    # Méthodes
    def get_discount_percentage(self):
        """Calcule % réduction par rapport au prix barré"""
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0
    
    def get_profit(self):
        """Calcule le bénéfice par vente"""
        if self.cost_price:
            return self.price - self.cost_price
        return 0
    
    def get_margin_percentage(self):
        """Calcule la marge en %"""
        profit = self.get_profit()
        if profit > 0 and self.price > 0:
            return (profit / self.price) * 100
        return 0
```

### Modèle ProductVariant (Variantes)
```python
class ProductVariant(db.Model):
    # Prix par variante
    price = db.Column(db.Float)              # Prix de vente variante
    suggested_price = db.Column(db.Float)    # Prix suggéré variante
    cost_price = db.Column(db.Float)         # Prix CJ variante
    
    # Note: Chaque variante peut avoir un prix différent
```

---

## 🔄 SYNCHRONISATION DES PRIX

### Lors de la Synchronisation Produit
```python
def sync_product_from_cj(cj_product_data):
    """Synchronise un produit CJ avec calcul automatique des prix"""
    
    # Prix depuis API CJ
    cj_sell_price = cj_product_data['sellPrice']
    cj_suggested_price = cj_product_data['suggestSellPrice']
    
    # Récupérer la marge pour la catégorie
    category = get_category(cj_product_data['categoryId'])
    markup = get_category_markup(category) or DEFAULT_MARKUP
    
    # Calculer le prix de vente
    selling_price = calculate_selling_price(cj_sell_price, markup)
    
    # Créer/Mettre à jour le produit
    product = Product(
        name=cj_product_data['name'],
        cj_pid=cj_product_data['pid'],
        
        # Prix
        cost_price=cj_sell_price,           # Prix CJ
        price=selling_price,                # Prix calculé
        compare_price=cj_suggested_price,   # Prix suggéré CJ
        suggested_price=cj_suggested_price, # Doublon (à nettoyer)
        
        # Autres champs...
    )
    
    return product

def calculate_selling_price(cost_price, markup_percentage):
    """Calcule le prix de vente avec marge"""
    price = cost_price * (1 + markup_percentage / 100)
    
    # Arrondir à .99 pour effet psychologique
    price = round(price, 2)
    if price > 10:
        price = int(price) + 0.99
    
    return price
```

### Lors de la Synchronisation Variantes
```python
def sync_variant_from_cj(product, cj_variant_data):
    """Synchronise une variante avec ses prix"""
    
    # Prix variante depuis API CJ
    variant_sell_price = cj_variant_data['variantSellPrice']
    variant_suggested_price = cj_variant_data.get('variantSuggestPrice')
    
    # Utiliser la même marge que le produit parent
    markup = calculate_product_markup(product)
    variant_price = calculate_selling_price(variant_sell_price, markup)
    
    variant = ProductVariant(
        product_id=product.id,
        cj_vid=cj_variant_data['vid'],
        
        # Prix
        cost_price=variant_sell_price,
        price=variant_price,
        suggested_price=variant_suggested_price,
        
        # Autres champs...
    )
    
    return variant
```

---

## 📈 AFFICHAGE FRONTEND

### Page Produit
```html
<!-- Prix principal -->
<div class="product-pricing">
    {% if product.compare_price and product.compare_price > product.price %}
        <!-- Prix barré -->
        <span class="price-compare">${{ product.compare_price }}</span>
        
        <!-- Badge réduction -->
        <span class="badge-discount">-{{ product.get_discount_percentage() }}%</span>
    {% endif %}
    
    <!-- Prix actuel -->
    <span class="price-current">${{ product.price }}</span>
    
    <!-- Économies -->
    {% if product.compare_price and product.compare_price > product.price %}
        <span class="savings">
            Économisez ${{ "%.2f"|format(product.compare_price - product.price) }}
        </span>
    {% endif %}
</div>

<!-- Sélecteur de variantes (si applicable) -->
{% if product.has_variants %}
<div class="variant-selector">
    <select id="variant-select" onchange="updatePrice()">
        {% for variant in product.variants %}
        <option value="{{ variant.id }}" 
                data-price="{{ variant.price }}"
                data-compare="{{ variant.suggested_price }}">
            {{ variant.color }} - {{ variant.size }}
        </option>
        {% endfor %}
    </select>
</div>

<script>
function updatePrice() {
    const select = document.getElementById('variant-select');
    const option = select.options[select.selectedIndex];
    
    const price = option.dataset.price;
    const compare = option.dataset.compare;
    
    // Mettre à jour l'affichage des prix
    document.querySelector('.price-current').textContent = '$' + price;
    if (compare && compare > price) {
        document.querySelector('.price-compare').textContent = '$' + compare;
        const discount = Math.round(((compare - price) / compare) * 100);
        document.querySelector('.badge-discount').textContent = '-' + discount + '%';
    }
}
</script>
{% endif %}
```

### Liste de Produits
```html
<div class="product-card">
    <img src="{{ product.image_url }}" alt="{{ product.name }}">
    
    <!-- Badge promo -->
    {% if product.get_discount_percentage() > 0 %}
    <span class="badge badge-sale">-{{ product.get_discount_percentage() }}%</span>
    {% endif %}
    
    <h3>{{ product.name }}</h3>
    
    <!-- Prix -->
    <div class="product-price">
        {% if product.compare_price and product.compare_price > product.price %}
            <del>${{ product.compare_price }}</del>
        {% endif %}
        <strong>${{ product.price }}</strong>
    </div>
</div>
```

---

## 🔧 CONFIGURATION SYSTÈME

### Table de Configuration des Marges
```sql
CREATE TABLE pricing_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_type ENUM('global', 'category', 'product') NOT NULL,
    target_id INT,  -- NULL pour global, category_id ou product_id
    markup_percentage DECIMAL(5,2) NOT NULL,
    min_price DECIMAL(10,2),  -- Prix minimum
    max_price DECIMAL(10,2),  -- Prix maximum
    rounding_strategy ENUM('none', 'up', 'down', 'nearest_99') DEFAULT 'nearest_99',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exemples de règles
INSERT INTO pricing_rules (rule_type, markup_percentage, rounding_strategy) 
VALUES ('global', 60.00, 'nearest_99');

INSERT INTO pricing_rules (rule_type, target_id, markup_percentage) 
VALUES ('category', 1, 80.00);  -- Catégorie Fashion

INSERT INTO pricing_rules (rule_type, target_id, markup_percentage) 
VALUES ('product', 123, 50.00);  -- Produit spécifique
```

### Service de Tarification
```python
class PricingService:
    """Service de gestion des prix et marges"""
    
    def __init__(self):
        self.default_markup = 60  # 60% par défaut
    
    def get_markup_for_product(self, product):
        """Récupère la marge applicable pour un produit"""
        # 1. Vérifier règle spécifique produit
        rule = PricingRule.query.filter_by(
            rule_type='product',
            target_id=product.id,
            is_active=True
        ).first()
        
        if rule:
            return rule.markup_percentage
        
        # 2. Vérifier règle catégorie
        if product.category_id:
            rule = PricingRule.query.filter_by(
                rule_type='category',
                target_id=product.category_id,
                is_active=True
            ).first()
            
            if rule:
                return rule.markup_percentage
        
        # 3. Règle globale
        rule = PricingRule.query.filter_by(
            rule_type='global',
            is_active=True
        ).first()
        
        return rule.markup_percentage if rule else self.default_markup
    
    def calculate_selling_price(self, cost_price, markup_percentage, rounding='nearest_99'):
        """Calcule le prix de vente avec marge et arrondi"""
        if not cost_price or cost_price <= 0:
            return 0
        
        # Calcul de base
        price = cost_price * (1 + markup_percentage / 100)
        
        # Stratégie d'arrondi
        if rounding == 'nearest_99':
            if price >= 10:
                price = int(price) + 0.99
            else:
                price = round(price, 2)
        elif rounding == 'up':
            price = math.ceil(price)
        elif rounding == 'down':
            price = math.floor(price)
        else:
            price = round(price, 2)
        
        return price
    
    def update_product_pricing(self, product, cj_sell_price, cj_suggested_price):
        """Met à jour les prix d'un produit"""
        markup = self.get_markup_for_product(product)
        
        product.cost_price = cj_sell_price
        product.price = self.calculate_selling_price(cj_sell_price, markup)
        product.compare_price = cj_suggested_price
        product.suggested_price = cj_suggested_price
        
        db.session.commit()
        
        return product
```

---

## 📊 ANALYTICS & REPORTING

### Métriques Importantes
```python
def get_pricing_analytics():
    """Récupère les analytics de tarification"""
    
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    analytics = {
        'total_products': len(products),
        'avg_cost_price': 0,
        'avg_selling_price': 0,
        'avg_margin_percentage': 0,
        'total_potential_profit': 0,
        'products_by_margin_range': {
            '0-30%': 0,
            '30-50%': 0,
            '50-70%': 0,
            '70-100%': 0,
            '100%+': 0
        }
    }
    
    total_cost = 0
    total_price = 0
    total_margin = 0
    
    for product in products:
        if product.cost_price and product.price:
            total_cost += product.cost_price
            total_price += product.price
            
            margin = product.get_margin_percentage()
            total_margin += margin
            
            # Classifier par tranche de marge
            if margin < 30:
                analytics['products_by_margin_range']['0-30%'] += 1
            elif margin < 50:
                analytics['products_by_margin_range']['30-50%'] += 1
            elif margin < 70:
                analytics['products_by_margin_range']['50-70%'] += 1
            elif margin < 100:
                analytics['products_by_margin_range']['70-100%'] += 1
            else:
                analytics['products_by_margin_range']['100%+'] += 1
    
    if len(products) > 0:
        analytics['avg_cost_price'] = total_cost / len(products)
        analytics['avg_selling_price'] = total_price / len(products)
        analytics['avg_margin_percentage'] = total_margin / len(products)
        analytics['total_potential_profit'] = total_price - total_cost
    
    return analytics
```

---

## ✅ CHECKLIST IMPLÉMENTATION

### Phase 1 - Basique
- [x] Champs prix dans modèle Product
- [ ] Service PricingService
- [ ] Calcul automatique prix lors synchronisation
- [ ] Affichage prix sur page produit
- [ ] Affichage prix barré et réduction

### Phase 2 - Avancé
- [ ] Table pricing_rules
- [ ] Configuration marges par catégorie
- [ ] Interface admin gestion marges
- [ ] Recalcul en masse des prix
- [ ] Analytics tarification

### Phase 3 - Optimisation
- [ ] Stratégies de tarification dynamique
- [ ] A/B testing prix
- [ ] Alertes marges faibles
- [ ] Historique évolution prix
- [ ] Comparaison concurrence

---

## 🎯 RECOMMANDATIONS

### Stratégie de Lancement
1. **Marge globale 60%** pour commencer
2. **Ajuster par catégorie** après analyse des ventes
3. **Surveiller la concurrence** et ajuster si nécessaire
4. **Tester différentes marges** sur produits similaires

### Optimisation Continue
- Analyser les produits avec marge < 40% (trop faible)
- Analyser les produits avec marge > 80% (peut-être trop élevé)
- Comparer prix vs concurrence
- Ajuster selon taux de conversion

### Affichage Psychologique
- Toujours afficher le prix barré si disponible
- Utiliser .99 pour prix > $10
- Mettre en avant les économies réalisées
- Badge "PROMO" pour réductions > 20%

---

**Date de création** : 22 Janvier 2026
**Version** : 1.0
