import os
import requests
import random
from flask import Flask, render_template, jsonify
from groq import Groq
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
load_dotenv()

# Stan globalny
balance = 1000.0
trades = []
current_bot_status = "Oczekiwanie na start..."

# Inicjalizacja Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def perform_trade_logic():
    global balance, current_bot_status
    print("DEBUG: Rozpoczęto cykl bota!") # To zobaczysz w logach Render
    
    current_bot_status = "Pobieranie danych..."
    try:
        url = "https://gamma-api.polymarket.com/events?active=true"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data: 
            current_bot_status = "Brak rynków"
            return
            
        market = random.choice(data).get('title', 'Unknown')
        current_bot_status = f"Analiza: {market[:15]}..."
        
        # Analiza AI
        prompt = f"Rynek: {market}. Kupić (BUY) czy czekać (HOLD)? Odpowiedz tylko słowem."
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192"
        )
        decision = response.choices[0].message.content.strip().upper()
        
        if "BUY" in decision and balance >= 10:
            balance -= 10.0
            trades.append({"event": market, "action": "BUY"})
            current_bot_status = "Kupiono!"
        else:
            current_bot_status = "Hold (Czekam)..."
            
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}") # To zobaczysz w logach Render
        current_bot_status = f"Błąd: {str(e)[:15]}"

# Scheduler - startuje w tle
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
        "trades": trades[-5:], 
        "status": current_bot_status
    })

if __name__ == '__main__':
    app.run()
