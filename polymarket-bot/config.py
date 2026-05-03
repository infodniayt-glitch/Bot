import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Symulowane saldo początkowe
INITIAL_BALANCE = 1000.0
