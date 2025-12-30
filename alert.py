import requests
import json
import os

STATE_FILE = "state.json"

# ---- Paramètres ----
DROP_THRESHOLD = 0.05          # -5%
REARM_THRESHOLD = 0.02         # réarme si on repasse au-dessus de -2% (anti-spam)
# Tu peux ajuster REARM_THRESHOLD selon ton goût

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"
PARAMS = {"ids": "ethereum", "vs_currencies": "usd"}


def get_price():
    r = requests.get(PRICE_URL, params=PARAMS, timeout=10)
    r.raise_for_status()
    return float(r.json()["ethereum"]["usd"])


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELELEGRAM_CHAT_ID, "text": message}
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "reference_price": None,  # prix de référence pour calculer la baisse
        "alerted": False          # a-t-on déjà notifié pour la baisse en cours ?
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def main():
    state = load_state()

    price = get_price()

    # Init référence au premier run
    if state["reference_price"] is None:
        state["reference_price"] = price
        state["alerted"] = False
        save_state(state)
        print(f"Init reference_price={price}")
        return

    reference = state["reference_price"]
    drop = (reference - price) / reference  # ex: 0.05 = -5%

    print(f"Référence : {reference}")
    print(f"Prix actuel : {price}")
    print(f"Baisse : {drop*100:.2f}%")
    print(f"Alerted : {state['alerted']}")

    # 1) Condition de baisse déclenchante
    if drop >= DROP_THRESHOLD:
        if not state["alerted"]:
            msg = (
                "🚨 Alerte baisse ETH\n"
                f"Prix: {price} USD\n"
                f"Baisse: {drop*100:.2f}%\n"
                f"Réf: {reference}"
            )
            # Envoie 1 seule fois
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
            resp = requests.post(url, json=payload, timeout=10)
            print("Telegram:", resp.status_code, resp.text)

            state["alerted"] = True
            save_state(state)
        else:
            print("Déjà alerté pour cette baisse -> pas de nouvelle notif.")

    # 2) Réarmement quand la baisse n'est plus là (ou beaucoup moins forte)
    # Ici on réarme si la baisse redevient < 2% (REARM_THRESHOLD)
    elif drop < REARM_THRESHOLD:
        # On réarme + on met à jour le prix de référence au niveau actuel
        # (comme ça une nouvelle baisse repartira de ce nouveau niveau)
        if state["alerted"]:
            print("Réarmement (la baisse est retombée) -> alerted=False")
        state["alerted"] = False
        state["reference_price"] = price
        save_state(state)
    else:
        # zone intermédiaire: pas assez bas pour alerter, pas assez haut pour réarmer
        save_state(state)


if __name__ == "__main__":
    main()
