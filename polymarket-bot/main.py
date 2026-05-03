import os
import time
import threading
import json
from datetime import datetime
from flask import Flask, render_template_string
from groq import Groq
from py_clob_client.client import ClobClient
from config import GROQ_API_KEY, INITIAL_BALANCE

app = Flask(__name__)
logs = []
balance_history = [INITIAL_BALANCE] # Historia salda do wykresu
current_balance = INITIAL_BALANCE
stats = {"total_trades": 0, "status": "Inicjalizacja..."}

clob = ClobClient("https://clob.polymarket.com")
groq_client = Groq(api_key=GROQ_API_KEY)

def add_log(message, type="info"):
    now = datetime.now().strftime("%H:%M:%S")
    logs.insert(0, {"time": now, "msg": message, "type": type})
    if len(logs) > 20: logs.pop()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Polymarket AI Pro</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; padding: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 10px; }
    </style>
</head>
<body>
    <h1>Polymarket AI Dashboard</h1>
    <div class="grid">
        <div class="card">
            <h3>Wykres Salda</h3>
            <canvas id="balanceChart"></canvas>
        </div>
        <div class="card">
            <h3>Logi (Ostatnie 20)</h3>
            {% for log in logs %}<div style="font-size: 12px; margin-bottom: 5px;">{{ log.msg }}</div>{% endfor %}
        </div>
    </div>
    <script>
        const ctx = document.getElementById('balanceChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ range(balance_history|length)|list }},
                datasets: [{ label: 'Saldo (USD)', data: {{ balance_history }}, borderColor: '#4ade80', tension: 0.1 }]
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE, logs=logs, balance_history=balance_history)

def trading_loop():
    global current_balance
    while True:
        try:
            raw_data = clob.get_markets()
            markets = raw_data.get('data', []) if isinstance(raw_data, dict) else []
            
            # Analizujemy Top 10 rynków (bezpieczny kompromis)
            for market in markets[:10]:
                question = market.get('question', 'Rynek')
                price = market.get('last_trade_price', '0.50')
                
                # Symulacja decyzji AI
                prompt = f"Rynek: {question}. Cena: {price}. Czy kupić? Odpowiedz tylko: KUP, SPRZEDAJ lub CZEKAJ."
                res = groq_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                decision = res.choices[0].message.content
                
                # Prosta logika symulacji portfela
                if "KUP" in decision:
                    current_balance -= 10 # Symulacja kosztu
                    balance_history.append(current_balance)
                    add_log(f"KUP: {question[:20]}", "trade")
                
                stats["total_trades"] += 1
            
            add_log("Cykl zakończony. Czekam 60s...", "info")
            time.sleep(60)
            
        except Exception as e:
            add_log(f"Błąd: {e}", "error")
            time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
