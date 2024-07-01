import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import classification_report, accuracy_score 
import numpy as np
import logging
from utils import load_data, feature_engineering, load_config, RollingTimeSeriesSplit
import yfinance as yf
import json
import joblib
import matplotlib.pyplot as plt
from datetime import datetime
from coinbase import jwt_generator 


# Params
MODEL_PATH = 'models/current_model.pkl'
plt.style.use('seaborn-v0_8')
plt.rcParams['figure.figsize'] = (14,8)


logging.basicConfig(filename='bot.log', level=logging.INFO)

def train_model(data, symbols, train_end_date):
    """
    Train a machine learning model on the data.
    """
    logging.info("Starting model training")

    # Split data into features and labels
    X = data[[f'{x.lower()}_sma' for x in symbols] + [f'{x.lower()}_ema' for x in symbols]].loc[:train_end_date]
    y = data[[f'{x.lower()}_1d_target' for x in symbols]].loc[:train_end_date]
      
    # Instantiate Rolling Time Series Split method
    tscv = RollingTimeSeriesSplit(n_splits = 5, train_size=120, test_size=15)

    model = RandomForestClassifier(random_state=42)
    param_grid = {'n_estimators': [100, 200], 'max_depth': [5, 10, None]}

    grid_search = GridSearchCV(model, param_grid, cv=tscv)
    grid_search.fit(X, y)

    best_model = grid_search.best_estimator_

    joblib.dump(best_model, f'models/current_model.pkl')
        
    logging.info("Model training completed")
    
    return best_model

def test_model(data, model, symbols, train_end_date, model_test_date):

    # Create test set
    test_set = data[train_end_date: ]
    X_test = test_set[[f'{x.lower()}_sma' for x in symbols] + [f'{x.lower()}_ema' for x in symbols]]
    y_test = test_set[[f'{x.lower()}_1d_target' for x in symbols]]
    
    # Create predictions
    y_pred = model.predict(X_test)
    
    # Performance metrics
    for ix, sym in enumerate(symbols):
        print(sym)
        print(classification_report(y_test[f'{sym.lower()}_1d_target'], y_pred[:,ix], zero_division = np.nan))

    # Generate signals from model
    df_perf = test_set[[f'{x.lower()}' for x in symbols]].copy()

    for ix, sym in enumerate(df_perf.columns):
        df_perf[f'{sym}_ret'] = np.log(df_perf[sym]/df_perf[sym].shift(1))
        df_perf[f'{sym}_pred'] = y_pred[:,ix]
        df_perf[f'{sym}_signal'] = np.where(df_perf[f'{sym}_pred'].values  > 0, 1, -1)
        df_perf[f'{sym}_strat_ret'] = df_perf[f'{sym}_signal'].shift(1) * df_perf[f'{sym}_ret']
        df_perf[f'{sym}_bh'] = df_perf[f'{sym}_ret'].cumsum()*100
        df_perf[f'{sym}_strat'] = df_perf[f'{sym}_strat_ret'].cumsum()*100

    syms = [x.lower() for x in symbols]
    fig, axes = plt.subplots(2,2, sharey=True, sharex=True)

    for ix, ax in enumerate(fig.axes):
        df_plot = df_perf[[f'{syms[ix]}_strat', f'{syms[ix]}_bh']]
        ax.plot(df_plot.index, df_perf[[f'{syms[ix]}_strat', f'{syms[ix]}_bh']])
        ax.tick_params(axis='x', rotation=45)
        ax.legend(['Strategy', 'Buy and hold'])
        ax.set_xlabel('')
        if ix % 2 == 0:
            ax.set_ylabel('Cumulative Return (%)')
        ax.set_title(f'Strategy vs Buy and hold {syms[ix].upper()}-USD')
    plt.savefig(f'models/model_test_{model_test_date}.png')
    plt.show()

    # Get cumulative performance
    ret_calc = [[f'{sym}_bh', f'{sym}_strat'] for sym in syms]
    print(df_perf[[y for x in ret_calc for y in x]].iloc[-1])


def main(run_test=True):
    config = load_config()
    symbols = config['cryptocurrencies']
    train_end_date = config['train_end_date']
    model_test_date = datetime.now().strftime('%Y-%m-%d')

    data = load_data(symbols)
    data = feature_engineering(data)
    model = train_model(data, symbols, train_end_date)

    logging.info('model saved')

    if run_test:
        test_model(data, model, symbols, train_end_date, model_test_date)

if __name__ == "__main__":
    main()




