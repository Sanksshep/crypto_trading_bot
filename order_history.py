# Load packages
from coinbase.rest import RESTClient
import json
import time
import logging
import requests
from datetime import datetime, timedelta
import pandas as pd
import pickle
import os
import numpy as np
import requests
import time



def main():
    # Load config file
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Keys and secrets 
    api_key = config["api_key"]
    api_secret = config["api_secret"]

    # Connect to REST API
    client = RESTClient(api_key=api_key, api_secret=api_secret)

    # Get orders
    orders = client.list_orders()
    
    # Select specific keys
    order_keys = ['order_id', 'product_id', 'side', 'status', 'created_time', 
                  'filled_size', 'average_filled_price', 'filled_value','total_fees', 
                  'reject_reason', 'last_fill_time']

    # Create data frame of orders
    order_df = pd.concat([pd.DataFrame({key:order[key] if key in order else None for key in order_keys}, index=[ix]) 
                          for ix, order in enumerate(orders['orders'])], axis=0)
    
    # Get time
    now = datetime.now().strftime('%Y-%m-%d')

    # Save dataframe to data folder and log
    order_df.to_csv(f'data/order_df_{now}.csv', index=False)
    print('Saved order df')

if __name__ == "__main__":
    main()    
