# Load packages
from coinbase.rest import RESTClient
# from coinbase import jwt_generator
import json
import time
import logging
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
# from ml_logic import feature_engineering
import pandas as pd
import pickle
import os
import numpy as np
import requests
import joblib
import time
from main_basic import *

# Set Style
plt.style.use('seaborn-v0_8')
plt.rcParams['figure.figsize'] = (14,8)

# Set PARAMS
PORTFOLIO_PATH = 'reports/portfolio_df.csv'
DATE = datetime.now().strftime('%Y-%m-%d')
REPORT_PATH = f"reports/daily_report_{DATE}.json"

# Function
def calculate_fees(data, num_trades = 0.0):
    all_trade_logs = load_dict_from_file('data/all_trade_logs.pkl')
    num = (data['fees'] > 0.0).sum()
    if num > num_trades:
        num_trades = num
    fees = []
    for key in all_trade_logs.keys():
        trades = [str(x) for x in all_trade_logs[key].keys()]
        if len(trades) > num_trades:
            log_name = trades[-1]
            fill_price = float(all_trade_logs[key][log_name]['fills']['price'])
            size = float(all_trade_logs[key][log_name]['fills']['size'])
            # fees 0.8% for taker
            fee = round(fill_price * size * 0.008,2)
            fees.append(fee)
        else:
            fees.append(0)
            
    return np.array(fees).sum()

logging.basicConfig(filename='bot.log', level=logging.INFO)

def generate_daily_report():
    """
    Generate daily trading report with graphs.
    """
    config = load_config()
    symbols = config['cryptocurrencies']

    api_key = config["api_key"]
    api_secret = config["api_secret"]

    client = RESTClient(api_key=api_key, api_secret=api_secret)
    portfolio_id = client.get_portfolios()['portfolios'][0]['uuid']
    portfolio = client.get_portfolio_breakdown(portfolio_id)
    old_cols = ['total_crypto_balance', 'total_cash_equivalent_balance', 'total_balance']
    new_cols = ['crypto', 'cash', 'total']
    
    # Load historical portfolio data
    try:
        df = pd.read_csv(PORTFOLIO_PATH,index_col='date')
        logging.info("Load historical data")
        
        # Append updated portfolio data
        temp_df = pd.DataFrame(portfolio['breakdown']['portfolio_balances']).reset_index()
        temp_df = pd.DataFrame(temp_df.loc[0,old_cols].values.reshape(-1,3), columns=old_cols, index=[DATE])
        temp_df.index.name = 'date'
        temp_df.columns = new_cols
        temp_df['daily_pnl'] = 0.0
        temp_df['total_pnl'] = 0.0
        temp_df[new_cols] = temp_df[new_cols].apply(pd.to_numeric, errors='coerce')
        temp_df['fees'] = 0.0
        
        df = pd.concat([df, temp_df], axis=0)
        df['daily_pnl'] = df['total'].diff()
        df['total_pnl'] = df['daily_pnl'].cumsum()

        # Calculate fees
        fees = calculate_fees(df)
        df.loc[DATE, 'fees'] = fees

        # Get allocation and cost basis
        pf = pd.DataFrame(portfolio['breakdown']['spot_positions'])[['asset', 'total_balance_fiat', 'allocation', 'cost_basis']]
        pf['cost_basis'] = pf['cost_basis'].apply(pd.Series)['value']
        pf['cost_basis'] = pf['cost_basis'].apply(pd.to_numeric, errors='coerce')
          
        logging.info("Generating daily report")

        try:
            # Plots
            plt.figure(figsize=(10, 6))
            df['daily_pnl'].plot(kind='bar', rot=0)
            plt.xlabel('')
            plt.ylabel('US$')
            plt.title('Daily Gain/Loss')
            plt.savefig('reports/daily_gain_loss.png')
            
            plt.figure(figsize=(10, 6))
            df['total_pnl'].plot(kind='bar', rot=0)
            plt.xlabel('')
            plt.ylabel('US$')
            plt.title('Total Gain/Loss')
            plt.savefig('reports/total_gain_loss.png')

            # Create report
            report = {
                "date": DATE,
                "total_gain_loss": df['total_pnl'].iloc[-1],
                "daily_gain_loss": df['daily_pnl'].iloc[-1],
                "portfolio_distribution": pf[['asset','allocation']].set_index('asset').to_dict()['allocation'],
                "daily_transaction_fees": df['fees'].iloc[-1],
                "total_transations_fees": df['fees'].sum()
            }

            # Save report
            with open(REPORT_PATH, 'w') as f:
                json.dump(report, f, indent=4)
           
            logging.info(f"Daily report generated: {REPORT_PATH}")

            # Save portfolio
            df.reset_index().to_csv(PORTFOLIO_PATH, index=False)
            logging.info("Saved portfolio")

        except Exception as e:
            logging.error(f"Error generating daily report: {e}")
            logging.error('Portfolio data not saved')

    except FileNotFoundError:
        # Create data frame
        df = pd.DataFrame(portfolio['breakdown']['portfolio_balances']).reset_index()
        df = pd.DataFrame(df.loc[0,old_cols].values.reshape(-1,3), columns=old_cols, index=[DATE])
        df.index.name = 'date'
        df.columns = new_cols
        df['daily_pnl'] = 0.0
        df['total_pnl'] = 0.0
        df[new_cols] = df[new_cols].apply(pd.to_numeric, errors='coerce')

        # Add fees
        fees = calculate_fees(df)
        df['fees'] = fees
     
        logging.error('No historical data, generated base data set')
        
        # Save base portfolio
        df.reset_index().to_csv(PORTFOLIO_PATH, index=False)
        logging.info('Saved starting portfolio data')


if __name__ == "__main__":
    generate_daily_report()

