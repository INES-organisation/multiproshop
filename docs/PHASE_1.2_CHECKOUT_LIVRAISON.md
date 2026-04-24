# 🚚 PHASE 1.2 - CHECKOUT & LIVRAISON CJ

## 🎯 Vue d'ensemble

Système complet de gestion de la livraison intégré avec CJ Dropshipping pour le checkout.

---

## ✅ FONCTIONNALITÉS IMPLÉMENTÉES

### 1. Service CjShippingService

#### Méthodes disponibles

**`get_shipping_methods(country_code, product_ids=None)`**
- Récupère les méthodes de livraison disponibles pour un pays
- Paramètres : Code pays ISO, IDs produits (optionnel)
- Retourne : Liste des méthodes avec prix et délais

**`calculate_shipping_cost(cart_items, country_code, shipping_method_id=None)`**
- Calcule les frais de livraison pour un panier
- Prend en compte le poids total et les variantes
- Retourne : Coût, devise, délai, méthode

**`estimate_delivery_time(country_code, shipping_method_id=None)`**
- Estime le délai de livraison selon le pays
- Retourne : Min/max jours, description

**`validate_shipping_address(address_data)`**
- Valide une adresse de livraison
- Vérifie les champs requis et le pays supporté
- Retourne : Validation + adresse normalisée

**`get_supported_countries()`**
- Liste des 40+ pays supportés par CJ
- Codes ISO : US, CA, GB, FR, DE, ES, IT, AU, JP, etc.

**`get_shipping_zones()`**
- 6 zones de livraison avec tarifs indicatifs
- Zone 1 : Amérique du Nord (5.99$)
- Zone 2 : Europe Occidentale (7.99$)
- Zone 3 : Europe du Nord (8.99$)
- Zone 4 : Océanie (9.99$)
- Zone 5 : Asie (6.99$)
- Zone 6 : Reste du monde (12.99$)

### 2. API REST - Routes Shipping

```
GET  /api/shipping/methods/<country_code>        - Méthodes disponibles
POST /api/shipping/calculate                     - Calculer frais
GET  /api/shipping/estimate-delivery/<country>   - Estimer délai
POST /api/shipping/validate-address              - Valider adresse
GET  /api/shipping/supported-countries           - Pays supportés
GET  /api/shipping/zones                         - Zones de livraison
POST /api/shipping/cart/calculate                - Frais pour panier session
```

### 3. Calcul Intelligent des Frais

#### Basé sur le poids
- Poids récupéré depuis les variantes ou produits
- Tarif de base : 3.99$
- Coût par kg supplémentaire :
  - 0-0.5kg : 3.99$
  - 0.5-1kg : 5.99$
  - 1-2kg : 7.99$
  - 2kg+ : 7.99$ + 1.50$/kg

#### Majoration selon le pays
- US : x1.0 (tarif de base)
- CA : x1.1
- Europe Occidentale : x1.2
- Asie : x1.0-1.4
- Océanie : x1.5
- Autres : x1.3

### 4. Intégration Panier

#### Session Flask
- Stockage des frais de livraison : `session['shipping_cost']`
- Méthode sélectionnée : `session['shipping_method']`
- Pays de destination : `session['shipping_country']`

#### Format cart_items
```json
[
  {
    "product_id": 123,
    "variant_id": 456,
    "quantity": 2
  }
]
```

---

## 📊 ZONES DE LIVRAISON

| Zone | Régions | Pays | Tarif Base | Délai |
|------|---------|------|------------|-------|
| **Zone 1** | Amérique du Nord | US, CA | 5.99$ | 7-15j |
| **Zone 2** | Europe Occidentale | GB, FR, DE, ES, IT, NL, BE | 7.99$ | 12-25j |
| **Zone 3** | Europe du Nord | SE, NO, DK, FI | 8.99$ | 15-30j |
| **Zone 4** | Océanie | AU, NZ | 9.99$ | 15-35j |
| **Zone 5** | Asie | JP, KR, SG, MY, TH | 6.99$ | 10-20j |
| **Zone 6** | Reste du monde | Autres | 12.99$ | 20-40j |

---

## 🔧 UTILISATION

### Backend - Calculer frais de livraison

```python
from services.cj_shipping_service import CjShippingService

shipping_service = CjShippingService(cj_api)

cart_items = [
    {'product_id': 123, 'variant_id': 456, 'quantity': 2},
    {'product_id': 789, 'variant_id': None, 'quantity': 1}
]

result = shipping_service.calculate_shipping_cost(
    cart_items=cart_items,
    country_code='FR',
    shipping_method_id=None
)

print(f"Frais de livraison: {result['shipping_cost']} {result['currency']}")
print(f"Délai: {result['delivery_time']}")
print(f"Méthode: {result['method']}")
```

### Frontend - API Call

```javascript
// Calculer frais pour le panier
fetch('/api/shipping/cart/calculate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        country_code: 'FR',
        shipping_method_id: null
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Frais:', data.shipping_cost);
        console.log('Délai:', data.delivery_time);
        updateCheckoutTotal(data.shipping_cost);
    }
});
```

### Valider une adresse

```javascript
fetch('/api/shipping/validate-address', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        country: 'FR',
        city: 'Paris',
        address: '123 Rue de la Paix',
        zip_code: '75001',
        state: 'Île-de-France',
        phone: '+33123456789'
    })
})
.then(response => response.json())
.then(data => {
    if (data.valid) {
        console.log('Adresse valide');
        proceedToPayment();
    } else {
        console.log('Erreur:', data.message);
        showAddressErrors(data.missing_fields);
    }
});
```

---

## 🎨 INTÉGRATION CHECKOUT

### Étape 1 : Sélection Pays
```html
<select id="shipping-country" onchange="updateShippingMethods()">
    <option value="US">États-Unis</option>
    <option value="FR">France</option>
    <option value="GB">Royaume-Uni</option>
    <!-- ... -->
</select>
```

### Étape 2 : Méthodes de Livraison
```javascript
function updateShippingMethods() {
    const country = document.getElementById('shipping-country').value;
    
    fetch(`/api/shipping/methods/${country}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayShippingMethods(data.methods);
            }
        });
}

function displayShippingMethods(methods) {
    const container = document.getElementById('shipping-methods');
    
    methods.forEach(method => {
        const html = `
            <div class="shipping-method">
                <input type="radio" name="shipping" value="${method.id}">
                <label>
                    <strong>${method.name}</strong>
                    <span>${method.price} USD</span>
                    <small>${method.delivery_time}</small>
                </label>
            </div>
        `;
        container.innerHTML += html;
    });
}
```

### Étape 3 : Calcul Total
```javascript
function calculateTotal() {
    const country = document.getElementById('shipping-country').value;
    const methodId = document.querySelector('input[name="shipping"]:checked').value;
    
    fetch('/api/shipping/cart/calculate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            country_code: country,
            shipping_method_id: methodId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateOrderSummary(data.shipping_cost);
        }
    });
}

function updateOrderSummary(shippingCost) {
    const subtotal = getCartSubtotal();
    const total = subtotal + shippingCost;
    
    document.getElementById('shipping-cost').textContent = `$${shippingCost.toFixed(2)}`;
    document.getElementById('order-total').textContent = `$${total.toFixed(2)}`;
}
```

---

## 📝 VALIDATION ADRESSE

### Champs requis
- `country` : Code pays ISO (requis)
- `city` : Ville (requis)
- `address` : Adresse complète (requis)
- `zip_code` : Code postal (requis)
- `state` : État/Province (optionnel)
- `phone` : Téléphone (optionnel)

### Exemple de validation
```python
address_data = {
    'country': 'FR',
    'city': 'Paris',
    'address': '123 Rue de la Paix',
    'zip_code': '75001',
    'state': 'Île-de-France',
    'phone': '+33123456789'
}

result = shipping_service.validate_shipping_address(address_data)

if result['valid']:
    print("✓ Adresse valide")
    normalized = result['normalized_address']
else:
    print("✗ Adresse invalide")
    print(f"Champs manquants: {result['missing_fields']}")
```

---

## 🚀 PROCHAINES ÉTAPES

### Phase 1.3 - Gestion Commandes CJ
- [ ] **CJOrderService** - Service de création commandes
- [ ] **Création commande après paiement** - Automatique
- [ ] **Tracking des commandes** - Suivi en temps réel
- [ ] **Synchronisation statuts** - Mise à jour automatique
- [ ] **Webhooks CJ** - Notifications événements
- [ ] **Gestion remboursements** - Retours et annulations

### Améliorations Livraison
- [ ] **Cache des méthodes de livraison** - Réduire appels API
- [ ] **Estimation date de livraison** - Calcul avec datetime
- [ ] **Livraison express** - Options premium
- [ ] **Livraison gratuite** - Seuils configurables
- [ ] **Multi-colis** - Gestion envois multiples

---

## 📚 RÉFÉRENCE API CJ

### Endpoints utilisés
- `POST /shopping/logistics/query` - Méthodes de livraison
- `POST /shopping/logistics/freightCalculate` - Calcul frais
- `GET /shopping/logistics/countries` - Pays supportés

### Format réponse CJ
```json
{
  "code": 200,
  "result": true,
  "data": [
    {
      "logisticsId": "CJ_PACKET_US",
      "logisticsName": "CJ Packet",
      "logisticsNameEn": "CJ Packet",
      "logisticsPrice": 5.99,
      "deliveryTime": "7-15",
      "deliveryTimeDesc": "7-15 business days",
      "trackingAvailable": true
    }
  ]
}
```

---

## 🔒 SÉCURITÉ

### Validation côté serveur
- ✅ Vérification pays supporté
- ✅ Validation format adresse
- ✅ Vérification stock avant calcul
- ✅ Protection contre manipulation prix

### Gestion des erreurs
- Fallback sur tarifs par défaut si API échoue
- Messages d'erreur clairs pour l'utilisateur
- Logging des erreurs pour debug
- Retry automatique sur timeout

---

## 📊 STATISTIQUES

| Métrique | Valeur |
|----------|--------|
| **Pays supportés** | 40+ |
| **Zones de livraison** | 6 |
| **Méthodes de livraison** | 5-10 par pays |
| **Délai moyen** | 15-25 jours |
| **Tarif moyen** | 7.99$ |

---

**Dernière mise à jour:** 23 janvier 2026  
**Version:** 1.0.0  
**Statut:** ✅ Implémenté et testé
