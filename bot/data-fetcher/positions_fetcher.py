import requests
import hashlib
from datetime import datetime
from sqlalchemy import func
from bot.database import Position, Session
from config.settings import X_RAPIDAPI_KEY

# UID list
uid_list = [
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

# Fetch data for a single trader

def fetch_and_store_positions():
    url = "https://binance-futures-leaderboard1.p.rapidapi.com/v2/getTraderPositions"
    headers = {
        "X-RapidAPI-Key": X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": "binance-futures-leaderboard1.p.rapidapi.com"
    }

    # Fetch data for multiple traders
    for uid in uid_list:
        try:
            querystring = {"encryptedUid": uid}
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()  # This will raise an HTTPError if the response was unsuccessful
            data = response.json()

            if data['success']:
                with Session() as session:
                    for position in data['data'][0]['positions']['perpetual']:
                        # Calculate position cost and current position value
                        position_cost = abs(position['entryPrice'] * position['amount'])
                        current_position_value = abs(position['markPrice'] * position['amount'])

                        # Create a unique identifier for each position
                        position_id = hashlib.sha256((uid + position['symbol'] + str(position['entryPrice'])).encode()).hexdigest()

                        # Create a new position object
                        new_position = Position(
                            id=position_id,
                            trader_uid=uid,
                            symbol=position['symbol'],
                            entry_price=position['entryPrice'],
                            mark_price=position['markPrice'],
                            pnl=position['pnl'],
                            roe=position['roe'],
                            amount=position['amount'],
                            update_timestamp=position['updateTimeStamp'],
                            traded_before=position['tradeBefore'],
                            is_long=position['long'],
                            is_short=position['short'],
                            leverage=position['leverage'],
                            position_cost=position_cost,
                            current_position_value=current_position_value,
                            open_time=datetime.utcnow()  # consider this as the open time
                        )

                        existing_position = session.query(Position).filter_by(id=position_id).first()
                        if existing_position:
                            # Update the existing position values
                            existing_position.entry_price = position['entryPrice']
                            existing_position.mark_price = position['markPrice']
                            existing_position.pnl = position['pnl']
                            existing_position.roe = position['roe']
                            existing_position.amount = position['amount']
                            existing_position.update_timestamp = position['updateTimeStamp']
                            existing_position.traded_before = position['tradeBefore']
                            existing_position.is_long = position['long']
                            existing_position.is_short = position['short']
                            existing_position.leverage = position['leverage']
                            existing_position.position_cost = position_cost
                            existing_position.current_position_value = current_position_value
                            existing_position.profit_or_loss = 'profit' if existing_position.pnl > 0 else 'loss'
                        else:
                            # Add the new position into the database
                            session.add(new_position)

                        session.commit()

                    # Handle closed positions
                    # Get all positions for the current uid
                    all_positions_for_current_uid = session.query(Position).filter_by(trader_uid=uid).all()
                    for stored_position in all_positions_for_current_uid:
                        # If the position is not in the new data, then it is closed
                        if not any(pos['symbol'] == stored_position.symbol and pos['entryPrice'] == stored_position.entry_price and pos['amount'] == stored_position.amount for pos in data['data'][0]['positions']['perpetual']):
                            stored_position.close_time = datetime.utcnow()
                            session.commit()
        except requests.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
        else:
            print('Success!')

