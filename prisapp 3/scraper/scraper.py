"""
Daglig scraper. Körs t.ex. via cron eller en molnschemaläggare (se README).

Två hämtningssätt beroende på plattform (se brands_config.py):
- "shopify" (Barena, Aspesi): hämtar det publika products.json-flödet för
  kollektionen. Ger oss "price" och "compare_at_price" direkt - inga
  CSS-selectors behövs, och det går inte sönder lika lätt som HTML-scraping.
- "custom_html" (Stone Island): scrapar HTML med CSS-selectors (se kommentar
  i brands_config.py om varför denna sajt är svårare).

Flöde för båda typerna:
1. Hämta produkter + priser för märket
2. Spara/uppdatera produkter i databasen, lägg till en rad i prishistorik
3. Om priset sjunkit tillräckligt mycket jämfört med föregående pris,
   skicka en push-notis till alla som bevakar produkten
"""

import sys
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Återanvänd samma databas-modeller som backend-API:et
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.database import SessionLocal, engine, Base  # noqa: E402
from app import models  # noqa: E402
from brands_config import BRANDS  # noqa: E402
from notifications import send_price_drop_notification  # noqa: E402

Base.metadata.create_all(bind=engine)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PrisbevakningBot/1.0; +https://example.com/bot)"
}


def parse_price(raw: str | None) -> float | None:
    if not raw:
        return None
    cleaned = raw.replace("kr", "").replace("SEK", "").replace(",", ".").strip()
    cleaned = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def fetch_products_shopify(brand_config: dict) -> list[dict]:
    """Hämtar produkter via Shopify:s publika products.json för en kollektion.

    Varje produkt kan ha flera varianter (t.ex. storlekar) med olika pris.
    Vi tar den billigaste varianten som produktens "pris just nu" och den
    högsta compare_at_price:en som "ordinarie pris", vilket ger en rimlig
    bild även om olika storlekar råkar ha marginellt olika pris.
    """
    url = f"{brand_config['base_url'].rstrip('/')}/collections/{brand_config['collection_handle']}/products.json"
    products = []
    page = 1

    while True:
        resp = requests.get(url, headers=HEADERS, params={"limit": 250, "page": page}, timeout=15)

        print(f"    [{brand_config['name']}] GET {resp.url} -> status {resp.status_code}")
        if resp.history:
            print(f"    [{brand_config['name']}] Omdirigerades via: {[r.url for r in resp.history]}")

        resp.raise_for_status()

        try:
            data = resp.json()
        except ValueError:
            print(f"    [{brand_config['name']}] Svaret var inte giltig JSON. Första 300 tecknen:")
            print(f"    {resp.text[:300]!r}")
            break

        batch = data.get("products", [])
        if page == 1:
            print(f"    [{brand_config['name']}] Sida 1 innehöll {len(batch)} produkter i rådata")
        if not batch:
            break

        for p in batch:
            variants = p.get("variants", [])
            if not variants:
                continue

            prices = [float(v["price"]) for v in variants if v.get("price")]
            compare_prices = [
                float(v["compare_at_price"]) for v in variants if v.get("compare_at_price")
            ]
            if not prices:
                continue

            current_price = min(prices)
            original_price = max(compare_prices) if compare_prices else None

            image_url = None
            if p.get("images"):
                image_url = p["images"][0].get("src")

            product_url = f"{brand_config['base_url'].rstrip('/')}/products/{p['handle']}"

            products.append({
                "name": p.get("title", "").strip(),
                "url": product_url,
                "image_url": image_url,
                "current_price": current_price,
                "original_price": original_price,
            })

        page += 1
        if page > 20:  # säkerhetsspärr mot oändlig loop
            break

    return products


def fetch_products_custom_html(brand_config: dict) -> list[dict]:
    """Hämtar produkter genom att scrapa HTML med CSS-selectors.

    OBS: Om sajten laddar priser via JavaScript kommer requests+BeautifulSoup
    inte se dem. Byt då ut denna funktion mot en Playwright-variant, t.ex.:

        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            html = page.content()
            browser.close()
    """
    selectors = brand_config["selectors"]
    resp = requests.get(brand_config["sale_url"], headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    products = []
    for card in soup.select(selectors["product_card"]):
        name_el = card.select_one(selectors["product_name"])
        url_el = card.select_one(selectors["product_url"])
        price_current_el = card.select_one(selectors["price_current"])
        price_original_el = card.select_one(selectors["price_original"])
        image_el = card.select_one(selectors["image"])

        if not name_el or not url_el:
            continue

        url = url_el.get("href", "")
        if url.startswith("/"):
            url = brand_config["base_url"].rstrip("/") + url

        products.append({
            "name": name_el.get_text(strip=True),
            "url": url,
            "image_url": image_el.get("src") if image_el else None,
            "current_price": parse_price(price_current_el.get_text() if price_current_el else None),
            "original_price": parse_price(price_original_el.get_text() if price_original_el else None),
        })
    return products


def fetch_products_for_brand(brand_config: dict) -> list[dict]:
    if brand_config["platform"] == "shopify":
        return fetch_products_shopify(brand_config)
    return fetch_products_custom_html(brand_config)


def upsert_product_and_check_price_drop(db, brand: models.Brand, item: dict):
    product = db.query(models.Product).filter(models.Product.url == item["url"]).first()
    previous_price = product.current_price if product else None

    if not product:
        product = models.Product(brand_id=brand.id, url=item["url"], name=item["name"])
        db.add(product)

    product.name = item["name"]
    product.image_url = item["image_url"]
    product.current_price = item["current_price"]
    product.original_price = item["original_price"]
    product.last_checked = datetime.utcnow()

    if item["current_price"] is not None:
        if product.lowest_price_seen is None or item["current_price"] < product.lowest_price_seen:
            product.lowest_price_seen = item["current_price"]
        product.is_on_sale = bool(
            item["original_price"] and item["current_price"] < item["original_price"]
        )

    db.commit()
    db.refresh(product)

    if item["current_price"] is not None:
        db.add(models.PriceHistory(product_id=product.id, price=item["current_price"]))
        db.commit()

    # Skicka notis om priset sjönk sedan förra kollen
    if previous_price and item["current_price"] and item["current_price"] < previous_price:
        drop_percent = (previous_price - item["current_price"]) / previous_price * 100
        notify_watchers(db, product, drop_percent)


def notify_watchers(db, product: models.Product, drop_percent: float):
    watchers = (
        db.query(models.WatchlistItem)
        .filter(models.WatchlistItem.product_id == product.id)
        .filter(models.WatchlistItem.notify_threshold_percent <= drop_percent)
        .all()
    )
    for watch in watchers:
        tokens = (
            db.query(models.DeviceToken)
            .filter(models.DeviceToken.user_id == watch.user_id)
            .all()
        )
        for token in tokens:
            send_price_drop_notification(
                fcm_token=token.fcm_token,
                product_name=product.name,
                new_price=product.current_price,
                drop_percent=drop_percent,
            )


def run():
    db = SessionLocal()
 try:
        print("!!!! DEBUG MARKER 12345 - NY KOD KÖRS !!!!")
      
        for brand_config in BRANDS:
            brand = db.query(models.Brand).filter(models.Brand.name == brand_config["name"]).first()
            if not brand:
                brand = models.Brand(name=brand_config["name"], base_url=brand_config["base_url"])
                db.add(brand)
                db.commit()
                db.refresh(brand)

            print(f"Scrapar {brand.name} ({brand_config['platform']})...")
            try:
                items = fetch_products_for_brand(brand_config)
            except Exception as exc:  # nätverksfel, ändrad struktur, bot-blockering m.m.
                print(f"  Misslyckades för {brand.name}: {exc}")
                continue

            print(f"  Hittade {len(items)} produkter")
            for item in items:
                upsert_product_and_check_price_drop(db, brand, item)
    finally:
        db.close()


if __name__ == "__main__":
    run()
