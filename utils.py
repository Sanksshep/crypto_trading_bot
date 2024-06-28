# Load packages
from coinbase.rest import RESTClient
from coinbase import jwt_generator
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from ml_logic import feature_engineering
import pandas as pd
import pickle
import os
import numpy as np
import requests
import pandas as pd
import joblib
import time


# Functions
def load_config():
    """
    Load configuration from config.json.
    """
    now = datetime.now()
    logging.info(f"Loading config at {now}")
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

def get_market_data(client, config, crypto, start_date, end_date):
    """
    Fetch historical market data for a given cryptocurrency trading in USD using Coinbase API v3.
    """
    logging.info(f"Fetching market data for {crypto}-USD")
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

# Function to load model and make predictions
def load_model_and_predict(data, model_path):
    model = joblib.load(model_path)
    symbols = data.columns.to_list()
    pred_dat = feature_engineering(data)
    X_pred = pred_dat[[f'{x}_sma' for x in symbols] + [f'{x}_ema' for x in symbols]]
    predictions = model.predict(X_pred)
    return predictions[-1,:]

# Function to translate predictions into signals
def get_trading_signal(prediction, profit_target, stop_loss_price, current_price, current_position, direction):
    """Generates trade signal based on prediction, profit/loss targets, current price, current posiiton,
        and direction of trade
        current_position: open, closed, default is closed if no position 
        direction: LONG
    """
    if current_position == 'closed':
        if prediction == 1:
            return 'BUY'
        # Coin short selling not supported

    else:
        if direction == 'LONG':
            if current_price <= stop_loss_price:
                return 'SELL'
            if prediction == 1:                 
                return 'HOLD'
            else:
                return 'SELL'
        else:
            if current_price >= stop_loss_price:
                return 'BUY'
            if prediction == 1:
                return 'BUY'
            else:
                return 'HOLD'
            
# Current price to execute trade
def get_current_price(client, crypto, threshold=1):
    book = client.get_best_bid_ask(f'{crypto}-USD')
    price_increment = client.get_product(f'{crypto}-USD')['price_increment']
    price_increment = len(price_increment[2:])
    bid = float(book['pricebooks'][0]['bids'][0]['price'])
    ask = float(book['pricebooks'][0]['asks'][0]['price'])
    mid = round(sum([bid,ask])/2*threshold, price_increment)

    return bid, ask, mid

# Calculate desired position size
def calculate_position_size(client, balance, crypto, crypto_price, config, positions):
    """
    Calculate the position size based on balance, cryptocurrency price, and max trade amount.
    """
    logging.info(f"Calculating position size with balance {balance}, \
                 crypto price {crypto_price}, \
                 and max trade amount {config['max_trade_amount']}")
    
    if balance < config['max_trade_amount']:
        logging.error("Insufficient balance, \
                      balance less than max trade amount, \
                      skipping trading cycle. \
                      Deposit funds or close positions")
        return 0.0      

    else: 
        cur_pos = positions[crypto]['status']

        if cur_pos == 'closed':
            size_increment = client.get_product(f'{crypto}-USD')['base_increment']
            size_increment = len(size_increment[2:])

            position_size_by_balance = min(balance * config['position_size_limit'] / crypto_price, balance / crypto_price)
            position_size_by_balance = round(position_size_by_balance, size_increment)
            
            position_size_by_trade_amount = config['max_trade_amount'] / crypto_price
            position_size_by_trade_amount = round(position_size_by_trade_amount, size_increment)

            return min(position_size_by_balance, position_size_by_trade_amount)
        
        else:
            return float(positions[crypto]['size'])

# Function to execute trade
def execute_trade(client, crypto, config, signal, position_size, client_order_id, trade_price, time_now, log_name, positions):
    """
    Execute a trade on Coinbase.
    Placeholder function to be implemented.
    """
    logging.info(f"Executing {signal} trade for {crypto}-USD with size {position_size}")

    # Create trade log dictionary
    trade_log = {}

    # Format size and price
    size = str(position_size)
    limit_price = np.format_float_positional(trade_price)
    # counteracts scientific notation
    
    if signal == 'BUY':
        limit_order = client.limit_order_gtc_buy(
            client_order_id=client_order_id,
            product_id=f"{crypto}-USD",
            base_size=size,
            limit_price=limit_price
        )
        target_return = (1 + config['take_profit_percent']/100)
        target_loss = (1 - config['stop_loss_percentages']["100+"]/100)
    else: 
        limit_order = client.limit_order_gtc_sell(
            client_order_id=client_order_id,
            product_id=f"{crypto}-USD",
            base_size=size,
            limit_price=limit_price
        )
        target_return = (1 - config['take_profit_percent']/100)
        target_loss = (1 + config['stop_loss_percentages']["100+"]/100)

    trade_log[log_name] = {'orders': {'crypto':crypto,
                 'action': signal,
                 'client_order_id': client_order_id,
                 'size': position_size,
                 'limit_price': limit_price,
                 'order_time': time_now.strftime("%Y-%m-%d %H:%M:%S"),
                 'limit_order_id': limit_order["order_id"],
    }}

    positions[crypto] = {'status': 'open', 
                         'direction': "LONG" if signal in ['BUY','HOLD'] else "FLAT",
                         'price': limit_price, 
                         'size': position_size , 
                         'profit_target': float(limit_price) * target_return,
                         'stop_loss_price': float(limit_price) * target_loss
    } 

    return limit_order, trade_log, positions

# Function to check if trades are filled
def check_order_status(client, crypto, logged_trade, positions):
    order_id = logged_trade['orders']['limit_order_id']
    order = client.get_order(order_id)
    if order['order']['status'] == 'FILLED':
        fill = client.get_fills(order_id, f'{crypto}-USD')['fills'][0]
        fill_dict = {'fills': {'filled': True, 
                                'size': fill['size'],
                                'price': fill['price'],
                                'time': fill['sequence_timestamp']}
        }
        positions[crypto]['status'] = 'open'
        positions[crypto]['direction'] = 'LONG'
        logged_trade.update(fill_dict)
        logging.info(f"{crypto} filled at {fill['sequence_timestamp']}")

        return logged_trade, positions
    else:
        return ValueError("Order not filled")

# Function to cancel order
def cancel_order(client, crypto, logged_trade, order_id):
    client.cancel_orders(order_ids=[order_id])
    logging.info(f'{crypto} not filled after 3 attempts. Cancelling order')
    time_now = datetime.now()
    fill_dict = {'fills': {'filled': False,
                                'cancelled': True,
                                'size': 0.0,
                                'price': 0.0,
                                'time': time_now}
    }
    logged_trade.update(fill_dict)
    return logged_trade

def retry_check_order_status(client, cryptos, all_trade_logs, order_dict, positions, delay_between_checks=5):
    if len(order_dict) > 0:
        max_attempts = 3
        attempts = {crypto: 0 for crypto in cryptos}
        errors = {crypto: False for crypto in cryptos}
        
        for attempt in range(max_attempts):
            for crypto in cryptos:
                if attempts[crypto] < max_attempts:
                    crypto_order = order_dict[crypto]['log_name']
                    logged_trade = all_trade_logs[crypto][crypto_order]
                    try:
                        logged_trade, positions = check_order_status(client, crypto, logged_trade, positions)
                        all_trade_logs[crypto][crypto_order] = logged_trade
                        errors[crypto] = False
                    except ValueError as e:
                        logging.error(f"Attempt {attempt + 1} failed for {crypto}: {e}")
                        # logging.warning(f"Attempt {attempt + 1} failed for {crypto}: {e}")
                        errors[crypto] = True
                    finally:
                        attempts[crypto] += 1

            time.sleep(delay_between_checks)

        for crypto, error in errors.items():
            if error:
                crypto_order = order_dict[crypto]['log_name']
                logged_trade = all_trade_logs[crypto][crypto_order]
                retry_order_info = order_dict[crypto]['limit_order']
                logged_trade = cancel_order(client, crypto, logged_trade, retry_order_info)
                all_trade_logs[crypto][crypto_order] = logged_trade
        
        return all_trade_logs
    else:
        # logging.info('No trades')
        logging.info('No trades')
        return all_trade_logs

# Load and save
def save_dict_to_file(data, filename):
    with open(filename, 'wb') as f:
        pickle.dump(data, f)

def load_dict_from_file(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

# Fetch account
def fetch_accounts(client):
    try:
        # Get accounts using the SDK's method
        accounts = client.get_accounts()
        print("### Accounts Data:")
        print(json.dumps(accounts, indent=2))
    except Exception as e:
        print(f"An error occurred: {e}")

