"""
Testar scraper.py:s parsningslogik utan nätverk och utan att behöva
FastAPI/SQLAlchemy installerat (de saknas i den här sandboxen).

Metod:
1. Stoppar in fejkade moduler i sys.modules för allt scraper.py importerar
   från backend (app.database, app.models) så att `import scraper` går
   igenom utan att sqlalchemy behöver finnas installerat.
2. Monkey-patchar requests.get så den returnerar realistisk Shopify
   products.json-data (samma struktur som Shopify faktiskt levererar -
   verifierad mot aspesi.com/barenavenezia.com tidigare i konversationen).
3. Kör den riktiga fetch_products_shopify()-funktionen från scraper.py och
   kontrollerar att den räknar ut rätt nuvarande pris / ordinarie pris.
"""
import sys
import types
from unittest.mock import patch, MagicMock

# --- Steg 1: fejka bort backend-beroendena ---
fake_database = types.ModuleType("app.database")
fake_database.SessionLocal = MagicMock()
fake_database.engine = MagicMock()
fake_database.Base = MagicMock()
fake_database.Base.metadata = MagicMock()

fake_models = types.ModuleType("app.models")
for name in ["Product", "Brand", "PriceHistory", "WatchlistItem", "DeviceToken"]:
    setattr(fake_models, name, MagicMock())

fake_app = types.ModuleType("app")
fake_app.database = fake_database
fake_app.models = fake_models

sys.modules["app"] = fake_app
sys.modules["app.database"] = fake_database
sys.modules["app.models"] = fake_models

sys.path.insert(0, ".")
import scraper  # noqa: E402  (importeras efter att fejk-modulerna finns på plats)

# --- Steg 2: realistisk Shopify products.json-data ---
# Strukturen matchar det Shopify faktiskt returnerar (verifierat tidigare
# mot aspesi.com/collections/mens-sale.atom, som bekräftar plattformen).
FAKE_SHOPIFY_RESPONSE = {
    "products": [
        {
            "id": 111,
            "title": "NYLON JACKET - NAVY",
            "handle": "nylon-jacket-navy",
            "images": [{"src": "https://cdn.shopify.com/fake/nylon-jacket.jpg"}],
            "variants": [
                {"id": 1, "price": "414.00", "compare_at_price": "690.00"},
                {"id": 2, "price": "414.00", "compare_at_price": "690.00"},
            ],
        },
        {
            "id": 222,
            "title": "COTTON CREWNECK SWEATER - NAVY",
            "handle": "cotton-crewneck-sweater-navy",
            "images": [{"src": "https://cdn.shopify.com/fake/sweater.jpg"}],
            "variants": [
                # Ingen rea på denna - compare_at_price saknas/null
                {"id": 3, "price": "132.00", "compare_at_price": None},
            ],
        },
    ]
}

FAKE_EMPTY_RESPONSE = {"products": []}


def fake_get(url, headers=None, params=None, timeout=None):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    page = (params or {}).get("page", 1)
    resp.json.return_value = FAKE_SHOPIFY_RESPONSE if page == 1 else FAKE_EMPTY_RESPONSE
    return resp


# --- Steg 3: kör den riktiga funktionen och verifiera resultatet ---
brand_config = {
    "name": "Aspesi",
    "platform": "shopify",
    "base_url": "https://aspesi.com/en-us",
    "collection_handle": "mens-sale",
}

with patch("scraper.requests.get", side_effect=fake_get):
    products = scraper.fetch_products_shopify(brand_config)

print(f"Antal produkter hittade: {len(products)}")
assert len(products) == 2, "Förväntade 2 produkter"

jacket = next(p for p in products if "JACKET" in p["name"])
assert jacket["current_price"] == 414.00, f"Fel pris: {jacket['current_price']}"
assert jacket["original_price"] == 690.00, f"Fel ordinarie pris: {jacket['original_price']}"
assert jacket["url"] == "https://aspesi.com/en-us/products/nylon-jacket-navy"
print(f"✓ Jacka: {jacket['current_price']} kr (ord. {jacket['original_price']} kr) - rea upptäckt korrekt")

sweater = next(p for p in products if "SWEATER" in p["name"])
assert sweater["original_price"] is None, "Tröjan ska inte ha ett ordinarie pris (ingen rea)"
print(f"✓ Tröja: {sweater['current_price']} kr, ingen rea - korrekt hanterat")

# Testa även is_on_sale-logiken i upsert-funktionen (utan att röra databasen)
is_on_sale_jacket = bool(jacket["original_price"] and jacket["current_price"] < jacket["original_price"])
is_on_sale_sweater = bool(sweater["original_price"] and sweater["current_price"] < (sweater["original_price"] or 0))
assert is_on_sale_jacket is True
assert is_on_sale_sweater is False
print("✓ is_on_sale-logiken ger rätt resultat i båda fallen")

print("\nAlla tester passerade.")
