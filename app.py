import os
import requests
import random
from flask import Flask, render_template, jsonify
from groq import Groq
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
app = Flask(__name__)

# Konfiguracja
balance = 1000.0
trades = []
current_bot_status = "Inicjalizacja..."
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_polymarket_data():
    try:
        # Pobieramy aktywne rynki z API Polymarket
        url = "https://gamma-api.polymarket.com/events?active=true"
        response = requests.get(url, timeout=10)
        events = response.json()
        
        # Wybieramy jedno losowe aktywne wydarzenie
        event = random.choice(events)
        title = event.get('title', 'Unknown Market')
        # Polymarket przechowuje kursy w 'markets' -> 'prices' (uproszczenie)
        return f"Rynek: {title}"
    except Exception as e:
        return f"Błąd pobierania danych: {str(e)}"

def perform_trade_logic():
    global balance, current_bot_status
    
    current_bot_status = "Pobieram dane z Polymarket..."
    market_data = get_polymarket_data()
    
    if "Błąd" in market_data:
        current_bot_status = market_data
        return

    current_bot_status = f"Analizuję: {market_data[:30]}..."
    
    try:
        # Analiza AI
        prompt = f"Analizuj rynek Polymarket: {market_data}. Czy widzisz okazję inwestycyjną? Czy kupić (BUY) czy czekać (HOLD)? Odpowiedz tylko BUY lub HOLD."
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192"
        )
        decision = response.choices[0].message.content
        
        if "BUY" in decision.upper() and balance > 10:
            current_bot_status = "Wykonywanie transakcji..."
            balance -= 10.0
            trades.append({"event": market_data, "action": "BUY", "status": "Live Data"})
        else:
            current_bot_status = "Czekam na lepsze okazje..."
            
    except Exception as e:
        current_bot_status = f"Błąd AI: {str(e)}"

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=perform_trade_logic, trigger="interval", minutes=2) # rzadziej, żeby nie zbanowali API
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    return jsonify({
        "balance": round(balance, 2), 
        "trades": trades[-10:], 
        "status": current_bot_status
    })

if __name__ == '__main__':
    app.run(port=5000)
