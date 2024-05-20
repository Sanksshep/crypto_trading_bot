# Automated Crypto Trading Bot

## Overview
This is an automated crypto trading bot designed to trade on Coinbase using the Coinbase API v3. The bot fetches market data, applies machine learning models to predict buy/sell actions, and executes trades based on the predictions.

## Features
- Automated trading every 12 hours
- Long and short strategies
- Risk management with take profit and stop loss
- Position sizing limited to 50%
- Trades all available cryptocurrencies on Coinbase
- Generates daily reports with graphs

## Requirements
- Python 3.6 or higher
- Coinbase API key with necessary permissions

## Project Structure
crypto_trading_bot/
├── config.json
├── main.py
├── update_config.py
├── sandbox_test.py
├── daily_report.py
├── ml_logic.py
├── backtesting.py
├── bot.log
├── reports/
│ └── daily_report_YYYYMMDD.json
└── README.md


## Configuration

### `config.json`
Create a `config.json` file in the root directory with the following structure:

2. Update Available Cryptocurrencies
Run the update_config.py script to fetch and update the list of available cryptocurrencies:

python update_config.py

3. Run the Main Trading Bot
Run the main.py script to start the trading bot:

python main.py

4. Backtest Models
Run the backtesting.py script to backtest the models on historical data:

python backtesting.py

5. Generate Reports
Run the daily_report.py script to generate daily reports with graphs:

python daily_report.py

6. Test in Sandbox
Run the sandbox_test.py script to test the trading bot in Coinbase's sandbox environment:

python sandbox_test.py

Logging
All events and errors are logged in bot.log.