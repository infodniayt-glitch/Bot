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

# Konfiguracja
balance = 1000.0
trades = []
current_bot_status = f"Uruchomiono o {datetime.now().strftime('%H:%M:%S')}"

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_polymarket_data():
    # Dodano timeout=5, żeby nie czekał w nieskończoność
    url = "https://gamma-api.polymarket.com/events?active=true"
    response = requests.get(url, timeout=5)
    data = response.json()
    if not data: return None
    event = random.choice(data)
    return event.get('title', 'Nieznane wydarzenie')

def perform_trade_logic():
    global current_bot_status, balance
    
    # Zapisujemy, że bot PRÓBUJE pracować
    start_time = datetime.now().strftime('%H:%M:%S')
    current_bot_status = f"Analizuję rynek... ({start_time})"
    
    try:
        # 1. Pobieranie danych
        market = get_polymarket_data()
        if not market:
            current_bot_status = "Błąd: Brak danych z Polymarket"
            return

        # 2. Zapytanie do AI
        prompt = f"Analizuj rynek: {market}. Czy to okazja na BUY czy HOLD? Odpowiedz tylko BUY lub HOLD."
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192"
        )
        decision = response.choices[0].message.content
        
        # 3. Logika transakcji
        if "BUY" in decision.upper() and balance > 10:
            balance -= 10.0
            trades.append({"event": market, "action": "BUY"})
            current_bot_status = f"Kupiono! Ostatnio: {start_time}"
        else:
            current_bot_status = f"Czekam... Ostatnia próba: {start_time}"
            
    except Exception as e:
        # TO JEST KLUCZOWE: Jeśli cokolwiek wywali błąd, zobaczymy go na stronie
        current_bot_status = f"BŁĄD: {str(e)[:30]}"

# Scheduler
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=perform_trade_logic, trigger="interval", seconds=60)
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
