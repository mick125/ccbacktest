from Wallets import *
import utils
from pathlib import Path
import simulators as sim

# set parameters
start_date = '2021-01-01'
end_date = '2021-12-31'

data_folder = 'data_crypto'

# BTC/USD
pair = 'BTC-USD'
quantum = 100
init_cash = 1000

# load historical data
data_df = utils.load_crypto_data(pair, start_date, end_date, data_folder)

# ---- FnG
# load FnG data
fng_json_path = Path(data_folder, 'FnG_to_2022-01-11.json')
# init wallet
wallet = Wallet(init_cash)
fng_df = utils.load_fng_data(fng_json_path, start_date, end_date)
sim.fng(fng_df, data_df, wallet, quantum)

print(f'\nFinal rate is\t\t{data_df.iloc[-1]["close"]:3.3f}')
print(f'Profit:\t\t\t\t{wallet.balance_base(data_df.iloc[-1]["close"]) / init_cash * 100 - 100:3.0f} %')
print(f'Market performance:\t{data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] * 100 - 100:3.0f} %')
