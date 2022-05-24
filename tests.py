import pandas as pd
import pickle as pkl

from multiprocessing import Pool
import os

from Wallets import *
import simulators as sim
from runners.run_a_grid import *
import utils


# scripts

def test_run_grid_once():
    """
    Script for test-running the run_grid_once function. All input parameters are hard-coded here on purpose.
    """
    pair = 'ETH-BTC'
    start_date = '2022-01-01'
    end_date = '2022-01-31'

    quantum = 100
    init_quote = 1000
    profit_rate = 0.02  # wanted profit at each trade
    n_steps = 10
    sell_under_top = 0.03
    buy_under_top = 0.12

    # load historical data
    data_df = utils.load_crypto_data(pair, start_date, end_date)

    init_buy_rate = data_df["open"][0] * 1.1

    # run grid bots for all parameter combinations in parallel
    run_grid_once(data_df, init_quote, quantum, init_buy_rate,
                  profit_rate, n_steps, sell_under_top, buy_under_top,
                  verbose=True)

def f(x):
    print('Child process id:', os.getpid())
    print('x', x)

    return x*2

if __name__ == '__main__':

    start_time = time.time()

    print('Parent process id:', os.getpid())
    with Pool(5) as p:
        print(p.map(f, [1, 2, 3]))

    # init wallet
    # wallet = Wallet()
    # wallet = WalletIdca()

    # wallet.buy(100, 1.3)
    # wallet.sell(10, 1.4)

    # wallet.init_buy_order(1600, 1.5)
    # wallet.buy_idca(100)
    # wallet.sell_idca(100)
    #
    # print(wallet.balance())
    # print(*wallet.history, sep='\n')

    # test_run_grid_once()

    print(f'\nSimulation FINISHED\nit took {time.time() - start_time:.2f} seconds')
