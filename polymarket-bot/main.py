import os
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string
from groq import Groq
# Import klienta Polymarket
from py_clob_client.client import ClobClient
from config import GROQ_API_KEY, INITIAL_BALANCE

app = Flask(__name__)
logs = []

# --- Konfiguracja API ---
# host='https://clob.polymarket.com' - oficjalne API Polymarket
clob = ClobClient("https://clob.polymarket.com")

def add_log(message, type="info"):
    now = datetime.now().strftime("%H:%M:%S")
    logs.insert(0, {"time": now, "msg": message, "type": type})
    if len(logs) > 50: logs.pop() # Zwiększamy bufor logów

def trading_loop():
    client = Groq(api_key=GROQ_API_KEY)
    add_log("System uruchomiony. Łączę z Polymarket API...")
    
    while True:
        try:
            # 1. Pobierz aktywne rynki (np. 5 pierwszych)
            markets = clob.get_markets()[:5]
            
            for market in markets:
                market_name = market.get('question')
                price = market.get('last_trade_price')
                
                # 2. Analiza przez AI
                prompt = f"Rynek: {market_name}. Cena YES: {price}. Czy trend jest wzrostowy? Odpowiedz: KUP/CZEKAJ i podaj krótkie uzasadnienie."
                
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                
                decision = completion.choices[0].message.content
                if "KUP" in decision.upper():
                    add_log(f"SYMULACJA: Decyzja KUP dla '{market_name[:30]}...'", "trade")
                
            add_log("Cykl analizy zakończony. Czekam 30s...")
            
        except Exception as e:
            add_log(f"BŁĄD API: {str(e)}", "error")
        
        time.sleep(30) # Szybsze sprawdzanie

# --- Dashboard HTML (zostaje bez zmian) ---
# ... (użyj tego samego HTML_TEMPLATE co poprzednio)

if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
