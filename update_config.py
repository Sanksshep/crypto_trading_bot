import json
import requests
import logging
from requests.auth import AuthBase

logging.basicConfig(filename='bot.log', level=logging.INFO)

class CoinbaseAuth(AuthBase):
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def __call__(self, request):
        request.headers.update({
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': self.api_secret,
            'CB-VERSION': '2021-11-09'
        })
        return request

def get_valid_trading_pairs():
    """
    Fetch valid trading pairs from Coinbase Pro and return those trading in USD.
    """
    url = "https://api.pro.coinbase.com/products"
    try:
        response = requests.get(url)
        response.raise_for_status()
        products = response.json()
        usd_pairs = [product['base_currency'] for product in products if product['quote_currency'] == 'USD']
        return usd_pairs
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching trading pairs: {e}")
        return []

def update_config():
    """
    Fetch available cryptocurrencies trading in USD from Coinbase Pro and update the config.json file.
    """
    logging.info("Starting update_config")
    
    config_path = 'config.json'
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    api_key = config['api_key']
    api_secret = config['api_secret']
    valid_pairs = get_valid_trading_pairs()
    
    config['cryptocurrencies'] = valid_pairs
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    logging.info("Successfully updated config.json with available USD cryptocurrencies")

if __name__ == "__main__":
    update_config()
