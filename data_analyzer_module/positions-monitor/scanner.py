### TODO Section ###

# TODO: Implement a notification system to alert you when a whale position is detected.
# TODO: Add functionality to track the performance of different position groups over time.
# TODO: Implement a machine learning model to predict market trends based on the data collected.
# TODO: Add functionality to adjust the scanner's parameters in real-time based on market conditions.
# TODO: Add functionality to export the data collected to a CSV file for further analysis.





import logging
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, or_, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String
from pytz import timezone
import decimal
import sys
import os
from decimal import Decimal

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
    """This function sets up logging to both a file and the console"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

# Database setup
def setup_database():
    """This function sets up the database connection and returns the Session and Base classes"""
    engine = create_engine(MY_POSTGRESQL_URL, echo=True)
    Session = sessionmaker(bind=engine)
    Base = declarative_base()
    return Session, Base

# Fetched Position table class definition
def define_fetched_position(Base):
    """This function defines the FetchedPosition class, which represents the fetched_positions table in the database"""
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
        """The constructor initializes the logger, Session, and FetchedPosition attributes"""
        self.logger = logger
        self.Session = Session
        self.FetchedPosition = FetchedPosition

    def fetch_recent_positions(self, session):
        """This function fetches recent positions from the database"""
        tz = timezone('UTC')  # Set the appropriate timezone
        thirty_minutes_ago = datetime.now(tz) - timedelta(minutes=THIRTY_MINUTES)
        positions = session.query(self.FetchedPosition).filter(
            or_(
                self.FetchedPosition.opened_at >= thirty_minutes_ago,
                self.FetchedPosition.closed_at >= thirty_minutes_ago
            )
        ).all()
        return positions if positions else []


    def calculate_position_cost(self, positions):
        """This function calculates the cost of multiple positions by multiplying the amount and entry price
        and taking the absolute value of the result to account for short positions."""
        position_cost = 0
        for position in positions:
            position_cost += abs(float(position.amount) * float(position.entry_price))
        return position_cost

    def find_whale_positions(self, positions):
        """This function finds whale positions that were opened or closed in the last 30 minutes"""
        tz = timezone('UTC')  # Set the appropriate timezone
        thirty_minutes_ago = datetime.now(tz) - timedelta(minutes=THIRTY_MINUTES)
        whale_positions = [
            position for position in positions
            if self.calculate_position_cost([position]) > WHALE_SIZE_THRESHOLD
            and (position.opened_at >= thirty_minutes_ago or position.closed_at >= thirty_minutes_ago)
        ]
        return whale_positions

    def find_similar_positions(self, positions):
        """This function finds similar positions among traders. Similarity is determined based on the symbol, 
        direction (long or short), and entry price. Similar positions are stored in a list of lists."""
        similar_positions = []
        for position in positions:
            if position in similar_positions:
                continue
            similar_positions.append([position])
            for position2 in positions:
                if position2 in similar_positions:
                    continue
                if (
                    position.symbol == position2.symbol
                    and position.long == position2.long
                    and decimal.Decimal(str(position.entry_price)) * decimal.Decimal('0.985')
                    <= position2.entry_price
                    <= decimal.Decimal(str(position.entry_price)) * decimal.Decimal('1.015')
                    and abs(position.leverage - position2.leverage) <= LEVERAGE_THRESHOLD
                    and abs(position.amount - position2.amount) <= SIMILARITY_THRESHOLD
                    and abs((position.opened_at - position2.opened_at).total_seconds()) <= THIRTY_MINUTES
                ):
                    similar_positions[-1].append(position2)
        return similar_positions

    def analyze_similar_positions(self, similar_positions):
        """This function analyzes the similar positions and determines how they could affect the market"""
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



    # TODO: Implement a risk management system that will calculate a risk value based on the exposure and direction of all open positions and
    #       the average open position pnl.
    #       If positions are over exposed to the upside and the average open pnl is negative, the risk value will be high to the downside.
    #       If positions are over exposed to the downside and the average open pnl is negative, the risk value will be high to the upside.
    #       If positions are over exposed to the upside and the average open pnl is positive, the risk value will be lower to the downside.
    #       If positions are over exposed to the downside and the average open pnl is positive, the risk value will be lower to the upside.
    #       If positions are not over exposed to either side, the risk value will be neutral.
    #       Output Values:
    #           -> Summary message (High risk to the upside/downside, Low risk to the upside/downside, Neutral)
    #           - Risk Value
    #           - Biggest Open Position with the highest exposure (Symbol, Direction, Amount, Entry Price, Leverage, PNL, ROE, Position Cost)
    #           - Average Open PNL
    #           - Average Open ROE
    #           - Average Leverage
    #           - Average Entry Price
    #           - Average Amount
    #           - Average Position Cost
    #           - Total Position Cost
    #           - Total Position PNL



    def calculate_average(self, values):
        """Calculate the average of a list of values"""
        if len(values) == 0:
            return 0
        return sum(values) / len(values)

    def risk_management(self, positions):
        """This function calculates the risk value of the open positions"""
        open_positions = [position for position in positions if position.closed_at is None]
        if not open_positions:
            print("No open positions.")
            return

        long_positions = [position for position in open_positions if position.long]
        short_positions = [position for position in open_positions if not position.long]

        total_long_position_cost = sum([self.calculate_position_cost([position]) for position in long_positions])
        total_short_position_cost = sum([self.calculate_position_cost([position]) for position in short_positions])

        average_open_pnl = self.calculate_average([position.pnl for position in open_positions])
        average_open_roe = self.calculate_average([position.roe for position in open_positions])
        average_leverage = self.calculate_average([position.leverage for position in open_positions])
        average_position_cost = self.calculate_average([self.calculate_position_cost([position]) for position in open_positions])
        total_position_cost = sum([self.calculate_position_cost([position]) for position in open_positions])
        total_position_pnl = sum([position.pnl for position in open_positions])

        biggest_open_position = max(open_positions, key=lambda position: self.calculate_position_cost([position]))

        # Calculate risk value based on the exposure and average PNL
        risk_value = Decimal(abs(total_long_position_cost - total_short_position_cost)) * (1 - Decimal(average_open_pnl))

        # Print risk management information
        # If there are more long positions than short positions, and the average open pnl of those long positions is negative, then there is a high risk for downside
        # If there are more long positions than short positions, and the average open pnl of those long positions is positive, then there is a medium risk for downside
        # If there are more short positions than long positions, and the average open pnl of those short positions is negative, then there is a high risk for upside
        # If there are more short positions than long positions, and the average open pnl of those short positions is positive, then there is a medium risk for the upside
        # If there are an equal number of long and short positions, then there is a low risk for either side
        print("Risk Analysis:")
        if len(long_positions) > len(short_positions):
            if average_open_pnl < 0:
                print("High risk for downside")
            else:
                print("Medium risk for downside")
        elif len(short_positions) > len(long_positions):
            if average_open_pnl < 0:
                print("High risk for upside")
            else:
                print("Medium risk for upside")
        else:
            print("Low risk for either side")

        # print risk values.
        # fromat to 2 decimals and thousands separator
        print(f"Risk Value: {risk_value:,.2f}")
        print(f"Biggest Open Position: {biggest_open_position.symbol}")
        print(f"Direction: {'Long' if biggest_open_position.long else 'Short'}")
        print(f"Amount: {biggest_open_position.amount:.4f}/{biggest_open_position.symbol.replace('USDT', '')}")
        print(f"Entry Price: {biggest_open_position.entry_price:,.2f}$")
        print(f"PNL: {biggest_open_position.pnl:.2f}$")
        print(f"ROE: {biggest_open_position.roe:.2f}%")
        print(f"Position Cost: {self.calculate_position_cost([biggest_open_position]):,.2f}$")
        print(f"Average Open PNL: {average_open_pnl:.2f}$")
        print(f"Average Open ROE: {average_open_roe:.2f}%")
        print(f"Average Leverage: {average_leverage:.2f}x")
        print(f"Average Position Cost: {average_position_cost:,.2f}$")
        print("")
        # print total long and short position costs
        print(f"Total Long Position Cost: {total_long_position_cost:,.2f}$")
        print(f"Total Short Position Cost: {total_short_position_cost:,.2f}$")




    def print_whale_positions(self, whale_positions):
        """This function prints the whale positions"""
        print("Whale Positions:")
        for position in whale_positions:
            self.print_position_info(position)
            print("")

    def print_position_info(self, position):
        """This function prints the information of a position"""
        print(f"Symbol: {position.symbol}")
        print(f"Direction: {'Long' if position.long else 'Short'}")
        print(f"Amount: {position.amount:.4f}/{position.symbol.replace('USDT', '')}")
        print(f"Entry Price: {position.entry_price:,.2f}$")
        print(f"PNL: {position.pnl:.2f}$")
        print(f"ROE: {position.roe:.2f}%")
        print(f"Position Cost: {self.calculate_position_cost([position]):,.2f}$")
        print(f"Leverage: {position.leverage}x")
        print("")

    def scan_database(self):
        """This function scans the database for recent positions, whale positions, and similar positions"""
        session = self.Session()
        try:
            self.logger.info("Scanning database for recent positions...")
            positions = self.fetch_recent_positions(session)
            self.logger.info("Finding whale positions...")
            whale_positions = self.find_whale_positions(positions)
            self.logger.info("Finding similar positions...")
            similar_positions = self.find_similar_positions(positions)
            self.logger.info("Analyzing similar positions...")
            self.analyze_similar_positions(similar_positions)
            self.logger.info("Printing whale positions...")
            self.print_whale_positions(whale_positions)
            self.logger.info("Analyzing risk levels...")
            self.risk_management(positions)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"A database error occurred: {e}")
        except TypeError as e:
            self.logger.error(f"A TypeError occurred: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
        finally:
            session.close()

    def run(self):
        """This function runs the scanner every 2 minutes"""
        while True:
            self.logger.info("Starting new scan...")
            self.scan_database()
            self.logger.info("Scan completed. Sleeping for 2 minutes...")
            time.sleep(120)  # Run every 2 minutes (120 seconds)


if __name__ == "__main__":
    logger = setup_logging()
    Session, Base = setup_database()
    FetchedPosition = define_fetched_position(Base)
    positions_scanner = PositionsScanner(logger, Session, FetchedPosition)
    positions_scanner.run()