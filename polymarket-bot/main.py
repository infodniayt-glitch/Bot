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
stats = {"total_trades": 0, "last_update": "Brak", "status": "Inicjalizacja..."}

# Konfiguracja klienta Polymarket
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
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: white; padding: 20px; }
        .log-container { background: #1e293b; padding: 15px; border-radius: 8px; }
        .log-entry { margin-bottom: 5px; font-family: monospace; border-bottom: 1px solid #334155; padding: 4px 0; }
        .info { color: #94a3b8; }
        .trade { color: #4ade80; }
        .error { color: #f87171; }
        .header { display: flex; justify-content: space-between; align-items: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Polymarket AI Bot Live</h1>
        <div>Status: <b>{{ stats.status }}</b></div>
    </div>
    <p>Ostatnia aktualizacja: {{ stats.last_update }} | Analizy: {{ stats.total_trades }}</p>
    <div class="log-container">
        {% for log in logs %}
        <div class="log-entry {{ log.type }}">[{{ log.time }}] {{ log.msg }}</div>
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
    add_log("System startuje. Pobieram dane rynkowe...", "info")
    
    while True:
        try:
            raw_data = clob.get_markets()
            
            # Pobieramy listę rynków z klucza 'data'
            markets = raw_data.get('data', []) if isinstance(raw_data, dict) else []
            
            if not markets:
                add_log("Brak rynków w danych API.", "error")
            else:
                add_log(f"Znaleziono {len(markets)} rynków. Analizuję...", "info")
                
                # Przetwarzamy pierwsze 3 rynki
                for market in markets[:3]:
                    question = market.get('question', 'Brak pytania')
                    # W danych Polymarketu cena często jest w 'last_trade_price' 
                    # lub wewnątrz obiektów 'clob_pair'
                    price = market.get('last_trade_price', 'brak ceny')
                    
                    add_log(f"Analiza: {question[:30]}... (Cena: {price})", "info")
                    
                    # Tutaj możesz dodać wywołanie do Groq AI
                    stats["total_trades"] += 1

            stats["last_update"] = datetime.now().strftime("%H:%M:%S")
            add_log("Cykl zakończony. Czekam 60s...", "info")
            
        except Exception as e:
            add_log(f"BŁĄD: {str(e)}", "error")
        
        time.sleep(60)
if __name__ == "__main__":
    # Uruchomienie bota w tle
    threading.Thread(target=trading_loop, daemon=True).start()
    # Uruchomienie serwera Flask
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
