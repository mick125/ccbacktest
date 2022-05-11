import os
import time
import math

import numpy as np
import pandas as pd
import pickle as pkl

import utils
from joblib import Parallel, delayed
from pathlib import Path

from Wallets import *
import simulators as sim


def run_grid_loop(pair, start_date, end_date,
                  profit_rate_list, n_steps_list, sell_under_top_list, buy_under_top_list, init_buy_rate=0,
                  n_cpu=8):
    """
    Run grid simulation for multiple parameter values in a loop.
    :return:
    """
    # create folder for history saving
    grid_history_save_path = Path(f'out/{pair}_{start_date}_to_{end_date}_grid-history')
    grid_history_save_path.mkdir(exist_ok=True)

    # load historical data
    data_df = utils.load_crypto_data(pair, start_date, end_date)

    if init_buy_rate == 0:
        init_buy_rate = data_df["open"][0]

    # run grid bots for all parameter combinations in parallel
    res = Parallel(n_jobs=n_cpu)(delayed(run_grid_once)
                                 (data_df, init_buy_rate, profit_rate, n_steps, sell_under_top, buy_under_top,
                                  grid_history_save_path, verbose=False)
                                 for profit_rate in profit_rate_list
                                 for n_steps in n_steps_list
                                 for sell_under_top in sell_under_top_list
                                 for buy_under_top in buy_under_top_list)

    res = pd.DataFrame(res, columns=['profit_rate', 'n_steps', 'sell_under_top', 'buy_under_top', 'profit',
                                     'portf_max_val', 'portf_min_val', 'n_levels_used', 'n_grid_resets',
                                     'n_transactions'])

    market_performance = data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] - 1

    print(f'\nMarket performance:\t{market_performance * 100:3.0f} %')

    return res, market_performance


def run_grid_once(data_df, init_buy_rate, profit_rate, n_steps, sell_under_top, buy_under_top,
                  grid_history_save_path, verbose=True, init_vol_quote=1000):
    """
    Runs a single grid simulation.
    :return: wallet
    """
    quantum = math.floor(init_vol_quote / n_steps)

    # init wallet
    wallet = Wallet(init_cash_quote=init_vol_quote)
    # do the simulation
    res = sim.a_grid(data_df, wallet, quantum, init_buy_rate,
                     profit_rate, n_steps, sell_under_top, buy_under_top,
                     verbose=verbose)

    profit = wallet.balance_quote(data_df.iloc[-1]["close"]) / init_vol_quote - 1

    print(f'profit_rate: {profit_rate:.2f}, '
          f'n_steps: {n_steps:>2}, '
          f'sell_under_top: {sell_under_top:.2f}, '
          f'buy_under_top: {buy_under_top:.2f}, '
          f'portf_max_val [q]: {res[0]:.4f}, '
          f'portf_min_val [q]: {res[1]:.4f}, '
          f'n_levels_used: {res[2]}, '
          f'n_grid_resets: {res[3]}, '
          f'n_transactions: {len(wallet.history)} '
          f'--> profit: {profit * 100:3.0f} %')

    # saving history to a file
    wal_hist = pd.DataFrame(wallet.history,
                            columns=['transaction', 'date', 'rate', 'amount_quote', 'amount_base', 'balance_quote'])

    file_name = f'init-buy-rate-{init_buy_rate:.4f}_' \
                f'profit-rate-{profit_rate:.3f}_' \
                f'n-steps-{n_steps}_' \
                f'sell_under_top-{sell_under_top:.3f}_' \
                f'buy_under_top-{buy_under_top:.3f}'

    wal_hist.to_csv(grid_history_save_path / Path(file_name + '.csv'), index=False)

    return profit_rate, n_steps, sell_under_top, buy_under_top, profit, *res, len(wallet.history)


# scripts
def grid_loop_script():
    """
    Wrapper for run_grid_loop containing all required parameters, saving results to CSV and writing std. outputs.
    """
    # set parameters
    # pair = 'ETH-BTC'
    pair = 'BTC-USD'
    start_date = '2020-01-01'
    end_date = '2020-04-30'
    n_cpu = 16

    # profit_rates = [0.02, 0.03, 0.04, 0.06]  # wanted profit at each trade
    profit_rates = [0.02]  # wanted profit at each trade
    n_stepss = np.arange(1, 72, 10)
    # n_stepss = [51]
    sell_under_tops = [0.03]
    buy_under_tops = [0.12]
    init_buy = 0

    start_time = time.time()

    print(f'Simulation started, '
          f'total of {len(profit_rates) * len(n_stepss) * len(sell_under_tops) * len(buy_under_tops)}'
          f' simulations will be calculated on {n_cpu} CPUs...\n')

    res_mult, _ = run_grid_loop(pair, start_date, end_date,
                                profit_rates, n_stepss, sell_under_tops, buy_under_tops, init_buy_rate=init_buy,
                                n_cpu=n_cpu)

    file_name = Path(f'out/{pair}_{start_date}_to_{end_date}_grid-result.csv')

    # if result file already exists, extend it, do not overwrite
    if file_name.is_file():
        existing_res = pd.read_csv(file_name)
        res_mult = pd.concat([existing_res, res_mult]).drop_duplicates(ignore_index=True)

    res_mult.to_csv(file_name, index=False)

    print(f'\nSimulation FINISHED\nit took {time.time() - start_time:.2f} seconds')


if __name__ == '__main__':
    grid_loop_script()
