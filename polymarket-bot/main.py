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
    </style>
</head>
<body>
    <h1>Polymarket AI Bot Live</h1>
    <p>Ostatnia aktualizacja: {{ stats.last_update }} | Transakcje: {{ stats.total_trades }}</p>
    <div class="log-container">
        {% for log in logs %}
        <div class="log-entry">[{{ log.time }}] {{ log.msg }}</div>
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
    add_log("System uruchomiony. Łączę z Polymarket API...")
    
    while True:
        try:
            markets = clob.get_markets()[:5]
            for market in markets:
                market_name = market.get('question')
                price = market.get('last_trade_price')
                prompt = f"Rynek: {market_name}. Cena YES: {price}. Czy trend jest wzrostowy? Odpowiedz: KUP/CZEKAJ i podaj krótkie uzasadnienie."
                
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                
                decision = completion.choices[0].message.content
                stats["total_trades"] += 1
                stats["last_update"] = datetime.now().strftime("%H:%M:%S")
                
                if "KUP" in decision.upper():
                    add_log(f"SYMULACJA: Decyzja KUP dla '{market_name[:30]}...'", "trade")
                else:
                    add_log(f"Analiza: {market_name[:20]}... (CZEKAJ)", "info")
            
            add_log("Cykl zakończony. Czekam 30s...")
            
        except Exception as e:
            add_log(f"BŁĄD API: {str(e)}", "error")
        
        time.sleep(30)

if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
