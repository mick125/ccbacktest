import pickle as pkl
from Historic_Crypto import HistoricalData

pair = 'ETH-BTC'
start_datetime = '2021-01-01-00-00'

# download data from CoinBase
data_df = HistoricalData(pair, 60, start_datetime).retrieve_data()

# save data
with open(f'data_crypto/{pair}_{start_datetime[:10]}.pkl', 'wb') as file:
    pkl.dump(data_df, file)
