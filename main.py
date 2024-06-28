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
from utils import * 

# Params
MODEL_PATH = 'models/current_model.pkl'
TRADE_LOG_PATH = 'data/all_trade_logs.pkl'
POSITION_PATH = 'data/positions.pkl'

logging.basicConfig(filename='bot.log', level=logging.INFO)

# Main function to run the trading script
def main():
    """
    Main trading bot logic.
    """
    logging.info("Starting main trading bot")
    
    config = load_config()

    api_key = config["api_key"]
    api_secret = config["api_secret"]

    # Instantiate Rest Client
    client = RESTClient(api_key=api_key, api_secret=api_secret)

    # Check balance
    balance = get_account_balance(client)
    if balance == 0:
        logging.error("Insufficient balance, zero balance, skipping trading cycle. Deposit funds or close positions")
    if balance < config['max_trade_amount']:
        logging.error("Insufficient balance, balance less than max trade amount, skipping trading cycle. Deposit funds or close positions")

    # Load trade logs and positions
    try:
        all_trade_logs = load_dict_from_file(TRADE_LOG_PATH)
        positions = load_dict_from_file(POSITION_PATH)
    except FileNotFoundError:
        all_trade_logs = {}
        positions = {crypto: {'status': 'closed',
                              'direction': 'flat', 
                              'price': 0, 
                              'size':0 , 
                              'profit_target': 0,
                              'stop_loss_price': 0} for crypto in config['cryptocurrencies']
        }

    # Get dates in unix time for trading
    start_date = (datetime.now() - timedelta(days=250)).strftime('%Y-%m-%d %H:%M:%S')
    start_date = get_unix_time(start_date)
    end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    end_date = get_unix_time(end_date)

    # Get market data 
    crypto_list = []
    
    for crypto in config['cryptocurrencies']:
        temp_df = get_market_data(client, config, crypto, start_date, end_date)
        temp_df = pd.DataFrame(temp_df['close'].values, index = temp_df.index, columns=[crypto])
        crypto_list.append(temp_df)

    mkt_data = pd.concat([x for x in crypto_list], axis=1)
    mkt_data.columns = [x.lower() for x in mkt_data.columns]

    # Generate predictions
    predictions = load_model_and_predict(mkt_data, MODEL_PATH)
    # print(f'Predictions: {predictions}')

    # Overwrite for time being
    predictions = np.array([1,1,1,1])
    # print(f'New predictions: {predictions}')

    # Generate signals
    signal_dict = {}
    for ix, crypto in enumerate(config['cryptocurrencies']):
        profit_target = positions[crypto]['profit_target']
        stop_loss_price = positions[crypto]['stop_loss_price']
        last_price = mkt_data[crypto.lower()].iloc[-1]
        current_position = positions[crypto]['status']
        direction = positions[crypto]['direction']        

        signal = get_trading_signal(predictions[ix], 
                                    profit_target, 
                                    stop_loss_price, 
                                    last_price, 
                                    current_position,
                                    direction)
            
        _, _, mid = get_current_price(client, crypto)

        signal_dict[crypto] = {'signal': signal,
                               'mid_price': mid}
        
    # print(f'Signals: {signal_dict}')

    # Generate trades
    order_dict = {}
    num_id = np.random.randint(1,500)

    for ix, crypto in enumerate(config['cryptocurrencies']):
        try:
            # If trade action     
            if signal_dict[crypto]['signal'] in ['BUY', 'SELL']:

                # Get position size
                pos_size = calculate_position_size(client, 
                                                   balance, 
                                                   crypto, 
                                                   signal_dict[crypto]['mid_price'], 
                                                   config, 
                                                   positions)

                # If sufficient funds
                if pos_size > 0.0:
                    signal_dict[crypto]['position_size'] = pos_size

                    # Generate client_order_id
                    num_id += 1
                    client_order_id = '0000' + str(num_id)

                    # Create log_name
                    time_now = datetime.now()
                    log_name = crypto + ' - ' + time_now.strftime("%Y-%m-%d %H:%M:%S")

                    # Get mid price from dictionary
                    mid_price = signal_dict[crypto]['mid_price']
                    
                    # Execute trade and store ids
                    limit_order, trade_log, positions = execute_trade(client, 
                                                                        crypto, 
                                                                        config, 
                                                                        signal, 
                                                                        pos_size, 
                                                                        client_order_id, 
                                                                        mid_price, 
                                                                        time_now, 
                                                                        log_name, 
                                                                        positions)
                    
                    if limit_order['success']:
                        balance = balance - pos_size * mid_price
                        logging.info(f'{crypto} order placed successfully')
      
                    else:
                        logging.error(f'{crypto} order failed')
                        
                    all_trade_logs[crypto] = trade_log
                    order_dict[crypto] = {'log_name': log_name,
                                            'order': limit_order
                    }
                
                # Insufficient funds
                else: 
                    trade_log[log_name] = {'orders': {'crypto':crypto,
                                'action': signal,
                                'client_order_id': client_order_id,
                                'size': pos_size,
                                'limit_price': mid_price,
                                'order_time': time_now.strftime("%Y-%m-%d %H:%M:%S"),
                                'limit_order_id': np.nan,
                    }}
                    all_trade_logs[crypto] = trade_log
                    order_dict[crypto] = {'log_name': log_name,
                                          'order': np.nan}

            # If no trade
            else:                
                if positions[crypto]['direction'] == "LONG":
                    # Update profit and loss targets if price has moved higher
                    if signal_dict[crypto]['mid_price'] > positions[crypto]['profit_target']:
                        positions[crypto]['profit_target'] = signal_dict[crypto]['mid_price'] * (1 + config['take_profit_percent'])
                        positions[crypto]['stop_loss_price'] = signal_dict[crypto]['mid_price'] * (1 - config['stop_loss_percentages'])
                        logging.info(f"Maintaining position in {crypto}. Updating targets")
                    # No update
                    else:
                        logging.info(f"Maintaining position in {crypto}. No change to targets.")

        except Exception as e:
            logging.error(f"Error processing {crypto}: {str(e)}")

        # Pause before executing next trade
        time.sleep(5)
    
   
    # Wait a minute before checking order status
    time.sleep(60)

    all_trade_logs = retry_check_order_status(client, 
                                          config['cryptocurrencies'],
                                          all_trade_logs,
                                          order_dict,
                                          positions
    )
    
    save_dict_to_file(all_trade_logs, TRADE_LOG_PATH)
    save_dict_to_file(positions, POSITION_PATH)
    logging.info('Saving trade logs')
    logging.info('Saving positions')

if __name__ == '__main__':
    main()

