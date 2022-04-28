import os
import pandas as pd
import pickle as pkl

from Wallets import *
import utils
from pathlib import Path
import simulators as sim


def run_grid_loop(pair, start_date, end_date,
                  profit_rate_list, n_steps_list, sell_under_top_list, buy_under_top_list):
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

    for profit_rate in profit_rate_list:
        for n_steps in n_steps_list:
            for sell_under_top in sell_under_top_list:
                for buy_under_top in buy_under_top_list:
                    prof, _ = run_grid_once(data_df, init_quote, quantum, init_buy_rate,
                                            profit_rate, n_steps, sell_under_top, buy_under_top,
                                            verbose=False)
                    print(f'profit_rate: {profit_rate:.2f} '
                          f'n_steps: {n_steps:>2} '
                          f'sell_under_top: {sell_under_top:.2f} '
                          f'buy_under_top: {buy_under_top:.2f} '
                          f'--> profit: {prof * 100:3.0f} %')

    print(f'\nMarket performance:\t{data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] * 100 - 100:3.0f} %')


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

    # print(f'\nFinal rate is\t\t{data_df.iloc[-1]["close"]:3.3f}')
    # print(f'Profit:\t\t\t\t{wallet.balance_quote(data_df.iloc[-1]["close"]) / init_vol_quote * 100 - 100:3.0f} %')
    # print(f'Market performance:\t{data_df.iloc[-1]["close"] / data_df.iloc[0]["open"] * 100 - 100:3.0f} %')

    return profit, wallet


if __name__ == '__main__':

    # set parameters
    pair = 'ETH-BTC'
    start_date = '2022-01-01'
    end_date = '2022-01-31'
    # end_date = '2022-04-27'

    profit_rates = [0.02, 0.03, 0.04]       # wanted profit at each trade
    n_stepss = [10, 8, 6]
    sell_under_tops = [0.03]
    buy_under_tops = [0.12]

    run_grid_loop(pair, start_date, end_date,
                  profit_rates, n_stepss, sell_under_tops, buy_under_tops)

