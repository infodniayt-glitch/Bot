import os
from flask import Flask, render_template, jsonify
from groq import Groq
from dotenv import load_dotenv
import random

load_dotenv()
app = Flask(__name__)

# Konfiguracja (Symulacja portfela)
balance = 1000.0  # Wirtualne USD
trades = []
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_market_data_mock():
    # Zastąp to w przyszłości wywołaniem API Polymarket
    markets = ["Bitcoin > 100k", "Wybory USA", "Eksploracja Marsa"]
    return {
        "event": random.choice(markets),
        "odds": random.uniform(0.1, 0.9)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/trade', methods=['POST'])
def trade():
    global balance
    data = get_market_data_mock()
    
    # AI Analiza
    prompt = f"Analizuj rynek: {data['event']} z szansą {data['odds']}. Czy kupić (BUY) czy ignorować (HOLD)? Odpowiedz krótko."
    
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192"
    )
    decision = response.choices[0].message.content
    
    # Logika transakcji
    if "BUY" in decision.upper() and balance > 10:
        amount = 10.0
        balance -= amount
        trades.append({"event": data['event'], "action": "BUY", "status": "Simulated"})
        return jsonify({"decision": decision, "status": "Kupiono", "balance": balance})
    
    return jsonify({"decision": decision, "status": "Hold/Skip", "balance": balance})

@app.route('/api/stats')
def stats():
    return jsonify({"balance": balance, "trades": trades[-5:]})

if __name__ == '__main__':
    app.run(debug=True)
