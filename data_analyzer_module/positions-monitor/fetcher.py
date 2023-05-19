import requests
import time
import concurrent.futures
import logging
import hashlib
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Numeric, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

import sys
import os

# Add the root directory of your project to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

# Now you can import config.settings
from config.settings import MY_POSTGRESQL_URL, X_RAPIDAPI_KEY


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fetcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()
engine = create_engine(MY_POSTGRESQL_URL, echo=True)
Session = sessionmaker(bind=engine)

# Fetched Position table class definition
class FetchedPosition(Base):
    __tablename__ = 'fetched_positions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(String, unique=True)
    uid = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    entry_price = Column(Numeric(20, 10), nullable=False)
    mark_price = Column(Numeric(20, 10), nullable=False)
    pnl = Column(Numeric(20, 10), nullable=False)
    roe = Column(Numeric(20, 10), nullable=False)
    amount = Column(Numeric(20, 10), nullable=False)
    update_timestamp = Column(BigInteger, nullable=False)
    trade_before = Column(Boolean, nullable=False)
    long = Column(Boolean, nullable=False)
    short = Column(Boolean, nullable=False)
    leverage = Column(Integer, nullable=False)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)

# API setup
API_URL = "https://binance-futures-leaderboard1.p.rapidapi.com/v2/getTraderPositions"
HEADERS = {
    "X-RapidAPI-Key": X_RAPIDAPI_KEY,
    "X-RapidAPI-Host": "binance-futures-leaderboard1.p.rapidapi.com"
}

class UIDFetcher:
    def __init__(self, url, headers):
        self.url = url
        self.headers = headers

    def fetch_data(self, uid):
        session = Session()
        try:
            logging.info(f"Fetching data for UID {uid}")
            querystring = {"encryptedUid": uid}
            response = requests.get(self.url, headers=self.headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            positions_data = data['data'][0]['positions']
            if not positions_data['perpetual'] and not positions_data['delivery']:
                logging.info(f"Positions data empty for UID {uid}")
                return

            # Get all position_ids for this UID from the database
            db_position_ids = {p.position_id for p in session.query(FetchedPosition.position_id).filter_by(uid=uid).all()}

            # Process the fetched positions
            self.process_positions(uid, positions_data, session, db_position_ids)
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred while fetching data for UID {uid}: {e}")
        except SQLAlchemyError as e:
            logging.error(f"An error occurred while interacting with the database: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            session.close()

    def process_positions(self, uid, positions_data, session, db_position_ids):
        for position_type in ['perpetual', 'delivery']:
            positions = positions_data[position_type]
            if positions is None:
                continue
            for position in positions:
                position_id = self.generate_position_id(uid, position)
                logging.info(f"Fetched position_id: {position_id}")
                db_position = session.query(FetchedPosition).filter_by(position_id=position_id).first()
                if db_position:
                    self.update_position(db_position, position)
                    db_position_ids.discard(position_id)
                else:
                    self.create_position(position_id, uid, position, session)
                session.commit()

        # Any remaining position_ids in the set were not in the fetched data, so mark them as closed
        for position_id in db_position_ids:
            logging.info(f"Database position_id not in fetched data: {position_id}")
            db_position = session.query(FetchedPosition).filter_by(position_id=position_id).first()
            if db_position:
                db_position.closed_at = datetime.utcnow()
                session.commit()



    # Define a function to generate a unique position_id for each position
    # This is done by hashing the UID for the position and the symbol of the position + the direction of the position (long/short)
    # This is done because the UID + symbol + direction is unique for each position
    def generate_position_id(self, uid, position):
        symbol = position["symbol"]
        direction = "long" if position["long"] else "short"
        position_string = f"{uid}{symbol}{direction}"
        position_id = hashlib.sha256(position_string.encode()).hexdigest()
        return position_id

    def update_position(self, db_position, position):
        logging.info(f"Updating existing position for UID {db_position.uid}")
        db_position.entry_price = position["entryPrice"]
        db_position.mark_price = position["markPrice"]
        db_position.pnl = position["pnl"]
        db_position.roe = position["roe"]
        db_position.amount = position["amount"]
        db_position.update_timestamp = position["updateTimeStamp"]
        db_position.trade_before = position["tradeBefore"]
        db_position.long = position["long"]
        db_position.short = position["short"]
        db_position.leverage = position["leverage"]

    def create_position(self, position_id, uid, position, session):
        logging.info(f"Creating new position for UID {uid}")
        db_position = FetchedPosition(
            position_id=position_id,
            uid=uid,
            symbol=position["symbol"],
            entry_price=position["entryPrice"],
            mark_price=position["markPrice"],
            pnl=position["pnl"],
            roe=position["roe"],
            amount=position["amount"],
            update_timestamp=position["updateTimeStamp"],
            trade_before=position["tradeBefore"],
            long=position["long"],
            short=position["short"],
            leverage=position["leverage"],
        )
        session.add(db_position)

    def fetch_all(self, uids):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Split the uids into chunks of 5
            uid_chunks = [uids[i:i + 5] for i in range(0, len(uids), 5)]

            for chunk in uid_chunks:
                futures = [executor.submit(self.fetch_data, uid) for uid in chunk]
                concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)

                # Wait for 1 second before fetching the next chunk
                time.sleep(1)
                 

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uids = [
        "E4C2BCB6FDF2A2A7A20D516B8389B952",
        "F90459BB0C3BC6CE241CADAA80DEBF25",
        "36D12879856E9ABF7148BAE61E77D279",
        "FE63D6040E22611D978B73064B3A2057",
        "FB23E1A8B7E2944FAAEC6219BBDF8243",
        "3EFA61BC63849632347ED020C78634E1",
        "6408AAEEEBF0C76A3D5F0E39C64AAABA",
        "8FE17CCE0A3EA996ED7D8B538419C826",
        "DF74DFB6CB244F8033F1D66D5AA0B171",
        "49A7275656A7ABF56830126ACC619FEB",
        "227087068C057B808A83125C8E586BB8",
        "5018838FFE413B7A80D2529393DB1D7A",
        "8FEB3EA2D767A27324E7D0A8B2E8FEA4",
        "BFE5C3E7EF7B3629438D907CD3B21D57",
        "3673EC40E6C6E3B1344BF2D06FDFBEAC",
        "D3C53A1F16564BC318AB4EB434C2D744",
        "9AE2180CA966B9DC203BDC35017E365B",
        "2AB7A7FDE7AA7493D5F6ADF5F89062F3",
        "EE56F412D7DAB7DBAFCEC2147FA2D223",
        "15E75BFF207E01A5A18BAED302A6F5A8",
        "FA49B09E9F2AFAC7D043ABCF7E4DA33E",
        "0932D2B47499C2E940AE805D3D2D9B72",
        "A67FD74A4472775D2D68342CB9A9DA83",
        "3BB43EB380247F51910B3E7951931601",
        "2EFB73F424C573BCE5841AD66A014852",
        "A086AC7B587E11941378E95DD6C872C6",
        "2154D02AD930F6C6E65C507DD73CB3E7",
        "BBFE38FA1FA9F14BE8533E0508DC8468",
        "538E78E33A3B0363FC37E393EB334103",
        "633EC27B03AF7CEA79BA725D434B06B5",
    ]
    fetcher = UIDFetcher(API_URL, HEADERS)
    fetcher.fetch_all(uids)