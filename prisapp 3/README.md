# Prisbevakning – Stone Island, Barena, Aspesi

Skelett för en app som dagligen kollar rea/prissänkningar hos utvalda klädmärken
och pushar en notis när priset sjunker. Tre delar:

```
backend/   FastAPI + databas (produkter, prishistorik, bevakningslistor)
scraper/   Daglig scraper som fyller databasen och triggar notiser
mobile/    Expo/React Native-app (bevakningslista + bläddra & lägg till)
```

## Vad jag har testat åt dig

Jag har **inte** kunnat köra hela kedjan live i den här miljön (ingen
internetuppkoppling här, och FastAPI/SQLAlchemy/firebase-admin kan inte
installeras i sandboxen). Men jag har verifierat att själva kodlogiken är
korrekt genom att köra den mot realistisk mockad data:

```bash
cd scraper
python test_scraper_logic.py       # Shopify-parsning (Barena/Aspesi)
python test_notification_logic.py  # CSS-scraping (Stone Island) + pris-tröskel
```

Båda testerna kör den *riktiga* koden från `scraper.py` (inte en förenklad
kopia) mot fejkad men verklighetstrogen data, och verifierar att:
- Shopify-flödet plockar ut rätt nuvarande pris/ordinarie pris per produkt
- Rader utan rea (`compare_at_price` saknas) hanteras korrekt
- CSS-scraping-koden (samma kodväg som Stone Island kommer använda) parsar
  ett HTML-exempel korrekt när selectorerna stämmer
- Tröskellogiken för notiser (t.ex. "notifiera vid minst 15% rabatt")
  ger rätt resultat i alla kombinationer

**Det du behöver testa själv, med riktig internetåtkomst:**
1. `python scraper.py` mot de riktiga sajterna (Barena/Aspesi borde funka direkt)
2. Backend: `pip install -r requirements.txt` och `uvicorn app.main:app --reload`
3. Mobilappen mot en deployad backend
4. En riktig push-notis end-to-end när du har satt upp Firebase

## Vad jag har verifierat mot de riktiga sajterna

Jag har faktiskt hämtat och undersökt alla tre sajterna (2026-09-13):

| Märke | Plattform | Hämtningssätt | Status |
|---|---|---|---|
| Barena | Shopify | Publikt `products.json`-flöde | Klart, verifierad URL |
| Aspesi | Shopify | Publikt `products.json`-flöde | Klart, verifierad URL |
| Stone Island | Salesforce Commerce Cloud | CSS-scraping | CSS-selectors måste fyllas i själv |

**Barena och Aspesi** exponerar Shopifys publika JSON-flöde för varje
kollektion (`<sajt>/collections/<handle>/products.json`), som innehåller både
`price` (nuvarande pris) och `compare_at_price` (ordinarie pris) per variant.
Det är mer robust än CSS-scraping eftersom det inte går sönder när sajten
byter design. Verifierade rea-URL:er:
- Barena: `https://barenavenezia.com/collections/private-sale-men`
- Aspesi: `https://aspesi.com/en-us/collections/mens-sale`

**Stone Island** körs på Salesforce Commerce Cloud (samma plattform som andra
märken i Moncler-koncernen) och saknar ett publikt produkt-API, så den kräver
fortfarande CSS-scraping. Jag kunde bekräfta rätt sale-URL
(`https://www.stoneisland.com/en-us/men/sales/view-all-sales`), men inte de
exakta CSS-klasserna – verktyget jag använde för att läsa sajten strippar bort
HTML-strukturen. Så här hittar du dem själv:

1. Öppna sale-URL:en ovan i Chrome/Firefox
2. Högerklicka på en produkts namn eller pris -> **Inspektera**
3. I DevTools ser du HTML-elementet markerat, t.ex. `<span class="price__sales">1 200 kr</span>`
4. Notera klassnamnet (`price__sales` i exemplet) och fyll i motsvarande
   nyckel i `scraper/brands_config.py` under `Stone Island -> selectors`
5. Upprepa för produktkortet (den yttre `<div>` eller `<li>` som omsluter hela
   produkten), namnet, länken, priset (nuvarande och ordinarie) och bilden
6. Kör `python scraper.py` och se i terminalen om produkter hittas för
   Stone Island

**Om Stone Island blockerar requests helt** (vanligt hos stora
e-handelssajter med bot-skydd som Akamai/PerimeterX): kontrollera
`stoneisland.com/robots.txt` för vad som är tillåtet, och undersök om
Moncler-koncernen har ett affiliate-program (t.ex. via Awin) som ger samma
prisdata på ett tillåtet sätt istället.

- Om en sajt renderar priser med JavaScript (inte fallet för någon av de tre
  här, men vanligt på andra sajter) räcker inte `requests` + `BeautifulSoup`.
  Byt då ut motsvarande funktion i `scraper/scraper.py` mot en
  Playwright-variant (kommentar finns i filen).

## 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Databasen är SQLite som standard (`prisapp.db`, skapas automatiskt) - bra för
att testa lokalt. **För deploy behöver du Postgres istället**, eftersom
Render (och de flesta molntjänster) har ett filsystem som återställs vid
omstart - en SQLite-fil skulle raderas.

### Deploya till Render

1. Lägg upp `prisapp`-mappen (eller åtminstone `backend/`, `scraper/` och
   `.github/`) i ett GitHub-repo
2. Skapa konto på [render.com](https://render.com) (inget kort krävs)
3. **Skapa databasen först:** Dashboard -> New -> PostgreSQL
   - Välj gratis-planen (varar ~30 dagar - bra för att testa, uppgradera till
     Basic-256MB (~$7/mån) när du vet att appen ska användas skarpt)
   - När den är klar, kopiera **"External Database URL"** (den behövs både
     av backend och av GitHub Actions-scrapern, som körs utanför Render)
4. **Skapa webbtjänsten:** Dashboard -> New -> Web Service -> koppla ditt
   GitHub-repo
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Under Environment: lägg till `DATABASE_URL` = den External Database URL
     du kopierade i steg 3
   - Välj Free-planen
5. Klicka Deploy. Efter någon minut får du en URL, t.ex.
   `https://prisapp-xyz.onrender.com`
6. Testa i webbläsaren: `https://prisapp-xyz.onrender.com/docs` - där ser du
   FastAPI:s auto-genererade API-dokumentation och kan testa endpoints direkt

**Bra att veta om gratisnivån:** webbtjänsten "somnar" efter 15 minuters
inaktivitet och tar 30-60 sekunder att vakna igen vid nästa anrop. Det märks
som en fördröjning första gången du öppnar appen efter en stund, men
påverkar inte scrapern eller notiserna eftersom de pratar direkt med
databasen (se nästa avsnitt) istället för via webbtjänsten.

**Cron jobs är INTE gratis på Render** (från $1/mån) - använd GitHub
Actions-workflowen i `.github/workflows/daily-scrape.yml` istället, som är
helt gratis. Den kör `scraper.py` en gång per dag. Lägg till dessa som
"Repository secrets" i ditt GitHub-repo (Settings -> Secrets and variables
-> Actions):
- `DATABASE_URL` - samma External Database URL som ovan
- `FCM_SERVICE_ACCOUNT_JSON` - hela innehållet i din Firebase
  service account-nyckel (JSON-filen från Firebase-genomgången), inklistrat
  som text

Du kan trigga workflowen manuellt direkt (utan att vänta till 07:00) under
GitHub-repots flik **Actions** -> "Daily price scrape" -> "Run workflow", för
att testa att allt är rätt kopplat.

## 2. Scraper

```bash
cd scraper
pip install -r requirements.txt
python scraper.py
```

Kör detta dagligen:
- **Enklast:** ett cron-jobb på en liten server (`0 7 * * * cd /path/scraper && python scraper.py`)
- **Serverlöst:** AWS Lambda + EventBridge, eller Google Cloud Scheduler + Cloud Run

### Notiser (push)
1. Skapa ett Firebase-projekt (gratis): https://console.firebase.google.com
2. Lägg till appen, ladda ner `google-services.json` (Android) och
   `GoogleService-Info.plist` (iOS) till `mobile/`
3. Skapa en service account-nyckel och peka på den:
   ```bash
   export FCM_SERVICE_ACCOUNT_PATH="/sökväg/till/nyckel.json"
   ```

## 3. Mobilapp

```bash
cd mobile
npm install
```

Byt `API_BASE_URL` i `mobile/api.js` till din deployade backend-URL.

### Push-notiser kräver en "development build"

Push-notiser i `hooks/usePushNotifications.js` fungerar **inte** i vanliga
Expo Go-appen (Expo tog bort stödet för remote push i Expo Go från SDK 49).
Du behöver bygga en egen dev-variant av appen en gång:

1. Lägg de nedladdade filerna från Firebase i `mobile/`:
   - `google-services.json` (Android)
   - `GoogleService-Info.plist` (iOS)
2. Se till att `android.package` / `ios.bundleIdentifier` i `mobile/app.json`
   matchar exakt det package name / bundle ID du angav i Firebase Console
3. Installera EAS CLI och bygg:
   ```bash
   npm install -g eas-cli
   eas login
   eas build:configure
   eas build --profile development --platform android
   ```
   (byt `android` mot `ios` för iPhone, kräver Apple-utvecklarkonto för push)
4. Installera den byggda appen på din telefon, kör sedan:
   ```bash
   npx expo start --dev-client
   ```
   och skanna QR-koden med kameran

Efter detta ber appen om notis-behörighet vid start, hämtar enhetens
FCM-token och skickar den till `/device-tokens` på din backend automatiskt.

### Snabbtest utan riktig build

Om du bara vill testa UI:t (bevakningslista, bläddra-skärm) utan notiser kan
du fortfarande använda vanliga Expo Go: `npx expo start`. Du får då ett
felmeddelande högst upp i appen ("Notiser avstängda: ...") men resten
fungerar som vanligt.

## Rekommenderad ordning att bygga vidare i

1. Fyll i rätt CSS-selectors för ett märke i taget, kör `python scraper.py`,
   verifiera att produkter dyker upp i databasen.
2. När scrapern fungerar för alla tre märken, deploya backend.
3. Testa mobilappen mot den deployade backend:en.
4. Sätt upp cron/schemaläggning för scrapern och koppla på Firebase-notiser.
