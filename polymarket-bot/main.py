import os
import time
import threading
from flask import Flask
from groq import Groq
from config import GROQ_API_KEY, INITIAL_BALANCE

# --- Konfiguracja Flask (Serwer WWW) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Tradingowy Polymarket działa poprawnie!"

# --- Logika Bota ---
def trading_loop():
    print("Logika bota: Uruchomiona w tle...")
    client = Groq(api_key=GROQ_API_KEY)
    
    while True:
        try:
            # Tu w przyszłości podepniesz API Polymarketu
            mock_market = {"name": "Czy jutro spadnie deszcz?", "price_yes": 0.45}
            
            prompt = f"Analizuj rynek: {mock_market}. Czy warto kupić pozycję YES? Odpowiedz tylko 'YES', 'NO' lub 'HOLD' i dodaj krótkie uzasadnienie."
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            decision = chat_completion.choices[0].message.content
            print(f"Analiza AI: {decision}")
            
        except Exception as e:
            print(f"Błąd w pętli bota: {e}")
        
        # Czekaj 60 sekund
        time.sleep(60)

# --- Uruchomienie ---
if __name__ == "__main__":
    # 1. Uruchom bota w osobnym wątku (nie blokuje serwera)
    bot_thread = threading.Thread(target=trading_loop, daemon=True)
    bot_thread.start()
    
    # 2. Uruchom serwer Flask (wymagane przez Render)
    # Render automatycznie przypisuje port przez zmienną środowiskową PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
