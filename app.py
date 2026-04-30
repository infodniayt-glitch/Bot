import os
import requests
import random
from flask import Flask, render_template, jsonify
from groq import Groq
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
app = Flask(__name__)

# Stan globalny
balance = 1000.0
trades = []
current_bot_status = "Oczekiwanie na ręczny start (wejdz na /start-bot)..."

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def perform_trade_logic():
    global balance, current_bot_status
    print("LOG: Rozpoczynam logikę bota...") # To pojawi się w logach Render
    
    current_bot_status = "Pobieranie danych z Polymarket..."
    
    try:
        url = "https://gamma-api.polymarket.com/events?active=true"
        response = requests.get(url, timeout=10)
        data = response.json()
        market = random.choice(data).get('title', 'Rynek')
        
        current_bot_status = f"Analiza: {market[:15]}..."
        
        prompt = f"Analizuj rynek: {market}. Czy BUY czy HOLD? Odpowiedz krótko."
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192"
        )
        decision = response.choices[0].message.content
        
        if "BUY" in decision.upper() and balance > 10:
            balance -= 10.0
            trades.append({"event": market, "action": "BUY"})
            current_bot_status = f"Kupiono: {market[:10]}..."
        else:
            current_bot_status = "Czekam..."
            
    except Exception as e:
        print(f"ERROR: {str(e)}") # Błąd w logach Render
        current_bot_status = f"Błąd: {str(e)}"

# Ręczny trigger do testów
@app.route('/start-bot')
def start_bot():
    perform_trade_logic()
    return "Bot uruchomiony ręcznie! Sprawdź dashboard."

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
