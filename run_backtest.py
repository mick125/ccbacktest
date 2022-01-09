import pandas as pd
import pickle as pkl

from Wallets import *
import simulators as sim

# set parameters

# ADA/USDT
pair = 'ADA-USD'
start_date = '2021-03-18'
init_buy = 1.5
profit_rate = 0.1   # 10%
quantum = 100       # $100
init_cash = 1500    # $1000

# ETH/BTC
# pair = 'ETH-BTC'
# start_date = '2021-01-01'
# init_buy = 0.025  # limit price for first buy
# profit_rate = 0.02       # wanted profit at each trade
# quantum = 0.00072
# init_cash = 0.022

# load data
with open(f'data_crypto/{pair}_{start_date}.pkl', 'rb') as file:
    data_df = pkl.load(file)

# init wallet
wallet = WalletIdca(init_cash_base=init_cash)
wallet.init_buy_order(quantum, 1.5)

# do the simulation
sim.idca_1st_approach(data_df, wallet, quantum, profit_rate, upbuy=False)

print('Buy order', wallet.buy_order)
print('Sell orders', wallet.sell_orders)
print(f'\nFinal rate is\t\t{data_df.iloc[-1]["close"]:3.3f}')
print(f'Profit:\t\t\t\t{wallet.balance_base(data_df.iloc[-1]["close"]) / init_cash * 100 - 100:3.0f} %')
print(f'Market performance:\t{data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] * 100 - 100:3.0f} %')
