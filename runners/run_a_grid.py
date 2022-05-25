import time
import pandas as pd
import numpy as np

from joblib import Parallel, delayed
from pathlib import Path

from Wallets import *
import simulators as sim
import utils


def rolling_window(df, window='60d', step='1d', orig_freq='1m'):
    """
    Generator of rolling windows with datetime index. I had to do it myself because pd.rolling doesn't support step.
    :param df: Dataframe data to roll a window on
    :param window: Window length
    :param step: Step size between the windows.
    :param orig_freq: frequency of the origin (input) data.
    """

    win_length = pd.Timedelta(int(window[:-1]), window[-1]) - pd.Timedelta(int(orig_freq[:-1]), orig_freq[-1])

    start_steps = pd.date_range(start=df.iloc[0].name, end=df.iloc[-1].name - win_length, freq=step)
    end_steps = [date + win_length for date in start_steps]

    for win in zip(start_steps, end_steps):
        yield df.loc[win[0]:win[1]].copy()


def run_grid_loop_param(pair, start_date, end_date,
                        profit_rate_list, n_steps_list, sell_under_top_list, buy_under_top_list, grid_type,
                        init_buy_rate=0, init_buy_rate_add=0, n_cpu=8):
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
        init_buy_rate = data_df["open"][0] + init_buy_rate_add

    # run grid bots for all parameter combinations in parallel
    res = Parallel(n_jobs=n_cpu)(delayed(run_grid_once)
                                 (data_df, profit_rate, n_steps, sell_under_top, buy_under_top,
                                  grid_history_save_path, grid_type,
                                  init_buy_rate=init_buy_rate, init_buy_rate_add=init_buy_rate_add, verbose=False)
                                 for profit_rate in profit_rate_list
                                 for n_steps in n_steps_list
                                 for sell_under_top in sell_under_top_list
                                 for buy_under_top in buy_under_top_list)

    res = pd.DataFrame(res,
                       columns=['start_date', 'end_date', 'market_perf',
                                'init_buy_rate', 'profit_rate', 'n_steps', 'sell_under_top', 'buy_under_top', 'profit',
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


def run_grid_loop_time(pair, start_date, end_date,
                       profit_rate_list, n_steps_list, sell_under_top_list, buy_under_top_list, grid_type,
                       window_length='60d', init_buy_rate_add=0, n_cpu=8):
    """
    Run grid simulation for multiple parameter values in a loop.
    :return:
    """
    # create folder for history saving
    grid_history_save_path = Path(f'out/{pair}_{start_date}_to_{end_date}_{grid_type}-grid_history_rolling-window')
    grid_history_save_path.mkdir(exist_ok=True)

    # load historical data
    data_df = utils.load_crypto_data(pair, start_date, end_date)

    # run grid bots for all parameter combinations in parallel
    res = Parallel(n_jobs=n_cpu)(delayed(run_grid_once)
                                 (window_df, profit_rate, n_steps, sell_under_top, buy_under_top,
                                  grid_history_save_path, grid_type,
                                  init_buy_rate_add=init_buy_rate_add, verbose=False)
                                 for profit_rate in profit_rate_list
                                 for n_steps in n_steps_list
                                 for sell_under_top in sell_under_top_list
                                 for buy_under_top in buy_under_top_list
                                 for window_df in rolling_window(data_df, window=window_length))

    res = pd.DataFrame(res,
                       columns=['start_date', 'end_date', 'market_perf',
                                'init_buy_rate', 'profit_rate', 'n_steps', 'sell_under_top', 'buy_under_top', 'profit',
                                'portf_max_val', 'portf_min_val', 'n_levels_used', 'n_grid_resets',
                                'n_transactions'])

    # save the output to here
    file_name = Path(f'out/{pair}_{start_date}_to_{end_date}_{grid_type}-grid_result_rolling-window.csv')

    # if result file already exists, extend it, do not overwrite
    if file_name.is_file():
        existing_res = pd.read_csv(file_name)
        res = pd.concat([existing_res, res]).drop_duplicates(ignore_index=True)

    res.to_csv(file_name, index=False)

    return res


def run_grid_once(data_df, profit_rate, n_steps, sell_under_top, buy_under_top,
                  grid_history_save_path, grid_type,
                  init_buy_rate=0, init_buy_rate_add=0, verbose=True, init_vol_quote=1000):
    """
    Runs a single grid simulation.
    :return: wallet
    """
    # init wallet
    wallet = Wallet(init_cash_quote=init_vol_quote)

    if init_buy_rate == 0:
        init_buy_rate = data_df["open"][0] + init_buy_rate_add

    # do the simulation
    res = sim.a_grid(data_df, wallet, init_buy_rate,
                     profit_rate, n_steps, sell_under_top, buy_under_top,
                     grid_type, verbose=verbose)

    profit = wallet.balance_quote(data_df.iloc[-1]["close"]) / init_vol_quote - 1

    market_performance = data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] - 1

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
                            columns=['date', 'transaction_type', 'current_grid_level', 'rate',
                                     'amount_quote', 'amount_base',
                                     'total_base', 'total_quote', 'balance_in_quote'])

    file_name = f'start_date-{data_df.iloc[0].name.strftime(utils.date_format_short)}_' \
                f'init-buy-rate-{init_buy_rate:.4f}_' \
                f'profit-rate-{profit_rate:.3f}_' \
                f'n-steps-{n_steps}_' \
                f'sell_under_top-{sell_under_top:.3f}_' \
                f'buy_under_top-{buy_under_top:.3f}'

    wal_hist.to_csv(grid_history_save_path / Path(file_name + '.csv'), index=False)

    return data_df.iloc[0].name, data_df.iloc[-1].name, market_performance, \
           init_buy_rate, profit_rate, n_steps, sell_under_top, buy_under_top, \
           profit, *res, \
           len(wallet.history)


# scripts
def grid_loop_script_param():
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
    add_to_init_buy = 3000

    start_time = time.time()

    print(f'Simulation started, '
          f'total of {len(profit_rates) * len(n_stepss) * len(sell_under_tops) * len(buy_under_tops)} '
          f'simulations will be calculated on {n_cpu} CPUs...\n')

    _, markt_perf = run_grid_loop_param(pair, start_date, end_date,
                                        profit_rates, n_stepss, sell_under_tops, buy_under_tops, grid_type,
                                        init_buy_rate=init_buy,
                                        init_buy_rate_add=add_to_init_buy,
                                        n_cpu=n_cpu)

    print(f'\nMarket performance:\t{markt_perf * 100:3.0f} %')
    print(f'\nSimulation FINISHED\nit took {time.time() - start_time:.2f} seconds')


def grid_loop_script_time():
    """
    Wrapper for run_grid_loop containing all required parameters, saving results to CSV and writing std. outputs.
    """
    # set parameters
    # pair = 'ETH-BTC'
    pair = 'BTC-USD'
    start_date = '2021-01-01'
    end_date = '2021-05-01'
    grid_type = 'log'
    # grid_type = 'lin'
    n_cpu = 16

    # sell_under_tops = np.arange(0.07, 0.16, 0.01)
    # buy_under_tops = np.arange(0.07, 0.16, 0.01)
    profit_rates = [0.09]  # wanted profit at each trade
    n_stepss = [8]
    sell_under_tops = [0.12]
    buy_under_tops = [0.12]
    add_to_init_buy = 0

    start_time = time.time()

    time_delta_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days

    print(f'Simulation started - test in rolling window, '
          f'total of '
          f'{len(profit_rates) * len(n_stepss) * len(sell_under_tops) * len(buy_under_tops) * time_delta_days} '
          f'simulations will be calculated on {n_cpu} CPUs...\n')

    run_grid_loop_time(pair, start_date, end_date,
                       profit_rates, n_stepss, sell_under_tops, buy_under_tops, grid_type,
                       window_length='2d',
                       init_buy_rate_add=add_to_init_buy,
                       n_cpu=n_cpu)

    print(f'\nSimulation FINISHED\nit took {time.time() - start_time:.2f} seconds')


if __name__ == '__main__':
    # grid_loop_script_param()
    grid_loop_script_time()
