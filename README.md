# Automated Crypto Trading Bot

## Overview
This is an automated crypto trading bot designed to trade on Coinbase using the Coinbase API v3. The bot fetches market data, applies machine learning models to predict buy/sell actions, and executes trades based on the predictions.

## Features
- Automates signal generation and order entry and checking
- Long-only as shorting not supported
- Risk management with take profit and stop loss
- Position sizing limited to 50% of portfolio
- Trades Bitcoin, Ethereum, DOGE, and Shiba Inu available cryptocurrencies on Coinbase
- Generates daily reports with graphs

## Requirements
- Python > 3.8  <= 3.10 
- [Coinbase Advanced API Python SDK](https://coinbase.github.io/coinbase-advanced-py/)

## Project Structure
crypto_trading_bot/  
├── config.json 
├── main.py 
├── utils.py 
├── update_config.py 
├── sandbox_test.py 
├── daily_report.py 
├── ml_logic.py 
├── backtesting.py 
├── bot.log 
├── reports/ 
│ └── daily_report_YYYY-MM-DD.json 
│ └── total_gain_loss.png 
│ └── daily_gain_loss.png 
│ └── portfolio_df.csv 
├── models/ 
│ └── current_model.pkl 
├── data/ 
│ └── all_trade_logs.pkl 
│ └── positions.pkl 
│ └── portfolio_df.pkl 
│ └── price_data.csv 
│ └── feature_set.csv 
│── requirements.txt 
└── README.md 


## Configuration

### `config.json`
Create a `config.json` file in the root directory with the following structure:

2. Update Available Cryptocurrencies
Run the update_config.py script to fetch and update the list of available cryptocurrencies:

python update_config.py

__Placeholder__ Currently not used

3. Run the Main Trading Bot
Run the main.py script to start the trading bot:

python main.py

4. Backtest Models
Run the backtesting.py script to backtest the models on historical data:

python backtesting.py

__Placeholder__ Currently not used

5. Generate Reports
Run the daily_report.py script to generate daily reports with graphs:

python daily_report.py

6. Test in Sandbox
Run the sandbox_test.py script to test the trading bot in Coinbase's sandbox environment:

python sandbox_test.py

__Placeholder__ Currently not used. Sandbox environment not enabled for Coinbase Advanced API Python SDK 

Logging
All events and errors are logged in bot.log.

## Steps to employ
- Create virtual env and install requirements.txt
    - For a mac use the following.
```
python3 -m venv venv
source ./venv/bin/activate
(venv) $ pip install --upgrade pip
(venv) $ pip install -r requirements.txt
```
- If install fails due to conflicts then
`(venv) $ pip install numpy pandas scikit-learn matplotlib yfinance coinbase-advanced-py`

- Go to [Coinbase Developers Platform](https://portal.cdp.coinbase.com/) to get API key and secret
- Ensure Trade and Transfer are selected in API restrictions
- Update `config.json` for API key and secret
- Run `ml_logic.py` to save model
- Run `main.py` once daily
- Run `daily_report.py` once daily

## IMPORTANT DISCLAIMER
All code, analyses, commentary, outputs, predictions, and results in this repository are provided as is, are for educational and informational purposes only, and do not constitute investment recommendations, offers to buy or sell securities, or recommendations on how to buy or sell securities. Past performance is not a predictor of future results. There is a significant risk of loss in investing and trading. Cryto currencies are highly speculative assets and not suitable for most investors. Derivatives pose a significant risk of loss with the potential to lose in excess of portfolio value. Users of this repository assume all risks and fully indemnify the repository's creator for any and all uses of the code, analyses, outputs, predictions, and/or results. 
