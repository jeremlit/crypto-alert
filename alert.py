import requests
import json
import os

STATE_FILE = "state.json"
SYMBOL = "ETHUSDT"
DROP_THRESHOLD = 0.05

# API publique Binance (sans client officiel)
URL = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"

def get_price():
    response = requests.get(URL, timeout=10)
    response.raise_for_status()
    return float(response.json()["price"])

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
