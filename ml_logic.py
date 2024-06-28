import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import classification_report, accuracy_score 
import numpy as np
import logging
from model_utils import load_config, RollingTimeSeriesSplit
import yfinance as yf
import json
import joblib
import matplotlib.pyplot as plt
from datetime import datetime


# Params
MODEL_PATH = 'models/current_model.pkl'
plt.style.use('seaborn-v0_8')
plt.rcParams['figure.figsize'] = (14,8)


logging.basicConfig(filename='bot.log', level=logging.INFO)

def load_data(symbols):
    """
    Load historical data for training models.
    Placeholder function to be implemented.
    """
    try:
        data = pd.read_csv('data/price_data.csv', index_col='date')
    
    except FileNotFoundError:
        sym_str = " ".join([f'{x}-USD' for x in symbols])
        start_date = '2020-05-01'
        end_date = '2024-04-30'

        data = yf.download(sym_str, start_date, end_date)['Close']
        data.columns.name = None
        data.columns = [x.replace('-USD', '').lower() for x in data.columns]
        data.index.name = 'date'

        data.to_csv('data/price_data.csv')

    logging.info("Loading historical data")
    # Placeholder: Replace with actual data loading logic
    return data

def feature_engineering(data):
    """
    Generate features from raw data.
    """
    logging.info("Starting feature engineering")
    # if 'Close' not in data.columns:
    #     logging.error("Market data does not contain 'close' column")
    #     return pd.DataFrame()  # Return empty DataFrame if 'close' column is missing

    # if len(data) < 15:
    #     logging.warning("Not enough data points to calculate SMA and EMA")
    #     return pd.DataFrame()  # Return empty DataFrame if not enough data points

    cols = data.columns.to_list()

    for col in cols:
        data[f'{col}_sma'] = data[col].rolling(window=15).mean()
        data[f'{col}_ema'] = data[col].ewm(span=15, adjust=False).mean()
        data[f'{col}_ret'] = np.log(data[col]/data[col].shift())
        data[f'{col}_1d_ret'] = data[f'{col}_ret'].shift(-1)
        data[f'{col}_1d_target'] = np.where(data[f'{col}_1d_ret'] >= 0, 1, 0)
      
    logging.info("Completed feature engineering")
    logging.info("Saving feature set ")
    data.to_csv('data/feature_set.csv', index=False)

    return data

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
    plt.savefig(f'images/model_test_{model_test_date}.png')
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

    print('model saved')

    if run_test:
        test_model(data, model, symbols, train_end_date, model_test_date)

if __name__ == "__main__":
    main()




