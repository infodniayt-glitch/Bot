import os
import requests
import random
from datetime import datetime  # <--- Dodaj to!
from flask import Flask, render_template, jsonify
from groq import Groq
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
app = Flask(__name__)

# Stan globalny
balance = 1000.0
trades = []
current_bot_status = "System uruchomiony, startuję..."

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_polymarket_data():
    try:
        url = "https://gamma-api.polymarket.com/events?active=true"
        response = requests.get(url, timeout=10)
        data = response.json()
        if not data: return "Brak aktywnych rynków"
        event = random.choice(data)
        return event.get('title', 'Nieznane wydarzenie')
    except Exception as e:
        return f"Błąd: {str(e)}"

def perform_trade_logic():
    global balance, current_bot_status
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
            trades.append({"event": market, "action": "BUY"})
            current_bot_status = f"Kupiono! ({market[:15]}...)"
        else:
            current_bot_status = "Czekam na okazję..."
    except Exception as e:
        current_bot_status = f"Błąd AI: {str(e)}"

# AUTO-START z natychmiastowym wywołaniem
scheduler = BackgroundScheduler(daemon=True)
# next_run_time=datetime.now() wymusza start TERAZ
scheduler.add_job(func=perform_trade_logic, trigger="interval", seconds=60, next_run_time=datetime.now())
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    return jsonify({
        "balance": round(balance, 2), 
        "trades": trades[-5:], 
        "status": current_bot_status
    })

if __name__ == '__main__':
    app.run()
