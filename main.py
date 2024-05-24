# Load packages
from coinbase.rest import RESTClient
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from ml_logic import predict_action, feature_engineering
import pandas as pd

logging.basicConfig(filename='bot.log', level=logging.INFO)

def load_config():
    """
    Load configuration from config.json.
    """
    logging.info("Loading config")
    with open('config.json', 'r') as f:
        return json.load(f)
    
def get_unix_time(datetime_string):
    """Returns unix time from date_time string, whichi is 
        given in YYYY-MM-DD format
    """
    datetime_string = datetime_string + ' 00:00:00'

    # Define the format of the datetime string
    format = '%Y-%m-%d %H:%M:%S'

    # Convert the datetime string to a datetime object
    datetime_object = datetime.strptime(datetime_string, format)

    # Convert the datetime object to Unix time
    unix_time = int(datetime_object.timestamp())

    return unix_time

def get_market_data(client, crypto, start_date, end_date, granularity):
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
        df['date'] = pd.to_datetime(df['start'], units='ms')
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

def execute_trade(client, crypto, action, size, client_order_id):
    """
    Execute a trade on Coinbase.
    Placeholder function to be implemented.
    """
    logging.info(f"Executing {action} trade for {crypto}-USD with size {size}")
    # Placeholder: Replace with actual implementation
    book = client.get_best_bid_ask(f'{crypto}-USD')
    bid = float(book['pricebooks'][0]['bids'][0]['price'])
    ask = float(book['pricebooks'][0]['asks'][0]['price'])
    mid = sum([bid,ask])/2

    # TODO
    # Separate function outside of this to generate client_order_id
    # From the docs: A unique ID provided by the client for their own identification purposes

    if action == 'BUY':
        limit_order = client.limit_order_gtc_buy(
            client_order_id=client_order_id,
            product_id="BTC-USD",
            base_size=size,
            limit_price=mid
        )
    else:
        limit_order = client.limit_order_gtc_sell(
            client_order_id=client_order_id,
            product_id="BTC-USD",
            base_size=size,
            limit_price=mid
        )

    limit_order_id = limit_order["order_id"]


def calculate_position_size(balance, crypto_price, max_trade_amount):
    """
    Calculate the position size based on balance, cryptocurrency price, and max trade amount.
    """
    logging.info(f"Calculating position size with balance {balance}, crypto price {crypto_price}, and max trade amount {max_trade_amount}")
    config = load_config()
    position_size_by_balance = min(balance * config['position_size_limit'], balance / crypto_price)
    position_size_by_trade_amount = max_trade_amount / crypto_price
    return min(position_size_by_balance, position_size_by_trade_amount)

def main():
    """
    Main trading bot logic.
    """
    logging.info("Starting main trading bot")
    config = load_config()

    client = RESTClient(api_key=config["api_key"], api_secret=config["api_secret"])
    
    while True:
        start_time = datetime.now()
        balance = get_account_balance()
        if balance == 0:
            logging.error("Insufficient balance, skipping trading cycle")
            time.sleep(3600)  # Wait for 1 hour before trying again
            continue
        
        for crypto in config['cryptocurrencies']:
            try:
                start_date = get_unix_time(config['start_date'])
                end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                market_data = get_market_data(client, crypto, start_date, end_date, granularity)
                
                if market_data.empty:
                    logging.warning(f"No market data for {crypto}-USD")
                    continue

                # TODO        
                # features = feature_engineering(market_data)
                # if features.empty:
                #     logging.warning(f"Not enough data to calculate features for {crypto}-USD")
                #     continue

                # action = predict_action(features)
                action = 'buy'

                if action in ['buy', 'sell']:
                    position_size = calculate_position_size(balance, market_data['close'].iloc[-1], config['max_trade_amount'])
                    execute_trade(action, crypto, position_size)
            except Exception as e:
                logging.error(f"Error processing {crypto}: {str(e)}")
        
        next_run = start_time + timedelta(hours=config['trade_interval_hours'])
        time.sleep((next_run - datetime.now()).total_seconds())

if __name__ == "__main__":
    main()
