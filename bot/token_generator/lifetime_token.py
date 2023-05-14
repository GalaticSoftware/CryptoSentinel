import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from bot.database import OneTimeToken, Base

# Import the database URL from the settings
from config.settings import MY_POSTGRESQL_URL

def generate_token():
    engine = create_engine(MY_POSTGRESQL_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)

    token = str(uuid.uuid4())
    new_token = OneTimeToken(token=token, expiration_time=None)  # No expiration time for lifetime access
    session.add(new_token)
    session.commit()

    print(f"Generated token: {token}")
    return token

if __name__ == "__main__":
    generate_token()