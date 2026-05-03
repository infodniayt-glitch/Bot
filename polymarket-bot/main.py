import os
from groq import Groq
from config import GROQ_API_KEY, INITIAL_BALANCE

client = Groq(api_key=GROQ_API_KEY)

def get_market_analysis(market_data):
    """Analiza rynku przez AI Groq"""
    prompt = f"Analizuj rynek: {market_data}. Czy warto kupić pozycję YES? Odpowiedz tylko 'YES', 'NO' lub 'HOLD' i dodaj krótkie uzasadnienie."
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def run_paper_trading():
    print(f"Start bota. Saldo: {INITIAL_BALANCE} USD")
    
    # Symulowane dane (w przyszłości tutaj podepniesz API Polymarketu)
    mock_market = {"name": "Czy jutro spadnie deszcz?", "price_yes": 0.45}
    
    decision = get_market_analysis(mock_market)
    print(f"Decyzja AI: {decision}")
    
    if "YES" in decision:
        print("Symulacja: Kupiono YES za 100 USD")
    else:
        print("Symulacja: Czekam na lepsze warunki.")

if __name__ == "__main__":
    run_paper_trading()
