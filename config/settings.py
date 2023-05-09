import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Load database connection
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# Load payment gateway connection
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")

# Load environment variables
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
CMCAL_API_KEY = os.getenv("CMCAL_API_KEY")
X_RAPIDAPI_KEY = os.getenv("X_RAPIDAPI_KEY")