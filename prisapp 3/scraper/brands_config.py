"""
Konfiguration per märke.

Jag har verifierat följande genom att faktiskt hämta sajterna (2026-09-13):

- Barena och Aspesi körs på SHOPIFY. Det betyder att de exponerar ett publikt
  JSON-flöde för varje kollektion: <bas-url>/collections/<handle>/products.json
  Där finns "price" (nuvarande pris) och "compare_at_price" (ordinarie pris)
  per variant - alltså exakt det vi behöver, helt utan CSS-gissning.

- Stone Island körs på Salesforce Commerce Cloud (samma plattform som andra
  Moncler-varumärken). Där finns ingen publik JSON-produktlista, så den kräver
  CSS-scraping av HTML:en. Den här typen av sajt har ofta bot-skydd
  (Akamai/PerimeterX eller liknande) - om requests-anropen börjar blockeras
  eller får konstiga svar är det troligen därför. Kontrollera robots.txt
  (stoneisland.com/robots.txt) innan du kör detta regelbundet, och undersök om
  Moncler-koncernen har ett affiliate-program (Awin m.fl.) som alternativ.

  CSS-selectorerna för Stone Island nedan är fortfarande PLATSHÅLLARE -
  jag kunde bekräfta att sale_url nedan stämmer, men kunde inte läsa ut de
  faktiska CSS-klasserna (verktyget jag använde för att hämta sidan strippar
  bort HTML-taggar). Öppna sale_url i webbläsaren, högerklicka på en produkt
  -> Inspektera, och fyll i rätt klasser (se README för steg-för-steg).
"""

BRANDS = [
    {
        "name": "Stone Island",
        "platform": "custom_html",
        "base_url": "https://www.stoneisland.com",
        "sale_url": "https://www.stoneisland.com/en-us/men/sales/view-all-sales",
        "selectors": {
            "product_card": "div.product-tile",       # TODO: verifiera i DevTools
            "product_name": ".product-tile__name",
            "product_url": "a.product-tile__link",
            "price_current": ".price__sales",
            "price_original": ".price__strike-through",
            "image": "img.product-tile__image",
        },
    },
    {
        "name": "Barena",
        "platform": "shopify",
        "base_url": "https://barenavenezia.com",
        "collection_handle": "private-sale-men",
    },
    {
        "name": "Aspesi",
        "platform": "shopify",
        "base_url": "https://aspesi.com/en-us",
        "collection_handle": "mens-sale",
    },
]
