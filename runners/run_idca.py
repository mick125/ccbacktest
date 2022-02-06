import os
import pandas as pd
import pickle as pkl

from Wallets import *
import utils
from pathlib import Path
import simulators as sim

# set parameters
start_date = '2021-01-01'
end_date = '2021-12-31'

data_folder = 'data_crypto'

# ADA/USDT
# pair = 'ADA-USD'
# start_date = '2021-03-18'
# init_buy = 1.5
# profit_rate = 0.1   # 10%
# quantum = 100       # $100
# init_cash = 1500    # $1000

# ETH/BTC
# pair = 'ETH-BTC'
# init_buy = 0.025  # limit price for first buy
# profit_rate = 0.02       # wanted profit at each trade
# quantum = 0.00072
# init_cash = 0.022

# BTC/USD
pair = 'BTC-USD'
init_buy = 45000  # limit price for first buy
profit_rate = 0.02       # wanted profit at each trade
quantum = 100
init_cash = 1000

# load historical data
data_df = utils.load_crypto_data(pair, start_date, end_date, data_folder)

# ---- iDCA
# init wallet
wallet = WalletIdca(init_cash_quote=init_cash)
# do the simulation
wallet.init_buy_order(quantum, init_buy)
sim.idca_1st_approach(data_df, wallet, quantum, profit_rate, upbuy=False)

print(f'\nFinal rate is\t\t{data_df.iloc[-1]["close"]:3.3f}')
print(f'Profit:\t\t\t\t{wallet.balance_quote(data_df.iloc[-1]["close"]) / init_cash * 100 - 100:3.0f} %')
print(f'Market performance:\t{data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] * 100 - 100:3.0f} %')
