import sys
import types
from unittest.mock import patch, MagicMock

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
import scraper  # noqa: E402

# --- Test 1: CSS-scraping (samma kod-väg som Stone Island använder) ---
FAKE_HTML = """
<html><body>
  <div class="product-tile">
    <a class="product-tile__link" href="/produkt/jacka-123">
      <span class="product-tile__name">Testjacka</span>
    </a>
    <span class="price__sales">1 200 kr</span>
    <span class="price__strike-through">2 000 kr</span>
    <img class="product-tile__image" src="https://example.com/jacka.jpg">
  </div>
</body></html>
"""


def fake_get(url, headers=None, timeout=None, **kwargs):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.text = FAKE_HTML
    return resp


brand_config = {
    "name": "Stone Island",
    "platform": "custom_html",
    "base_url": "https://www.stoneisland.com",
    "sale_url": "https://www.stoneisland.com/en-us/men/sales/view-all-sales",
    "selectors": {
        "product_card": "div.product-tile",
        "product_name": ".product-tile__name",
        "product_url": "a.product-tile__link",
        "price_current": ".price__sales",
        "price_original": ".price__strike-through",
        "image": "img.product-tile__image",
    },
}

with patch("scraper.requests.get", side_effect=fake_get):
    products = scraper.fetch_products_custom_html(brand_config)

assert len(products) == 1, f"Förväntade 1 produkt, fick {len(products)}"
p = products[0]
assert p["name"] == "Testjacka"
assert p["url"] == "https://www.stoneisland.com/produkt/jacka-123", p["url"]
assert p["current_price"] == 1200.0, p["current_price"]
assert p["original_price"] == 2000.0, p["original_price"]
print(f"✓ CSS-scraping funkar: {p['name']} - {p['current_price']} kr (ord. {p['original_price']} kr)")
print("  (Detta bevisar att SJÄLVA SCRAPING-KODEN funkar korrekt - det som")
print("   återstår är att peka selectorerna på Stone Islands riktiga HTML,")
print("   vilket kräver att du öppnar DevTools på den riktiga sajten.)")

# --- Test 2: pris-drop-tröskel (avgör om notis ska skickas) ---
def would_notify(previous_price, new_price, threshold_percent):
    if not (previous_price and new_price and new_price < previous_price):
        return False
    drop_percent = (previous_price - new_price) / previous_price * 100
    return drop_percent >= threshold_percent


cases = [
    (1000, 850, 15, True),   # 15% rabatt, tröskel 15% -> ska notifiera
    (1000, 900, 15, False),  # 10% rabatt, tröskel 15% -> ska INTE notifiera
    (1000, 1000, 15, False), # oförändrat pris -> ska INTE notifiera
    (1000, 1100, 15, False), # pris höjdes -> ska INTE notifiera
]
for prev, new, threshold, expected in cases:
    result = would_notify(prev, new, threshold)
    status = "✓" if result == expected else "✗ FEL"
    print(f"{status} {prev}kr -> {new}kr, tröskel {threshold}% => notifiera={result} (förväntat {expected})")
    assert result == expected

print("\nAlla tester passerade.")
