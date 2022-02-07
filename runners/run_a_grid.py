import os
import pandas as pd
import pickle as pkl

from Wallets import *
import utils
from pathlib import Path
import simulators as sim

# set parameters
start_date = '2021-12-01'
end_date = '2021-12-31'

data_folder = 'data_crypto'


# BTC/USD
pair = 'BTC-USD'
profit_rate = 0.02       # wanted profit at each trade
quantum = 100
init_quote = 1000
# init_base = 0
init_buy = 51000  # limit price for first buy
n_steps = 10

# load historical data
data_df = utils.load_crypto_data(pair, start_date, end_date, data_folder)

# ---- advanced grid
# init wallet
wallet = Wallet(init_cash_quote=init_quote)
# do the simulation
# wallet.init_buy_order(quantum, init_buy)
sim.a_grid(data_df, wallet, quantum, profit_rate, init_buy, n_steps)

print(f'\nFinal rate is\t\t{data_df.iloc[-1]["close"]:3.3f}')
print(f'Profit:\t\t\t\t{wallet.balance_quote(data_df.iloc[-1]["close"]) / init_quote * 100 - 100:3.0f} %')
print(f'Market performance:\t{data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] * 100 - 100:3.0f} %')
