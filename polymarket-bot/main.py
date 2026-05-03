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
balance_history = [INITIAL_BALANCE]
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
            <h3>Saldo: {{ current_balance }} USD</h3>
            <canvas id="balanceChart"></canvas>
        </div>
        <div class="card">
            <h3>Dziennik Działań</h3>
            {% for log in logs %}<div style="font-size: 12px; margin-bottom: 5px; color: {{ '#4ade80' if log.type == 'trade' else 'white' }}">{{ log.msg }}</div>{% endfor %}
        </div>
    </div>
    <script>
        const ctx = document.getElementById('balanceChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ range(balance_history|length)|list }},
                datasets: [{ label: 'Saldo', data: {{ balance_history }}, borderColor: '#38bdf8', fill: true }]
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE, logs=logs, balance_history=balance_history, current_balance=current_balance)

def trading_loop():
    global current_balance
    add_log("System AI aktywny. Zarządzanie budżetem włączone.", "info")
    
    while True:
        try:
            raw_data = clob.get_markets()
            markets = raw_data.get('data', []) if isinstance(raw_data, dict) else []
            
            # Analiza tylko 3 rynków na cykl, aby nie przeciążyć AI
            for market in markets[:3]:
                question = market.get('question', 'Rynek')
                price = market.get('last_trade_price', '0.50')
                
                # Ulepszony prompt dla AI
                prompt = f"""
                Jesteś profesjonalnym traderem. Masz budżet {current_balance} USD.
                Rynek: {question}. Cena: {price}. 
                Czy to okazja inwestycyjna? 
                Jeśli tak, napisz 'KUP' i powód. Jeśli nie, napisz 'CZEKAJ'.
                """
                
                res = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}], 
                    model="llama-3.3-70b-versatile"
                )
                decision = res.choices[0].message.content
                
                # Logika "Bezpiecznik Budżetowy"
                if "KUP" in decision.upper():
                    if current_balance >= 10:
                        current_balance -= 10
                        balance_history.append(current_balance)
                        add_log(f"KUPIONO: {question[:15]}...", "trade")
                    else:
                        add_log(f"ODMOWA (brak środków): {question[:15]}", "error")
                else:
                    add_log(f"CZEKAM: {question[:15]}...", "info")
                
                stats["total_trades"] += 1
            
            add_log("Cykl analizy zakończony. Czekam 60s...", "info")
            time.sleep(60)
            
        except Exception as e:
            add_log(f"BŁĄD: {str(e)}", "error")
            time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
