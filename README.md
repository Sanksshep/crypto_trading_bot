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
├── index.html  
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
│ └── price_data.csv  
│ └── feature_set.csv   
│── requirements.txt  
└── README.md  


## Configuration

1. `config.json` holds api keys, secrets, and important parameters

2. `ml_logic.py` the main file to train and save model

3. `main.py` runs the main trading bot

4. `daily_report.py` generates daily and total gain and loss calculations with graphs

5. `index.html` file to populate web page with output of `daily_report.py`


## Other placeholder files not currently being used

1. `update_config.py` updates `config.json` for current list of available cryptocurrencies:

2. `backtesting.py` script to backtest the models on historical data:

3. `sandbox_test.py` tests the trading bot in Coinbase's sandbox environment


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
- `(venv) $ cd crypto_trading_bot`
- Update `config.json` for API key and secret
- If folders models, data, and/or reports don't exist run:
    - `(venv) $ mkdir models`
    - `(venv) $ mkdir data`
    - `(venv) $ mkdir reports`
- Run `ml_logic.py` to save model
- Run `main.py` once daily
- Run `daily_report.py` once daily
- From terminal run
``` python -m http.server```
- Then open web broswer and type
```http://localhost:8000/index.html``` 

## To run the report
- cd into crypt_trading_bot-sm-sandbox and then from the terminal run
```
python -m http.server
```
- Then open a new window in your web browser and enter
```
http://localhost:8000/index.html
```

## IMPORTANT DISCLAIMER
All code, analyses, commentary, outputs, predictions, and results in this repository are provided as is, are for educational and informational purposes only, and do not constitute investment recommendations, offers to buy or sell securities, or recommendations on how to buy or sell securities. Past performance is not a predictor of future results. There is a significant risk of loss in investing and trading. Cryto currencies are highly speculative assets and not suitable for most investors. Derivatives pose a significant risk of loss with the potential to lose in excess of portfolio value. Users of this repository assume all risks and fully indemnify the repository's creator for any and all uses of the code, analyses, outputs, predictions, and/or results. 
