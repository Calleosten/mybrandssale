"""
Push-notiser via Firebase Cloud Messaging (FCM).

Setup:
1. Skapa ett gratis Firebase-projekt: https://console.firebase.google.com
2. Lägg till din app (iOS/Android) i projektet, ladda ner konfigurationsfilerna
   (google-services.json / GoogleService-Info.plist) till mobilappen
3. Skapa ett service account-nyckelfil (Project settings -> Service accounts)
   och peka på den nedan via miljövariabeln FCM_SERVICE_ACCOUNT_PATH
4. pip install firebase-admin
"""

import os

FCM_SERVICE_ACCOUNT_PATH = os.getenv("FCM_SERVICE_ACCOUNT_PATH", "")

_firebase_app = None


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    import firebase_admin
    from firebase_admin import credentials

    if not FCM_SERVICE_ACCOUNT_PATH:
        raise RuntimeError(
            "Sätt miljövariabeln FCM_SERVICE_ACCOUNT_PATH till sökvägen för din "
            "Firebase service account-nyckel (se kommentar högst upp i denna fil)."
        )

    cred = credentials.Certificate(FCM_SERVICE_ACCOUNT_PATH)
    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def send_price_drop_notification(fcm_token: str, product_name: str, new_price: float, drop_percent: float):
    try:
        from firebase_admin import messaging

        _get_firebase_app()
        message = messaging.Message(
            notification=messaging.Notification(
                title="Prissänkning!",
                body=f"{product_name} har sänkts {drop_percent:.0f}% - nu {new_price:.0f} kr",
            ),
            token=fcm_token,
        )
        messaging.send(message)
        print(f"  Notis skickad för {product_name}")
    except Exception as exc:
        # I skelettet loggar vi bara felet så att scraper-jobbet inte kraschar
        # om FCM inte är konfigurerat än.
        print(f"  Kunde inte skicka notis ({product_name}): {exc}")
