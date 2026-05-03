import os
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string
from groq import Groq
from config import GROQ_API_KEY, INITIAL_BALANCE

# --- Konfiguracja i Pamięć Bota ---
app = Flask(__name__)
logs = []  # Lista przechowująca historię działań
stats = {
    "balance": INITIAL_BALANCE,
    "total_trades": 0,
    "last_update": "Brak"
}

def add_log(message, type="info"):
    """Dodaje wpis do logów dashboardu"""
    now = datetime.now().strftime("%H:%M:%S")
    logs.insert(0, {"time": now, "msg": message, "type": type})
    if len(logs) > 10:  # Trzymamy tylko 10 ostatnich wpisów
        logs.pop()

# --- Dashboard UI (HTML/CSS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Polymarket AI Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }
        .stat-card { background: #1e293b; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #334155; }
        .stat-card h3 { margin: 0; color: #94a3b8; font-size: 14px; text-transform: uppercase; }
        .stat-card p { margin: 10px 0 0; font-size: 24px; font-weight: bold; color: #38bdf8; }
        .log-container { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
        .log-entry { padding: 10px; border-bottom: 1px solid #334155; font-family: monospace; font-size: 14px; }
        .log-entry:last-child { border: none; }
        .time { color: #64748b; margin-right: 15px; }
        .type-info { color: #38bdf8; }
        .type-trade { color: #4ade80; }
        .type-error { color: #f87171; }
        .badge { background: #4ade80; color: #064e3b; padding: 4px 10px; border-radius: 20px; font-size: 12px; }
    </style>
    <meta http-equiv="refresh" content="30">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Polymarket AI Bot <span class="badge">Live</span></h1>
            <p>Ostatnia aktualizacja: {{ stats.last_update }}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Saldo (Paper)</h3>
                <p>${{ stats.balance }}</p>
            </div>
            <div class="stat-card">
                <h3>Wykonane Analizy</h3>
                <p>{{ stats.total_trades }}</p>
            </div>
            <div class="stat-card">
                <h3>Status AI</h3>
                <p style="color: #4ade80;">Online</p>
            </div>
        </div>

        <h3>Dziennik Działań (Logi)</h3>
        <div class="log-container">
            {% for log in logs %}
            <div class="log-entry">
                <span class="time">[{{ log.time }}]</span>
                <span class="type-{{ log.type }}">{{ log.msg }}</span>
            </div>
            {% endfor %}
            {% if not logs %}
            <p style="text-align: center; color: #64748b;">Oczekiwanie na pierwsze dane...</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE, logs=logs, stats=stats)

# --- Pętla Tradingowa ---
def trading_loop():
    client = Groq(api_key=GROQ_API_KEY)
    add_log("System zainicjowany. Start pętli tradingowej.")
    
    while True:
        try:
            # Symulacja danych rynkowych
            mock_market = {"name": "Czy BTC przebije 100k w tym tygodniu?", "price_yes": 0.62}
            add_log(f"Analizuję rynek: {mock_market['name']}", "info")
            
            prompt = f"Analizuj rynek: {mock_market}. Czy warto kupić pozycję YES? Odpowiedz krótko: YES/NO i dlaczego."
            
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            
            decision = completion.choices[0].message.content
            stats["total_trades"] += 1
            stats["last_update"] = datetime.now().strftime("%H:%M:%S")
            
            if "YES" in decision.upper():
                add_log(f"DECYZJA: KUPUJĘ (Paper Trade). Powód: {decision[:60]}...", "trade")
            else:
                add_log(f"DECYZJA: CZEKAM. AI mówi: {decision[:60]}...", "info")
                
        except Exception as e:
            add_log(f"BŁĄD: {str(e)}", "error")
        
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
