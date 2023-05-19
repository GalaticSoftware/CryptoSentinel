import logging
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String
from pytz import timezone
import decimal
import sys
import os

# Add the root directory of your project to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

# Import settings from config
from config.settings import MY_POSTGRESQL_URL, X_RAPIDAPI_KEY

# Constants
THIRTY_MINUTES = 30
LEVERAGE_THRESHOLD = 5
SIMILARITY_THRESHOLD = 1.5
WHALE_SIZE_THRESHOLD = 1_000_000
SHARK_SIZE_THRESHOLD = 100_000
DOLPHIN_SIZE_THRESHOLD = 10_000
FISH_SIZE_THRESHOLD = 1_000

# Setup logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("scanner.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Database setup
engine = create_engine(MY_POSTGRESQL_URL, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Database setup
def setup_database():
    engine = create_engine(MY_POSTGRESQL_URL, echo=True)
    Session = sessionmaker(bind=engine)
    Base = declarative_base()
    return Session, Base


# Fetched Position table class definition
def define_fetched_position(Base):
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
    return FetchedPosition

# Main class definition
class PositionsScanner:
    def __init__(self, logger, Session, FetchedPosition):
        self.logger = logger
        self.Session = Session
        self.FetchedPosition = FetchedPosition

    def fetch_recent_positions(self, session):
        tz = timezone('UTC')  # Set the appropriate timezone
        thirty_minutes_ago = datetime.now(tz) - timedelta(minutes=THIRTY_MINUTES)
        positions = session.query(self.FetchedPosition).filter(
            or_(
                self.FetchedPosition.opened_at >= thirty_minutes_ago,
                self.FetchedPosition.closed_at >= thirty_minutes_ago
            )
        ).all()
        return positions if positions else []


    # calculate position cost for multiple positions by multiplying amount and entry price and taking the absolute value of the result
    # to account for short positions. Then return the result as a float and store it in the position_cost variable.
    def calculate_position_cost(self, positions):
        position_cost = 0
        for position in positions:
            position_cost += abs(float(position.amount) * float(position.entry_price))
        return position_cost

    def find_whale_positions(self, positions):
        tz = timezone('UTC')  # Set the appropriate timezone
        thirty_minutes_ago = datetime.now(tz) - timedelta(minutes=THIRTY_MINUTES)
        # Find whale positions that were opened or closed in the last 30 minutes
        # for example: positions with a position cost greater than 1,000,000 USD
        whale_positions = [
            position for position in positions
            if self.calculate_position_cost([position]) > WHALE_SIZE_THRESHOLD
            and (position.opened_at >= thirty_minutes_ago or position.closed_at >= thirty_minutes_ago)
                ]
        return whale_positions

    def find_similar_positions(self, positions):
            # Find if traders (UIDs) have similar positions open
            # we will use the symbol, direction (long or short), and entry price to determine if positions are similar
            # similar positions will be stored in a list of lists
            # each list will contain positions that are similar to each other
            # (similar entry price, symbol, and direction) similar entry price means a range of +- 1.5%

            similar_positions = []
            for position in positions:
                # check if the position is already in the list of similar positions
                # if it is, skip it
                if position in similar_positions:
                    continue
                # create a new list for similar positions
                similar_positions.append([position])
                # loop through the positions again and check if they are similar
                for position2 in positions:
                    # check if the position is already in the list of similar positions
                    # if it is, skip it
                    if position2 in similar_positions:
                        continue
                    # check if the position is similar to the current position
                    # add conditions for leverage and amount
                    if (
                        position.symbol == position2.symbol
                        and position.long == position2.long
                        and decimal.Decimal(str(position.entry_price)) * decimal.Decimal('0.985')
                        <= position2.entry_price
                        <= decimal.Decimal(str(position.entry_price)) * decimal.Decimal('1.015')
                        and abs(position.leverage - position2.leverage) <= 5  # replace with your threshold
                        and abs(position.amount - position2.amount) <= 20  # replace with your threshold
                        and abs((position.opened_at - position2.opened_at).total_seconds()) <= 50  # replace with your threshold in seconds
                    ):
                        # if it is, add it to the list of similar positions
                        similar_positions[-1].append(position2)
            return similar_positions

    # TODO: create a system to analyze the similar positions and determine how they could affect the market
    # This could be done by analyzing the amount of similar positions in each list and the total amount of
    # positions in each list. If there are a lot of similar positions in a list, it could mean that a lot of
    # traders are trading the same thing.
    # That could indicate a lot of trading interest and liquidity in a particular symbol.
    # If a lot of traders a long on a symbol, it could mean that downside price aciton could be more violent
    # if the price goes down. If a lot of traders are short on a symbol, it could mean that upside price action
    # could be more violent if the price goes up.

    def analyze_similar_positions(self, similar_positions):
        for position_list in similar_positions:
            num_similar_positions = len(position_list)
            total_positions = len(similar_positions)
            similarity_percentage = num_similar_positions / total_positions * 100

            # Only consider Moderate and High concentration positions
            if similarity_percentage > 30:
                # Find the position with the highest position cost
                max_position_cost = max(position_list, key=lambda position: self.calculate_position_cost([position]))

                # Print only the symbol of the position with the highest position cost
                print(f"Symbol: {max_position_cost.symbol}")

                if similarity_percentage > 70:
                    print("High concentration of similar positions")
                    print("This could indicate significant trading interest and liquidity in the symbol.")
                    print("Retail traders may be getting trapped and providing liquidity to market makers.")
                else:
                    print("Moderate concentration of similar positions")
                    print("Traders are showing interest in the symbol.")

                # Print additional information about the position with the highest position cost
                self.print_position_info(max_position_cost)
                print("")


    def print_whale_positions(self, whale_positions):
        print("Whale Positions:")
        for position in whale_positions:
            self.print_position_info(position)
        print("")

    def print_similar_positions(self, similar_positions):
        print("Similar Positions:")
        for position in similar_positions:
            self.print_position_info(position)
        print("")

    def print_position_info(self, position):
        print(f"Symbol: {position.symbol}")
        print(f"Direction: {'Long' if position.long else 'Short'}")
        # print the amount + symbol without USDT
        print(f"Amount: {position.amount:.4f}/{position.symbol.replace('USDT', '')}")
        print(f"Entry Price: {position.entry_price:,.2f}$")
        print(f"PNL: {position.pnl:.2f}$")
        # print PNL with two decimal places and format to percentage
        print(f"PNL: {position.pnl:,.2f}$")
        print(f"ROE: {position.roe:.2f}%")
        # print position cost in USD and with thousands separators and two decimal places
        print(f"Position Cost: {self.calculate_position_cost([position]):,.2f}$")
        print(f"Leverage: {position.leverage}x")
        print("")

    def scan_database(self):
        session = self.Session()
        try:
            positions = self.fetch_recent_positions(session)
            whale_positions = self.find_whale_positions(positions)
            similar_positions = self.find_similar_positions(positions)
            self.analyze_similar_positions(similar_positions)
            self.print_whale_positions(whale_positions)
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while scanning the database: {e}")
        finally:
            session.close()

    def run(self):
        while True:
            self.scan_database()
            time.sleep(120)  # Run every 2 minutes (120 seconds)


if __name__ == "__main__":
    logger = setup_logging()
    Session, Base = setup_database()
    FetchedPosition = define_fetched_position(Base)
    positions_scanner = PositionsScanner(logger, Session, FetchedPosition)
    positions_scanner.run()
