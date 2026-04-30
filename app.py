import os
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

def perform_trade_logic():
    global balance, current_bot_status
    
    current_bot_status = "Analizowanie rynku przez AI..."
    
    # Symulacja danych rynkowych
    markets = ["Bitcoin > 100k", "Wybory USA", "Eksploracja Marsa", "Cena Złota"]
    event = random.choice(markets)
    odds = random.uniform(0.1, 0.9)
    
    try:
        # Analiza AI
        prompt = f"Rynek: {event}, Szansa: {odds:.2f}. Czy kupić (BUY) czy ignorować (HOLD)? Odpowiedz krótko."
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192"
        )
        decision = response.choices[0].message.content
        
        if "BUY" in decision.upper() and balance > 10:
            current_bot_status = "Wykonywanie transakcji (Kupno)..."
            balance -= 10.0
            trades.append({"event": event, "action": "BUY", "status": "Simulated"})
        else:
            current_bot_status = "Brak sygnału (Hold)..."
            
    except Exception as e:
        current_bot_status = f"Błąd: {str(e)}"
    
    # Czekanie
    current_bot_status = "Czekam na kolejny cykl..."

# Uruchomienie harmonogramu
scheduler = BackgroundScheduler()
scheduler.add_job(func=perform_trade_logic, trigger="interval", seconds=60)
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
