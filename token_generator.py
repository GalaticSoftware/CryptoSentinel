import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database.models import OneTimeToken, Base


import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the database URL from the settings
from config.settings import MY_POSTGRESQL_URL

engine = create_engine(MY_POSTGRESQL_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def generate_token(access_duration):
    session = Session()
    token = str(uuid.uuid4())  # Generate a unique token
    expiration_time = datetime.utcnow() + timedelta(hours=24)  # Set the token to expire in 24 hours

    # Create a new OneTimeToken object
    one_time_token = OneTimeToken(token=token, expiration_time=expiration_time, access_duration=access_duration, used=False)

    # Add the new token to the session and commit the changes
    session.add(one_time_token)
    session.commit()

    # Close the session
    session.close()

    return token

if __name__ == "__main__":
    access_duration = "one_month"  # You can change this to the desired access duration
    token = generate_token(access_duration)
    print(f"Generated token: {token}")

