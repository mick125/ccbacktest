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


def run_grid_param_list(pair, start_date, end_date,
                      profit_rate_list, n_steps_list, sell_under_top_list, buy_under_top_list, grid_type,
                      init_buy_rate=0, n_cpu=8):
    """
    Run grid simulation for multiple parameter values in a loop.
    :return:
    """
    # create folder for history saving
    grid_history_save_path = Path(f'out/{pair}_{start_date}_to_{end_date}_grid-history')
    grid_history_save_path.mkdir(exist_ok=True)

    # create parameter list
    par_list = list()
    for profit_rate in profit_rate_list:
        for n_steps in n_steps_list:
            for sell_under_top in sell_under_top_list:
                for buy_under_top in buy_under_top_list:
                    par_list.append([profit_rate, n_steps, sell_under_top, buy_under_top])

    par_list = pd.DataFrame(par_list, columns=['profit_rate', 'n_steps', 'sell_under_top', 'buy_under_top'])

    # drop meaningless numbers of steps
    if grid_type == 'lin':
        par_list.drop(par_list[np.floor(1 / par_list['profit_rate']) < par_list['n_steps']].index, inplace=True)

    # load historical data
    data_df = utils.load_crypto_data(pair, start_date, end_date)

    # remove parameter sets which are present in result table
    par_list = par_list.merge(data_df[par_list.columns], on=[par_list.columns], indicator=True)
    par_list = par_list[par_list['_merge'] == 'left_only'].drop(columns=['_merge'], inplace=True)

    # add further input parameters

    if init_buy_rate == 0:
        init_buy_rate = data_df["open"][0]

    # run grid bots for all parameter combinations in parallel
    res = Parallel(n_jobs=n_cpu)(delayed(run_grid_once)
                                 (data_df, init_buy_rate, profit_rate, n_steps, sell_under_top, buy_under_top,
                                  grid_history_save_path, grid_type, verbose=False)
                                 for profit_rate in profit_rate_list
                                 for n_steps in n_steps_list
                                 for sell_under_top in sell_under_top_list
                                 for buy_under_top in buy_under_top_list)

    res = pd.DataFrame(res, columns=['profit_rate', 'n_steps', 'sell_under_top', 'buy_under_top', 'profit',
                                     'portf_max_val', 'portf_min_val', 'n_levels_used', 'n_grid_resets',
                                     'n_transactions'])

    market_performance = data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] - 1

    # save the output to here
    file_name = Path(f'out/{pair}_{start_date}_to_{end_date}_{grid_type}-grid_result.csv')

    # if result file already exists, extend it, do not overwrite
    if file_name.is_file():
        existing_res = pd.read_csv(file_name)
        res = pd.concat([existing_res, res]).drop_duplicates(ignore_index=True)

    res.to_csv(file_name, index=False)

    return res, market_performance


def run_grid_loop(pair, start_date, end_date,
                  profit_rate_list, n_steps_list, sell_under_top_list, buy_under_top_list, grid_type,
                  init_buy_rate=0, n_cpu=8):
    """
    Run grid simulation for multiple parameter values in a loop.
    :return:
    """
    # create folder for history saving
    grid_history_save_path = Path(f'out/{pair}_{start_date}_to_{end_date}_{grid_type}-grid_history')
    grid_history_save_path.mkdir(exist_ok=True)

    # load historical data
    data_df = utils.load_crypto_data(pair, start_date, end_date)

    if init_buy_rate == 0:
        init_buy_rate = data_df["open"][0] + 5000

    # run grid bots for all parameter combinations in parallel
    res = Parallel(n_jobs=n_cpu)(delayed(run_grid_once)
                                 (data_df, init_buy_rate, profit_rate, n_steps, sell_under_top, buy_under_top,
                                  grid_history_save_path, grid_type, verbose=False)
                                 for profit_rate in profit_rate_list
                                 for n_steps in n_steps_list
                                 for sell_under_top in sell_under_top_list
                                 for buy_under_top in buy_under_top_list)

    res = pd.DataFrame(res, columns=['profit_rate', 'n_steps', 'sell_under_top', 'buy_under_top', 'profit',
                                     'portf_max_val', 'portf_min_val', 'n_levels_used', 'n_grid_resets',
                                     'n_transactions'])

    market_performance = data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] - 1

    # save the output to here
    file_name = Path(f'out/{pair}_{start_date}_to_{end_date}_{grid_type}-grid_result.csv')

    # if result file already exists, extend it, do not overwrite
    if file_name.is_file():
        existing_res = pd.read_csv(file_name)
        res = pd.concat([existing_res, res]).drop_duplicates(ignore_index=True)

    res.to_csv(file_name, index=False)

    return res, market_performance


def run_grid_once(data_df, init_buy_rate, profit_rate, n_steps, sell_under_top, buy_under_top,
                  grid_history_save_path, grid_type, verbose=True, init_vol_quote=1000):
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
                     grid_type, verbose=verbose)

    profit = wallet.balance_quote(data_df.iloc[-1]["close"]) / init_vol_quote - 1

    print(f'profit_rate: {profit_rate:.2f}, '
          f'n_steps: {n_steps:>2}, '
          f'sell_under_top: {sell_under_top:.2f}, '
          f'buy_under_top: {buy_under_top:.2f}, '
          f'n_levels_used: {res[2]}, '
          f'n_grid_resets: {res[3]}, '
          f'n_transactions: {len(wallet.history)} '
          f'--> profit: {profit * 100:3.0f} %')
        # f'portf_max_val [q]: {res[0]:.4f}, '
        # f'portf_min_val [q]: {res[1]:.4f}, '

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
    start_date = '2022-01-04'
    end_date = '2022-05-05'
    # grid_type = 'log'
    grid_type = 'lin'
    n_cpu = 1

    # profit_rates = np.arange(0.01, 0.2, 0.02)  # wanted profit at each trade
    # n_stepss = np.arange(8, 30, 2)
    sell_under_tops = np.arange(0.02, 0.25, 0.02)
    buy_under_tops = np.arange(0.02, 0.2, 0.02)
    profit_rates = [0.07]  # wanted profit at each trade
    n_stepss = [51]
    # sell_under_tops = [0.03]
    # buy_under_tops = [0.12]
    init_buy = 0

    start_time = time.time()

    print(f'Simulation started, '
          f'total of {len(profit_rates) * len(n_stepss) * len(sell_under_tops) * len(buy_under_tops)} '
          f'simulations will be calculated on {n_cpu} CPUs...\n')

    # _, markt_perf = run_grid_param_list(pair, start_date, end_date,
    _, markt_perf = run_grid_loop(pair, start_date, end_date,
                                  profit_rates, n_stepss, sell_under_tops, buy_under_tops, grid_type,
                                  init_buy_rate=init_buy,
                                  n_cpu=n_cpu)

    print(f'\nMarket performance:\t{markt_perf * 100:3.0f} %')
    print(f'\nSimulation FINISHED\nit took {time.time() - start_time:.2f} seconds')


if __name__ == '__main__':
    grid_loop_script()
