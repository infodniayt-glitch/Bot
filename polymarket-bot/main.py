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
stats = {
    "balance": INITIAL_BALANCE,
    "total_trades": 0,
    "last_update": "Brak",
    "status": "Inicjalizacja..."
}

# Inicjalizacja klientów
clob = ClobClient("https://clob.polymarket.com")
groq_client = Groq(api_key=GROQ_API_KEY)

def add_log(message, type="info"):
    now = datetime.now().strftime("%H:%M:%S")
    logs.insert(0, {"time": now, "msg": message, "type": type})
    if len(logs) > 15: logs.pop()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Polymarket AI Bot</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; padding: 20px; }
        .container { max-width: 800px; margin: auto; }
        .card { background: #1e293b; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .log-entry { font-family: monospace; padding: 8px; border-bottom: 1px solid #334155; }
        .trade { color: #4ade80; }
        .error { color: #f87171; }
        h1 { color: #38bdf8; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Polymarket AI Bot</h1>
        <div class="card">
            <p><strong>Saldo:</strong> {{ stats.balance }} | <strong>Analizy:</strong> {{ stats.total_trades }}</p>
            <p><strong>Status:</strong> {{ stats.status }} | <strong>Aktualizacja:</strong> {{ stats.last_update }}</p>
        </div>
        <div class="card">
            <h3>Dziennik Działań</h3>
            {% for log in logs %}
            <div class="log-entry {{ log.type }}">[{{ log.time }}] {{ log.msg }}</div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE, logs=logs, stats=stats)

def trading_loop():
    add_log("System startuje. Łączę z rynkiem...", "info")
    
    while True:
        try:
            # 1. Pobranie rynków
            raw_data = clob.get_markets()
            markets = raw_data.get('data', []) if isinstance(raw_data, dict) else []
            
            if markets:
                # Analizujemy pierwszy rynek
                market = markets[0]
                question = market.get('question', 'Nieznany rynek')
                price = market.get('last_trade_price', '0.50')
                
                add_log(f"Analizuję rynek: {question[:30]}...", "info")
                
                # 2. Zapytanie do Groq AI
                prompt = f"Rynek: {question}. Cena: {price}. Czy to okazja? Odpowiedz bardzo krótko (KUP/CZEKAJ + powód)."
                chat_completion = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                
                decision = chat_completion.choices[0].message.content
                stats["total_trades"] += 1
                stats["status"] = "Online"
                add_log(f"DECYZJA: {decision}", "trade")
            
            stats["last_update"] = datetime.now().strftime("%H:%M:%S")
            
        except Exception as e:
            stats["status"] = "BŁĄD"
            add_log(f"BŁĄD: {str(e)}", "error")
        
        time.sleep(60) # Czekaj minutę

if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
