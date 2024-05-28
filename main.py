# Load packages
from coinbase.rest import RESTClient
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from ml_logic import predict_action, feature_engineering
import pandas as pd
import pickle
import os
import numpy as np

logging.basicConfig(filename='bot.log', level=logging.INFO)

def load_config():
    """
    Load configuration from config.json.
    """
    logging.info("Loading config")
    with open('config.json', 'r') as f:
        return json.load(f)

def get_unix_time(datetime_string):
    """Returns unix time from date_time string, which is 
        given in YYYY-MM-DD format
    """
    if len(datetime_string) < 11:
        datetime_string = datetime_string + ' 00:00:00'

    # Define the format of the datetime string
    format = '%Y-%m-%d %H:%M:%S'

    # Convert the datetime string to a datetime object
    datetime_object = datetime.strptime(datetime_string, format)

    # Convert the datetime object to Unix time
    unix_time = int(datetime_object.timestamp())

    return unix_time

def get_market_data(client, crypto, start_date, end_date):
    """
    Fetch historical market data for a given cryptocurrency trading in USD using Coinbase API v3.
    """
    logging.info(f"Fetching market data for {crypto}-USD")
    config = load_config()
    crypto = f'{crypto}-USD'

    try:
        data = client.get_candles(crypto, start=start_date, end=end_date, granularity='ONE_DAY')
        # Transform the data into a DataFrame
        df = pd.DataFrame(data['candles'], columns=['start', 'low', 'high', 'open', 'close', 'volume'])
        df = df.apply(pd.to_numeric, errors='coerce')
        df.rename(columns={'start': 'date'}, inplace=True)
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df = df.sort_values(by='date', ascending=True)
        df.set_index('date', inplace=True)
       
        return df
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching market data for {crypto}-USD: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

def get_account_balance(client):
    """
    Fetch account balance from Coinbase API v3.
    """
    logging.info("Fetching account balance")

    try:
        accounts = client.get_accounts()
        usd_balance = 0
        account_num = len(accounts['accounts'])
        for i in range(account_num):
            if accounts['accounts'][i]['currency'] == "USD":
               usd_balance = float(accounts['accounts'][i]['available_balance']['value'])
               break
        
        logging.info(f"Account balance: {usd_balance} USD")
        return usd_balance
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching account balance: {e}")
        return 0  # Return 0 if there is an error

def get_current_price(client, crypto):
    book = client.get_best_bid_ask(f'{crypto}-USD')
    bid = float(book['pricebooks'][0]['bids'][0]['price'])
    ask = float(book['pricebooks'][0]['asks'][0]['price'])
    mid = sum([bid,ask])/2

    return bid, ask, mid

# def create_client_order_id():
#         num_id = 1
#         client_order_id = '0000' + str(num_id)
 

def execute_trade(client, crypto, action, position_size, client_order_id, trade_price):
    """
    Execute a trade on Coinbase.
    Placeholder function to be implemented.
    """
    logging.info(f"Executing {action} trade for {crypto}-USD with size {size}")

    # Format size and price
    size = round(position_size,6).astype(str)
    limit_price = str(round(trade_price,3))

    if action == 'BUY':
        limit_order = client.limit_order_gtc_buy(
            client_order_id=client_order_id,
            product_id=f"{crypto}-USD",
            base_size=size,
            limit_price=limit_price
        )
    else:
        limit_order = client.limit_order_gtc_sell(
            client_order_id=client_order_id,
            product_id=f"{crypto}-USD",
            base_size=size,
            limit_price=limit_price
        )

    return limit_order["order_id"]


def calculate_position_size(balance, crypto_price, max_trade_amount):
    """
    Calculate the position size based on balance, cryptocurrency price, and max trade amount.
    """
    logging.info(f"Calculating position size with balance {balance}, crypto price {crypto_price}, and max trade amount {max_trade_amount}")
    config = load_config()

    position_size_by_balance = min(balance * config['position_size_limit'], balance / crypto_price)
    position_size_by_trade_amount = max_trade_amount / crypto_price
    return min(position_size_by_balance, position_size_by_trade_amount)

def save_dict_to_file(data, filename):
    with open(filename, 'wb') as f:
        pickle.dump(data, f)

def load_dict_from_file(filename):
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    return {}


def main():
    """
    Main trading bot logic.
    """
    logging.info("Starting main trading bot")
    config = load_config()

    client = RESTClient(api_key=config["api_key"], api_secret=config["api_secret"])

    # Load previously saved data
    try: 
        market_data = load_dict_from_file('data/market_data.pkl')
        position_data = load_dict_from_file('data/position_data.pkl')
        order_ids = load_dict_from_file('data/order_ids.pkl')
        num_id = 0
    except FileNotFoundError:
        market_data = {}
        position_data = {}
        order_ids = {}
        num_id = 0

    while True:
        start_time = datetime.now()
        balance = get_account_balance(client)
        if balance == 0:
            logging.error("Insufficient balance, skipping trading cycle. Deposit funds or close positions")
            # Uncomment below if account is funded
            # time.sleep(3600)  # Wait for 1 hour before trying again
            # continue

        # Flags to track updates
        market_data_updated = False
        position_data_updated = False
        order_ids_updated = False        

        for crypto in config['cryptocurrencies']:
            try:
                start_date = get_unix_time(config['start_date'])
                end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                end_date = get_unix_time(end_date)
                market_data[crypto] = get_market_data(client, crypto, start_date, end_date)
                
                if market_data[crypto].empty:
                    logging.warning(f"No market data for {crypto}-USD")
                    continue

                # TODO        
                # features = feature_engineering(market_data[crypto])
                # if features.empty:
                #     logging.warning(f"Not enough data to calculate features for {crypto}-USD")
                #     continue

                # action = predict_action(features)

                last_price = market_data[crypto]['close'].iloc[-1]
                # Get mid-price
                _, _, mid = get_current_price(client, crypto)

                # Select HOLD to see data and     
                action = 'HOLD'

                if action in ['BUY', 'SELL']:
                    # Get position size and create dictionary
                    pos_size = calculate_position_size(balance, last_price, config['max_trade_amount'])
                    position_data[crypto] = {'position_size': pos_size, 'last_price': last_price, 'mid_price': mid}

                    # Generate client_order_id
                    num_id += 1
                    client_order_id = '0000' + str(num_id)

                    # Execute trade and store ids
                    limit_order_id = execute_trade(client, crypto, action, pos_size, client_order_id, mid)
                    order_ids[crypto] = {'limit_order_id': limit_order_id, 
                                         'order_time': datetime.now(),
                                         'client_order_id': client_order_id}
                    
                    market_data_updated = True
                    position_data_updated = True
                    order_ids_updated = True

                else:
                    # Get position size and create dictionary
                    pos_size = calculate_position_size(balance, last_price, config['max_trade_amount'])
                    position_data[crypto] = {'position_size': pos_size, 'last_price': last_price, 'mid_price': mid}

                    # Generate client_order_id
                    num_id += 1
                    client_order_id = '0000' + str(num_id)

                    # Execute trade and store ids
                    # limit_order_id = execute_trade(client, crypto, action, pos_size, client_order_id, mid)
                    order_ids[crypto] = {'limit_order_id': np.nan, 
                                         'order_time': datetime.now(),
                                         'client_order_id': client_order_id}    

            except Exception as e:
                logging.error(f"Error processing {crypto}: {str(e)}")
        
            # Save updated data only if there are changes
            if market_data_updated:
                save_dict_to_file(market_data, 'data/market_data.pkl')
                logging.info('market_data saved')
            if position_data_updated:
                save_dict_to_file(position_data, 'data/position_data.pkl')
                logging.info('position data saved')
            if order_ids_updated:
                save_dict_to_file(order_ids, 'dataorder_ids.pkl')
                logging.info('order ids saved')

        # Check for trade fills
        fill_dict = {}
        for crypto in config['cryptocurrencies']:
            time_now = datetime.now()
            if time_now + timedelta(minutes=config['check_fill_time']) > 5:
                fill = client.get_fills(order_ids[crypto]['limit_order_id'], f'{crypto}-USD')
                if fill['fills']['trade_type'] == 'FILL':
                    fill_dict[crypto] = {'filled': True, 
                                         'size': fill['fills']['size'],
                                         'price': fill['fills']['price'],
                                         'time': fill['fills']['sequence_timestamp']}
                    logging.info(f"{crypto} filled at {fill['fills']['sequence_timestamp']}")
                else:
                    fill_dict[crypto] = {'filled': False, 
                                         'size': 0.0,
                                         'price': 0.0,
                                         'time': 0.0}
                    client.cancel_orders(order_ids=[order_ids[crypto]['limit_order_id']])
                    logging.info(f'{crypto} not filled cancelling order')

        next_run = start_time + timedelta(hours=config['trade_interval_hours'])
        time.sleep((next_run - datetime.now()).total_seconds())

if __name__ == "__main__":
    main()
