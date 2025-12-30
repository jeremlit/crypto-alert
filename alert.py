from binance.client import Client
import json
import os

STATE_FILE = "state.json"
SYMBOL = "ETHUSDT"
DROP_THRESHOLD = 0.05

client = Client()

# Charger l'état précédent
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
        reference_price = state["reference_price"]
else:
    reference_price = float(client.get_symbol_ticker(symbol=SYMBOL)["price"])

current_price = float(client.get_symbol_ticker(symbol=SYMBOL)["price"])
drop = (reference_price - current_price) / reference_price

print(f"Référence : {reference_price}")
print(f"Prix actuel : {current_price}")
print(f"Baisse : {drop * 100:.2f} %")

if drop >= DROP_THRESHOLD:
    print("🚨 ALERTE : baisse de 5 % détectée")
    reference_price = current_price  # reset après alerte

# Sauvegarder le nouvel état
with open(STATE_FILE, "w") as f:
    json.dump({"reference_price": reference_price}, f)
