import os
import pandas as pd
import pickle as pkl

import utils
from joblib import Parallel, delayed
from pathlib import Path

from Wallets import *
import simulators as sim


def run_grid_loop(pair, start_date, end_date,
                  profit_rate_list, n_steps_list, sell_under_top_list, buy_under_top_list,
                  n_cpu=8):
    """
    Run grid simulation for multiple parameter values in a loop.
    :return:
    """
    quantum = 100
    init_quote = 1000
    data_folder = 'data_crypto'

    # load historical data
    data_df = utils.load_crypto_data(pair, start_date, end_date, data_folder)

    init_buy_rate = data_df["open"][0]

    # run grid bots for all parameter combinations in parallel
    res = Parallel(n_jobs=n_cpu)(delayed(run_grid_once)
                                 (data_df, init_quote, quantum, init_buy_rate,
                                  profit_rate, n_steps, sell_under_top, buy_under_top,
                                  verbose=False)
                                 for profit_rate in profit_rate_list
                                 for n_steps in n_steps_list
                                 for sell_under_top in sell_under_top_list
                                 for buy_under_top in buy_under_top_list)

    res = pd.DataFrame(res, columns=['profit_rate', 'n_steps', 'sell_under_top', 'buy_under_top', 'profit', 'wallet'])
    market_performance = data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] - 1

    print(f'\nMarket performance:\t{market_performance:3.0f} %')

    return res, market_performance


def run_grid_once(data_df, init_vol_quote, quantum, init_buy_rate,
                  profit_rate, n_steps, sell_under_top, buy_under_top, verbose=True):
    """
    Runs a single grid simulation.
    :return: wallet,
    """
    # init wallet
    wallet = Wallet(init_cash_quote=init_vol_quote)
    # do the simulation
    # wallet.init_buy_order(quantum, init_buy)
    sim.a_grid(data_df, wallet, quantum, init_buy_rate,
               profit_rate, n_steps, sell_under_top, buy_under_top,
               verbose=verbose)

    profit = wallet.balance_quote(data_df.iloc[-1]["close"]) / init_vol_quote - 1

    print(f'profit_rate: {profit_rate:.2f}, '
          f'n_steps: {n_steps:>2}, '
          f'sell_under_top: {sell_under_top:.2f}, '
          f'buy_under_top: {buy_under_top:.2f}, '
          f'--> profit: {profit * 100:3.0f} %')

    return profit_rate, n_steps, sell_under_top, buy_under_top, profit, wallet


if __name__ == '__main__':
    # set parameters
    pair = 'ETH-BTC'
    start_date = '2022-01-01'
    end_date = '2022-01-31'
    # end_date = '2022-04-27'
    n_cpu = 1

    profit_rates = [0.02, 0.03, 0.04]       # wanted profit at each trade
    # n_stepss = [10, 8, 6]
    n_stepss = [10]
    sell_under_tops = [0.03]
    buy_under_tops = [0.12]

    run_grid_loop(pair, start_date, end_date,
                  profit_rates, n_stepss, sell_under_tops, buy_under_tops,
                  n_cpu=n_cpu)
