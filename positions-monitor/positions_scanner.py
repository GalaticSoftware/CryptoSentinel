import logging
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String
from pytz import timezone
import decimal

from config.settings import MY_POSTGRESQL_URL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("positions_scanner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(MY_POSTGRESQL_URL, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

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

# Define a new class that will scan the database for changes in positions
# This class will be scheduled to run every 5 minutes in the main.py file
# This class will also be responsible for sending notifications to the user
# if a big change in position is detected
# This could be:
# - A big position being opened (if amount times entry price is greater than 1000000)
# - A big position being closed (if amount times entry price is greater than 1000000)
# In addition to this, the class will also send a notification to the user if:
# - Multiple traders (UIDs) have similar positions open
# - Multiple positions just opened or closed in the last 30 minutes

class PositionsScanner:
    def __init__(self):
        engine = create_engine(MY_POSTGRESQL_URL, echo=True)
        self.Session = sessionmaker(bind=engine)

    def scan_database(self):
        session = self.Session()
        try:
            # Fetch positions that opened or closed in the last 30 minutes
            tz = timezone('UTC')  # Set the appropriate timezone
            thirty_minutes_ago = datetime.now(tz) - timedelta(minutes=30)
            positions = session.query(FetchedPosition).filter(
                or_(
                    FetchedPosition.opened_at >= thirty_minutes_ago,
                    FetchedPosition.closed_at >= thirty_minutes_ago
                )
            ).all()

            # Find positions that have been opened or closed where the amount times entry price is greater than 1000000
            big_positions = []
            for position in positions:
                if (position.opened_at >= thirty_minutes_ago or position.closed_at >= thirty_minutes_ago) and position.amount * decimal.Decimal(str(position.entry_price)) > decimal.Decimal('1000000'):
                    big_positions.append(position)

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
                    if (
                        position.symbol == position2.symbol
                        and position.long == position2.long
                        and decimal.Decimal(str(position.entry_price)) * decimal.Decimal('0.985')
                        <= position2.entry_price
                        <= decimal.Decimal(str(position.entry_price)) * decimal.Decimal('1.015')
                    ):
                        # if it is, add it to the list of similar positions
                        similar_positions[-1].append(position2)

            # TODO: create a system to analyze the similar positions and determine how they could affect the market
            # This could be done by analyzing the amount of similar positions in each list and the total amount of
            # positions in each list. If there are a lot of similar positions in a list, it could mean that a lot of
            # traders are trading the same thing.
            # That could indicate a lot of trading interest and liquidity in a particular symbol.
            # If a lot of traders a long on a symbol, it could mean that downside price aciton could be more violent
            # if the price goes down. If a lot of traders are short on a symbol, it could mean that upside price action
            # could be more violent if the price goes up.

            # Analyze similar positions and determine their potential impact
            for position_list in similar_positions:
                num_similar_positions = len(position_list)
                total_positions = len(positions)
                similarity_percentage = num_similar_positions / total_positions * 100

                # Analyze the similarity percentage and provide insights
                if similarity_percentage > 70:
                    print("High concentration of similar positions")
                    print("This could indicate significant trading interest and liquidity in the symbol.")
                    print("Retail traders may be getting trapped and providing liquidity to market makers.")
                elif similarity_percentage > 30:
                    print("Moderate concentration of similar positions")
                    print("Traders are showing interest in the symbol.")
                else:
                    print("Low concentration of similar positions")
                    print("There is a diverse range of trading strategies among market participants.")

                # Analyze the position directions (long or short)
                num_long_positions = sum(position.long for position in position_list)
                num_short_positions = sum(position.short for position in position_list)

                if num_long_positions > num_short_positions:
                    print("More traders are long on the symbol")
                    print("There might be a potential for a downside squeeze as retail traders may get trapped.")
                    print("Market makers could exploit this by triggering stop losses.")
                elif num_long_positions < num_short_positions:
                    print("More traders are short on the symbol")
                    print("There might be a potential for an upside squeeze as retail traders may get trapped.")
                    print("Market makers could exploit this by triggering short squeezes.")
                else:
                    print("Equal number of long and short positions")
                    print("There is a balanced sentiment among traders.")

                # Analyze PNL data
                pnl_values = [position.pnl for position in position_list]
                average_pnl = sum(pnl_values) / len(pnl_values)

                if average_pnl > 0:
                    print("Average PNL of similar positions is positive")
                    print("Retail traders are generating profits, but they might be exposed to potential reversals.")
                    print("Market makers could exploit this by inducing reversals and trapping retail traders.")
                elif average_pnl < 0:
                    print("Average PNL of similar positions is negative")
                    print("Retail traders are experiencing losses, and there might be potential for further downside.")
                    print("Market makers could exploit this by triggering further selling pressure.")
                else:
                    print("Average PNL of similar positions is close to zero")
                    print("Retail traders have mixed performance, and the market sentiment is uncertain.")

                # Print additional information about the similar positions if needed
                for position in position_list:
                    self.print_position_info(position)
                print("")



            

            # TODO: Similar analysis like the one above.
            # TODO: Create a system to analyze the big positions and determine how they could affect the market


            # Print out the positions that have been found
            print("Big Positions:")
            for position in big_positions:
                self.print_position_info(position)
            print("")


        except Exception as e:
            logging.error(f"An unexpected error occurred while scanning the database: {e}")
        finally:
            session.close()

    def print_position_info(self, position):
        print(f"Position ID: {position.position_id}")
        print(f"UID: {position.uid}")
        print(f"Symbol: {position.symbol}")
        print(f"Entry Price: {position.entry_price}")
        print(f"Mark Price: {position.mark_price}")
        print(f"PNL: {position.pnl}")
        print(f"ROE: {position.roe}")
        print(f"Amount: {position.amount}")
        print(f"Update Timestamp: {position.update_timestamp}")
        print(f"Trade Before: {position.trade_before}")
        print(f"Long: {position.long}")
        print(f"Short: {position.short}")
        print(f"Leverage: {position.leverage}")
        print(f"Opened At: {position.opened_at}")
        print(f"Closed At: {position.closed_at}")
        print("")

    def send_notification(self, message):
        # TODO: Implement logic for sending notifications to the user
        logging.info(f"Sending notification: {message}")

    def run(self):
        while True:
            self.scan_database()
            time.sleep(300)  # Run every 5 minutes

if __name__ == "__main__":
    positions_scanner = PositionsScanner()
    positions_scanner.run()
