import os
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string
from groq import Groq
from py_clob_client.client import ClobClient
from config import GROQ_API_KEY, INITIAL_BALANCE

app = Flask(__name__)
logs = []
stats = {"total_trades": 0, "last_update": "Brak"}

# --- Konfiguracja API ---
# Używamy publicznego hosta
clob = ClobClient("https://clob.polymarket.com")

def add_log(message, type="info"):
    now = datetime.now().strftime("%H:%M:%S")
    logs.insert(0, {"time": now, "msg": message, "type": type})
    if len(logs) > 50: logs.pop()

# --- Szablon Dashboardu ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Polymarket AI Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; padding: 20px; }
        .log-entry { margin-bottom: 5px; font-family: monospace; border-bottom: 1px solid #334155; }
        .trade { color: #4ade80; }
        .error { color: #f87171; }
    </style>
</head>
<body>
    <h1>Polymarket AI Bot Live</h1>
    <p>Ostatnia aktualizacja: {{ stats.last_update }} | Analizy: {{ stats.total_trades }}</p>
    <div class="log-container">
        {% for log in logs %}
        <div class="log-entry {{ log.type }}">{{ log.msg }}</div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE, logs=logs, stats=stats)

def trading_loop():
    client = Groq(api_key=GROQ_API_KEY)
    add_log("System startuje...")
    
    while True:
        try:
            # Pobranie rynków
            # Niektóre wersje biblioteki zwracają słownik zamiast listy
            raw_data = clob.get_markets()
            
            # Bezpieczne sprawdzanie danych
            if isinstance(raw_data, list):
                markets = raw_data[:5]
            else:
                markets = []
                add_log(f"Debug: API zwróciło typ {type(raw_data)} zamiast listy.", "error")

            if not markets:
                add_log("Brak danych z API Polymarket.", "error")
            
            for market in markets:
                market_name = market.get('question', 'Brak nazwy')
                price = market.get('last_trade_price', 0)
                
                prompt = f"Rynek: {market_name}. Cena YES: {price}. Czy trend jest wzrostowy? Odpowiedz: KUP/CZEKAJ i podaj krótkie uzasadnienie."
                
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                
                decision = completion.choices[0].message.content
                stats["total_trades"] += 1
                stats["last_update"] = datetime.now().strftime("%H:%M:%S")
                
                if "KUP" in decision.upper():
                    add_log(f"DECYZJA KUP: {market_name[:20]}...", "trade")
                
            add_log("Cykl zakończony.")
            
        except Exception as e:
            add_log(f"BŁĄD: {str(e)}", "error")
        
        time.sleep(60) # Czekamy minutę między cyklami

if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
