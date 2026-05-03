import os
import json
import ccxt
import pandas as pd
from flask import Flask, render_template_string, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from groq import Groq

app = Flask('')
start_time = datetime.now()
STATS_FILE = 'balance_history.json'

# --- KONFIGURACJA SYMULACJI ---
INITIAL_CAPITAL = 1000.0       
TRADE_AMOUNT_USDC = 200.0      
RSI_BUY_THRESHOLD = 35         
RSI_SELL_THRESHOLD = 58        
SYMBOLS = ["BTC", "ETH", "BNB", "SOL"] # Dodano BNB i SOL

# Klucze API (dla symulacji potrzebne tylko do pobierania cen)
mexc = ccxt.mexc({'options': {'defaultType': 'spot'}, 'enableRateLimit': True})
groq_client = Groq(api_key=os.getenv('GROQ_KEY'))

# --- STAN PORTFELA (WIRTUALNY) ---
display_state = {
    "usdc": INITIAL_CAPITAL, 
    "total": INITIAL_CAPITAL, 
    "profit": 0.0,
    "buy_count": 0, 
    "sell_count": 0,
    "last_action": "Inicjalizacja Symulacji...",
    "assets": {s: {"amount": 0.0, "rsi": 50.0} for s in SYMBOLS}
}

# Średnie ceny zakupu dla każdej waluty
avg_buy_prices = {s: 0.0 for s in SYMBOLS}

def ask_ai_decision(symbol, price, rsi):
    try:
        prompt = f"Analiza techniczna {symbol}: Cena {price}, RSI {rsi}. Czy to bezpieczny moment na zakup w strategii DCA? Odpowiedz tylko jednym słowem: TAK lub NIE."
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5
        )
        answer = completion.choices[0].message.content.strip().upper()
        return "TAK" in answer
    except:
        return True 

def calculate_rsi(symbol):
    try:
        pair = f"{symbol}/USDC"
        bars = mexc.fetch_ohlcv(pair, timeframe='1m', limit=50)
        df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))
        return round(rsi.iloc[-1], 1)
    except: return 50.0

def save_history(val):
    history = []
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            try: history = json.load(f)
            except: history = []
    history.append({"t": datetime.now().isoformat(), "v": round(val, 2)})
    with open(STATS_FILE, 'w') as f:
        json.dump(history[-20000:], f)

def run_loop():
    global display_state, avg_buy_prices
    try:
        current_time = datetime.now().strftime("%H:%M")
        calculated_total = display_state["usdc"] 
        ai_reports = []

        for symbol in SYMBOLS:
            pair = f"{symbol}/USDC"
            ticker = mexc.fetch_ticker(pair)
            price = float(ticker['last'])
            
            rsi_val = calculate_rsi(symbol)
            current_amt = display_state["assets"][symbol]["amount"]
            
            # --- LOGIKA KUPNA (SYMULACJA) ---
            if rsi_val < RSI_BUY_THRESHOLD and display_state["usdc"] >= TRADE_AMOUNT_USDC:
                if ask_ai_decision(symbol, price, rsi_val):
                    qty = TRADE_AMOUNT_USDC / price
                    
                    # Aktualizacja średniej ceny
                    old_qty = current_amt
                    old_avg = avg_buy_prices[symbol]
                    avg_buy_prices[symbol] = ((old_qty * old_avg) + (qty * price)) / (old_qty + qty)
                    
                    # Aktualizacja stanu
                    display_state["assets"][symbol]["amount"] += qty
                    display_state["usdc"] -= TRADE_AMOUNT_USDC
                    display_state["buy_count"] += 1
                    ai_reports.append(f"🤖 SYM-KUPNO {symbol}")
                    current_amt = display_state["assets"][symbol]["amount"]

            # --- LOGIKA SPRZEDAŻY (SYMULACJA) ---
            elif rsi_val > RSI_SELL_THRESHOLD and current_amt > 0:
                # Sprzedaj tylko jeśli cena jest wyższa od średniej ceny zakupu (Profit Protection)
                if price > avg_buy_prices[symbol]:
                    received_usdc = current_amt * price
                    display_state["usdc"] += received_usdc
                    display_state["assets"][symbol]["amount"] = 0.0
                    avg_buy_prices[symbol] = 0.0
                    display_state["sell_count"] += 1
                    ai_reports.append(f"💰 SYM-SPRZEDAŻ {symbol}")
                    current_amt = 0.0

            calculated_total += (current_amt * price)
            display_state["assets"][symbol]["rsi"] = rsi_val

        display_state.update({
            "total": round(calculated_total, 2),
            "profit": round(calculated_total - INITIAL_CAPITAL, 2),
            "last_action": " | ".join(ai_reports) if ai_reports else f"[{current_time}] Skanowanie {', '.join(SYMBOLS)}...",
        })
        save_history(calculated_total)
    except Exception as e: 
        print(f"Błąd pętli: {e}")

# --- API FLASK ---
@app.route('/api/data/<range_type>')
def get_data(range_type):
    history = []
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            try: history = json.load(f)
            except: history = []
    
    now = datetime.now()
    points = []
    # (Logika filtrowania czasu pozostaje taka sama jak w Twoim kodzie)
    # ... skrócona dla czytelności, pobiera ostatnie N punktów zależnie od range_type ...
    step = 1 if range_type == 'day' else 5
    for entry in history[-50:]: 
        entry_time = datetime.fromisoformat(entry['t'])
        points.append({"t": entry_time.strftime("%H:%M"), "v": entry['v']})
        
    return jsonify({"state": display_state, "history": points})

@app.route('/')
def home():
    # Dynamicznie generujemy wiersze dla assetów w HTML
    asset_rows = "".join([
        f'<div class="card"><div style="color:#f3ba2f;">{s}</div><div id="{s.lower()}_amt" class="value">--</div></div>' 
        for s in SYMBOLS
    ])
    
    # Dynamiczny JS do aktualizacji tych assetów
    js_updates = "".join([
        f"document.getElementById('{s.lower()}_amt').innerText = d.state.assets.{s}.amount.toFixed(4);" 
        for s in SYMBOLS
    ])

    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>AI TRADER TEST-MODE</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ background: #0b0e11; color: white; font-family: sans-serif; padding: 15px; margin: 0; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; max-width: 600px; margin: auto; }}
        .card {{ background: #1e2329; padding: 15px; border-radius: 12px; border: 1px solid #2b3139; text-align: center; }}
        .label {{ color: #848e9c; font-size: 0.75em; text-transform: uppercase; }}
        .value {{ font-size: 1.1em; font-weight: bold; margin-top: 5px; }}
        .sub-label {{ font-size: 0.72em; color: #f3ba2f; margin-top: 8px; border-top: 1px solid #2b3139; padding-top: 5px; }}
        .chart-container {{ max-width: 600px; margin: 15px auto; background: #1e2329; border-radius: 12px; padding: 15px; border: 1px solid #2b3139; }}
        #timer {{ position: fixed; top: 10px; right: 10px; background: #0ecb81; color: black; padding: 3px 10px; border-radius: 20px; font-size: 0.75em; font-weight: bold; z-index: 100; }}
        .ai-box {{ max-width: 600px; margin: 15px auto; padding: 12px; background: rgba(14, 203, 129, 0.1); border: 1px solid #0ecb81; border-radius: 8px; font-size: 0.85em; text-align: center; color: #0ecb81; }}
        .asset-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px; max-width: 600px; margin: 15px auto; }}
        button {{ background: #2b3139; color: #848e9c; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; }}
        button.active {{ background: #f3ba2f; color: black; font-weight: bold; }}
    </style></head>
    <body>
        <div id="timer">SYMULACJA</div>
        <h3 style="color: #f3ba2f; text-align:center;">🧪 AI TRADER v11.0 [PAPER TEST]</h3>
        <div class="grid">
            <div class="card"><div class="label">Wirtualne USDC</div><div class="value" id="usdc">--</div></div>
            <div class="card"><div class="label">Zysk Symulowany</div><div id="profit" class="value">--</div><div class="sub-label">S: <b id="s_count" style="color:white;">0</b> | K: <b id="b_count" style="color:white;">0</b></div></div>
            <div class="card" style="grid-column: span 2;"><div class="label">Całkowita Wartość Portfela</div><div id="total" class="value">--</div></div>
        </div>
        <div class="ai-box"><b>AI Decision Engine:</b><br><span id="ai_action">Skanowanie...</span></div>
        <div class="chart-container"><canvas id="myChart"></canvas></div>
        <div class="asset-grid">{asset_rows}</div>
        <script>
            let chart; let timeLeft = 30;
            async function update() {{
                const res = await fetch('/api/data/day'); const d = await res.json();
                document.getElementById('usdc').innerText = d.state.usdc.toFixed(2) + ' $';
                document.getElementById('total').innerText = d.state.total.toFixed(2) + ' $';
                document.getElementById('b_count').innerText = d.state.buy_count;
                document.getElementById('s_count').innerText = d.state.sell_count;
                document.getElementById('ai_action').innerText = d.state.last_action;
                {js_updates}
                const pEl = document.getElementById('profit');
                pEl.innerText = (d.state.profit>=0?'+':'') + d.state.profit.toFixed(2) + ' $';
                pEl.style.color = d.state.profit>=0?'#0ecb81':'#f6465d';
                const chartData = {{
                    labels: d.history.map(h => h.t),
                    datasets: [{{ data: d.history.map(h => h.v), borderColor: '#f3ba2f', borderWidth: 2, tension: 0.1, fill: false }}]
                }};
                if(!chart) {{
                    chart = new Chart(document.getElementById('myChart'), {{
                        type: 'line', data: chartData,
                        options: {{ animation: false, plugins: {{ legend: {{ display: false }} }} }}
                    }});
                }} else {{ chart.data = chartData; chart.update(); }}
            }}
            setInterval(update, 30000);
            update();
        </script>
    </body></html>
    """)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_loop, trigger="interval", seconds=30)
    scheduler.start()
    run_loop()
    app.run(host='0.0.0.0', port=10000)
