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

def get_market_data(crypto):
    """
    Fetch historical market data for a given cryptocurrency trading in USD using Coinbase API v3.
    """
    logging.info(f"Fetching market data for {crypto}-USD")
    config = load_config()
    
    # URL for fetching historical data from Coinbase API v3
    url = f"https://api.coinbase.com/api/v3/brokerage/products/{crypto}-USD/candles?granularity=86400"

    try:
        headers = {
            'Authorization': f'Bearer {config["api_key"]}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Transform the data into a DataFrame
        df = pd.DataFrame(data, columns=['start', 'low', 'high', 'open', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['start'])
        df.set_index('date', inplace=True)
        
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching market data for {crypto}-USD: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

def get_account_balance():
    """
    Fetch account balance from Coinbase API v3.
    """
    logging.info("Fetching account balance")
    config = load_config()
    url = "https://api.coinbase.com/api/v3/brokerage/accounts"
    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Find the USD balance
        usd_balance = 0
        for account in data['accounts']:
            if account['currency'] == 'USD':
                usd_balance = float(account['balance']['amount'])
                break
        
        logging.info(f"Account balance: {usd_balance} USD")
        return usd_balance
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching account balance: {e}")
        return 0  # Return 0 if there is an error

def execute_trade(action, crypto, size):
    """
    Execute a trade on Coinbase.
    Placeholder function to be implemented.
    """
    logging.info(f"Executing {action} trade for {crypto}-USD with size {size}")
    # Placeholder: Replace with actual implementation

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
    
    while True:
        start_time = datetime.now()
        balance = get_account_balance()
        if balance == 0:
            logging.error("Insufficient balance, skipping trading cycle")
            time.sleep(3600)  # Wait for 1 hour before trying again
            continue
        
        for crypto in config['cryptocurrencies']:
            try:
                market_data = get_market_data(crypto)
                
                if market_data.empty:
                    logging.warning(f"No market data for {crypto}-USD")
                    continue

                features = feature_engineering(market_data)
                if features.empty:
                    logging.warning(f"Not enough data to calculate features for {crypto}-USD")
                    continue

                action = predict_action(features)
                
                if action in ['buy', 'sell']:
                    position_size = calculate_position_size(balance, market_data['close'].iloc[-1], config['max_trade_amount'])
                    execute_trade(action, crypto, position_size)
            except Exception as e:
                logging.error(f"Error processing {crypto}: {str(e)}")
        
        next_run = start_time + timedelta(hours=config['trade_interval_hours'])
        time.sleep((next_run - datetime.now()).total_seconds())

if __name__ == "__main__":
    main()
