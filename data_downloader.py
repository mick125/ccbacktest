import pickle as pkl
import pandas as pd
from Historic_Crypto import HistoricalData

pair = 'BTC-USD'
start_datetime = '2018-01-01-00-00'
# start_datetime = '2021-12-31-23-00'  # test purposes
end_datetime = '2018-12-31-23-59'
# end_datetime = '2021-12-31-23-59'

# download data from CoinBase
data_df = HistoricalData(pair, 60, start_date=start_datetime, end_date=end_datetime).retrieve_data()

# save data
with open(f'data_crypto/{pair}_{start_datetime[:10]}_to_{end_datetime[:10]}.pkl', 'wb') as file:
    pkl.dump(data_df, file)

pd.DataFrame(data_df).to_parquet(f'data_crypto/{pair}_{start_datetime[:10]}_to_{end_datetime[:10]}.parquet')
