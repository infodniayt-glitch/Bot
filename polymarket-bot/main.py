import time
from groq import Groq
from config import GROQ_API_KEY, INITIAL_BALANCE

client = Groq(api_key=GROQ_API_KEY)

def get_market_analysis(market_data):
    prompt = f"Analizuj rynek: {market_data}. Czy warto kupić pozycję YES? Odpowiedz tylko 'YES', 'NO' lub 'HOLD' i dodaj krótkie uzasadnienie."
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def run_paper_trading():
    # Tu w przyszłości będzie logika pobierania danych
    mock_market = {"name": "Czy jutro spadnie deszcz?", "price_yes": 0.45}
    decision = get_market_analysis(mock_market)
    print(f"Analiza zakończona. Decyzja AI: {decision}")

if __name__ == "__main__":
    print("Bot uruchomiony i działa w pętli...")
    while True:
        try:
            run_paper_trading()
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
        
        # Czekaj 60 sekund przed kolejną iteracją
        time.sleep(60)
