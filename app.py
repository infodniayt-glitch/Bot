import os
import random
from flask import Flask, render_template, jsonify
from groq import Groq
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
app = Flask(__name__)

# Konfiguracja początkowa
balance = 1000.0
trades = []
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def perform_trade_logic():
    global balance
    # Symulacja danych rynkowych
    markets = ["Bitcoin > 100k", "Wybory USA", "Eksploracja Marsa", "Cena Złota > 2500"]
    event = random.choice(markets)
    odds = random.uniform(0.1, 0.9)
    
    # Analiza AI
    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": f"Analizuj rynek: '{event}' z szansą {odds:.2f}. Jesteś botem tradingowym. Czy kupić (BUY) czy ignorować (HOLD)? Odpowiedz tylko słowem BUY lub HOLD."}],
            model="llama3-8b-8192"
        )
        decision = response.choices[0].message.content.strip().upper()
        
        if "BUY" in decision and balance > 10:
            balance -= 10.0
            trades.append({"event": event, "action": "BUY", "status": "Simulated"})
    except Exception as e:
        print(f"Błąd AI: {e}")

# Uruchomienie harmonogramu (automatyczne transakcje co 60 sekund)
scheduler = BackgroundScheduler()
scheduler.add_job(func=perform_trade_logic, trigger="interval", seconds=60)
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    return jsonify({"balance": round(balance, 2), "trades": trades[-10:]})

if __name__ == '__main__':
    app.run(port=5000)
