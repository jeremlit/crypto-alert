import requests
import json
import os

STATE_FILE = "state.json"

# ---- PARAMÈTRES STRATÉGIE ----
DROP_THRESHOLD = 0.05     # -5 %
REARM_THRESHOLD = 0.02    # réarmement si la baisse < -2 %
RSI_PERIOD = 14
RSI_THRESHOLD = 40        # RSI 4H max pour autoriser une alerte

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ---- COINGECKO ----
PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"
PRICE_PARAMS = {"ids": "ethereum", "vs_currencies": "usd"}

OHLC_URL = "https://api.coingecko.com/api/v3/coins/ethereum/ohlc"
OHLC_PARAMS = {"vs_currency": "usd", "days": 14}


# ---------- UTILITAIRES ----------
def get_price():
    r = requests.get(PRICE_URL, params=PRICE_PARAMS, timeout=10)
    r.raise_for_status()
    return float(r.json()["ethereum"]["usd"])


def get_rsi_4h(period=14):
    r = requests.get(OHLC_URL, params=OHLC_PARAMS, timeout=10)
    r.raise_for_status()
    ohlc = r.json()

    closes = [candle[4] for candle in ohlc]  # close prices

    if len(closes) < period + 1:
        return None

    gains, losses = [], []
    for i in range(1, period + 1):
        delta = closes[-i] - closes[-i - 1]
        if delta >= 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period if losses else 0.00001

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    r = requests.post(url, json=payload, timeout=10)
    print("Telegram:", r.status_code, r.text)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"reference_price": None, "alerted": False}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ---------- LOGIQUE PRINCIPALE ----------
def main():
    state = load_state()

    price = get_price()
    rsi_4h = get_rsi_4h()

    print(f"Prix actuel : {price}")
    print(f"RSI 4H : {rsi_4h}")

    # Init
    if state["reference_price"] is None:
        state["reference_price"] = price
        state["alerted"] = False
        save_state(state)
        print("Init state.")
        return

    reference = state["reference_price"]
    drop = (reference - price) / reference

    print(f"Référence : {reference}")
    print(f"Baisse : {drop*100:.2f}%")
    print(f"Alerted : {state['alerted']}")

    # ---- CONDITION D'ALERTE ----
    if (
        drop >= DROP_THRESHOLD
        and rsi_4h is not None
        and rsi_4h <= RSI_THRESHOLD
        and not state["alerted"]
    ):
        send_telegram(
            "🚨 SETUP ETH VALIDE\n"
            f"Prix : {price} USD\n"
            f"Baisse : {drop*100:.2f}%\n"
            f"RSI 4H : {rsi_4h}"
        )
        state["alerted"] = True
        save_state(state)
        return

    # ---- RÉARMEMENT ----
    if drop < REARM_THRESHOLD:
        state["alerted"] = False
        state["reference_price"] = price
        save_state(state)
        print("Réarmement effectué.")
        return

    save_state(state)


if __name__ == "__main__":
    main()
