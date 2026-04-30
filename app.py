import os
import requests
import random
from datetime import datetime
from flask import Flask, render_template, jsonify
from groq import Groq
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
app = Flask(__name__)

# Stan globalny
balance = 1000.0
trades = []
current_bot_status = "Oczekiwanie..."
last_update = "--:--"

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_polymarket_data():
    try:
        url = "https://gamma-api.polymarket.com/events?active=true"
        response = requests.get(url, timeout=10)
        data = response.json()
        if not data: return "Brak rynków"
        event = random.choice(data)
        return event.get('title', 'Nieznane')
    except Exception as e:
        return f"Błąd sieci"

def perform_trade_logic():
    global balance, current_bot_status, last_update
    
    last_update = datetime.now().strftime("%H:%M:%S")
    current_bot_status = "Analizowanie rynku..."
    market = get_polymarket_data()
    
    try:
        prompt = f"Analizuj rynek: {market}. Czy to okazja na BUY czy HOLD? Odpowiedz krótko."
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192"
        )
        decision = response.choices[0].message.content
        
        if "BUY" in decision.upper() and balance > 10:
            balance -= 10.0
            # Dodajemy log z czasem
            trades.append({"time": last_update, "event": market[:30], "action": "BUY"})
            current_bot_status = "Kupiono!"
        else:
            current_bot_status = "Czekam..."
    except Exception as e:
        current_bot_status = f"Błąd AI"

# Scheduler
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=perform_trade_logic, trigger="interval", seconds=60, next_run_time=datetime.now())
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    return jsonify({
        "balance": round(balance, 2), 
        "trades": trades[::-1], # Odwracamy listę (najnowsze na górze)
        "status": current_bot_status,
        "last_update": last_update
    })

if __name__ == '__main__':
    app.run()
