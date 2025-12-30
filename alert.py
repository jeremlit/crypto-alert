import requests
import json
import os

STATE_FILE = "state.json"
DROP_THRESHOLD = 0.05

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# CoinGecko API
URL = "https://api.coingecko.com/api/v3/simple/price"
PARAMS = {
    "ids": "ethereum",
    "vs_currencies": "usd"
}

def get_price():
    response = requests.get(URL, params=PARAMS, timeout=10)
    response.raise_for_status()
    return float(response.json()["ethereum"]["usd"])

# Charger l'état précédent
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
        reference_price = state["reference_price"]
else:
    reference_price = get_price()

current_price = get_price()
drop = (reference_price - current_price) / reference_price

print(f"Référence : {reference_price}")
print(f"Prix actuel : {current_price}")
print(f"Baisse : {drop * 100:.2f} %")

if drop >= DROP_THRESHOLD:
    print("🚨 ALERTE : baisse de 5 % détectée")
    reference_price = current_price  # reset après alerte

# Sauvegarder l'état
with open(STATE_FILE, "w") as f:
    json.dump({"reference_price": reference_price}, f)

send_telegram("✅ Test Telegram OK – script alert.py existant")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, json=payload, timeout=10)
