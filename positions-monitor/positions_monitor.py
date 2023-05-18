import requests
import time
import concurrent.futures
import os
import psycopg2
import datetime

from psycopg2 import sql
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Numeric, BigInteger, ForeignKey, func, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import exists

from config.settings import MY_POSTGRESQL_URL

# Create a declarative base class for creating table classes
Base = declarative_base()
engine = create_engine(MY_POSTGRESQL_URL, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

# Create Database Table if it doesn't exist
# Fetched Position table class definition
class FetchedPosition(Base):
    __tablename__ = 'fetched_positions'
    id = Column(Integer, primary_key=True)  # unique identifier for each position
    uid = Column(String, nullable=False)  # trader UID
    symbol = Column(String, nullable=False)  # symbol
    entry_price = Column(Numeric(20, 10), nullable=False)  # entry price
    mark_price = Column(Numeric(20, 10), nullable=False)  # mark price
    pnl = Column(Numeric(20, 10), nullable=False)  # pnl
    roe = Column(Numeric(20, 10), nullable=False)  # roe
    amount = Column(Numeric(20, 10), nullable=False)  # amount
    update_timestamp = Column(BigInteger, nullable=False)  # update timestamp
    trade_before = Column(Boolean, nullable=False)  # traded before
    long = Column(Boolean, nullable=False)  # is long
    short = Column(Boolean, nullable=False)  # is short
    leverage = Column(Integer, nullable=False)  # leverage
    opened_at = Column(DateTime, default=datetime.utcnow)  # when the position was opened
    closed_at = Column(DateTime)  # when the position was closed



# Define the URL and headers
url = "https://binance-futures-leaderboard1.p.rapidapi.com/v2/getTraderPositions"
headers = {
    "X-RapidAPI-Key": "d272cbb83emshafd80a0ad2aebbfp1e6fa8jsne11ab7615f57",
    "X-RapidAPI-Host": "binance-futures-leaderboard1.p.rapidapi.com"
}

# Define a list of UIDs
uids = [
        "3AFFCB67ED4F1D1D8437BA17F4E8E5ED",
        "F5335CE565C1C0712A254FB595193E84",
        "4325641055745EBAFED26DB3ACDC7AF1",
        "268BCB704E7DA7FE7EE3D228F248BDAB",
        "A086AC7B587E11941378E95DD6C872C6",
        "DA200CE4A90667D0E59FDF8E6B68E599",
        "65B136F1A727C572A5CA114F3CDC97AA",
        "36D12879856E9ABF7148BAE61E77D279",
        "87FFB710AC2792DE3145272BCBA05EBE",
        "A980D282CBFA6AC326160A5B2D879798",
        "8785BDE7F3A55E0C353ABDFE85899A26",
        "A99ACCB8798FCC1D822250364ED487AB",
        "FB7B3C9E5AE654B39231923DDB4D5260",
        "C20E7A8966C0014A4AF5774DD709DC42",
        "D3AFE978B3F0CD58489BC27B35906769",
        "F90459BB0C3BC6CE241CADAA80DEBF25",
        "E4C2BCB6FDF2A2A7A20D516B8389B952",
        "A532C4316C00206168F795EDFBB3E164",
        "21CD087408060BDD97F001B72CC2B0D3",
        "FE63D6040E22611D978B73064B3A2057",
        "B8538478A5B1907531E8EAC3BCFE0626",
        "FB23E1A8B7E2944FAAEC6219BBDF8243",
        "3EFA61BC63849632347ED020C78634E1",
        "AB995C0BACF7B0DF83AAAA61CAD3AD11",
        "6F79990013ADA8A281145D9EC2421AC3",
        "5233F02D1841D75C9DCC63D356A1758C",
        "D2EE8B6D70AAC0181B6D0AB857D6EF60",
        "F4BD136947A8A5DD4494D9A4264432B6",
        "BFE5C3E7EF7B3629438D907CD3B21D57",
        "8FE17CCE0A3EA996ED7D8B538419C826",
        "6408AAEEEBF0C76A3D5F0E39C64AAABA",
        "FB7B3C9E5AE654B39231923DDB4D5260",
        "49A7275656A7ABF56830126ACC619FEB",
    ]



# Define a function to fetch data for a single UID
def fetch_data(uid):
    querystring = {"encryptedUid": uid}
    response = requests.get(url, headers=headers, params=querystring)
    print(response.text)
    return response.json()

# Fetch data for all UIDs
data = []
# Use a ThreadPoolExecutor to fetch data for all UIDs concurrently
# This will speed up the data fetching process
# The number of threads is set to 5
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = []
    for i, uid in enumerate(uids):
        # Add a delay after 5 requests to avoid rate limiting
        if i % 5 == 0:
            time.sleep(2)
        futures.append(executor.submit(fetch_data, uid))
    for future in concurrent.futures.as_completed(futures):
        data.append(future.result())

# Print the data
print(data)


