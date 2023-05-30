import os
from dotenv import load_dotenv
import psycopg2
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Load database connection
MY_POSTGRESQL_URL = os.getenv("MY_POSTGRESQL_URL")


def get_connection():
    return psycopg2.connect(MY_POSTGRESQL_URL, sslmode="require")


# Load payment gateway connection
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_PROVIDER_TOKEN = os.getenv("STRIPE_PROVIDER_TOKEN")
STRIPE_PROVIDER_TOKEN_TEST = os.getenv("STRIPE_PROVIDER_TOKEN_TEST")

# Load environment variables
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
CMCAL_API_KEY = os.getenv("CMCAL_API_KEY")
X_RAPIDAPI_KEY = os.getenv("X_RAPIDAPI_KEY")
X_RAPIDAPI_KEY2 = os.getenv("X_RAPIDAPI_KEY2")

TELEGRAM_IDS = os.getenv("TELEGRAM_IDS")
