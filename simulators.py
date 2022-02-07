import Wallets

import time
import pandas as pd
import numpy as np
from collections import deque

import enrich


def a_grid(data: pd.DataFrame, wallet: Wallets.Wallet, quantum, profit_rate, init_buy_rate, n_buy_steps, sell_top_hyst):
    """
    Advanced grid bot. Buying strategy for growth added.
    :param data: historical data (additional required columns: 'ath')
    :param wallet: wallet object
    :param quantum: trading quantum in quote currency
    :param profit_rate: target profit rate in each trade
    :param init_buy_rate: rate of first buy order
    :param n_buy_steps: how
    :return:
    """
    print('Simulation STARTED')
    start_time = time.time()

    enrich.add_top(data)
    enrich.add_prev_top(data)
    enrich.add_new_top(data)

    buy_orders = np.array([init_buy_rate * (1 - profit_rate * step) for step in range(n_buy_steps)] + [np.nan])
    sell_orders = np.array([np.nan, np.nan] + buy_orders[1:-1].tolist()) * (1 + profit_rate + wallet.fee)
    idx = 0

    for index, row in data.iterrows():
        # nejakej vypis, aby bylo snesitelnejsi cekani
        #     if index.hour == 6 and index.minute == 0:
        #         print(f"{index}: {row['open']:.02f}", end='\r', flush=True)

        # BUY
        if row['low'] < buy_orders[idx] < row['high']:
            wallet.buy(quantum, buy_orders[idx])
            print(f'{index}: BUY  [{idx}] @ {buy_orders[idx]:.7f},'
                  f'{wallet.quote:05.7f} [quote], {wallet.base:05.7f} [base]')
            idx += 1

        # SELL
        if row['low'] < sell_orders[idx] < row['high']:
            wallet.sell(quantum / buy_orders[idx - 1] * (1 - wallet.fee), sell_orders[idx])
            print(f'{index}: SELL [{idx}] @ {sell_orders[idx]:.7f},'
                  f'{wallet.quote:05.7f} [quote], {wallet.base:05.7f} [base]')
            idx -= 1

        # TODO add upwards buys
        if row['new_top'] and (row['top'] - sell_top_hyst) > buy_orders[0] * (1 + profit_rate - wallet.fee):
            print('PRILOZ')

    end_time = time.time()
    print(f'Simulation FINISHED\nit took {end_time - start_time:.2f} seconds')


def a_grid_vectorized(data: pd.DataFrame):
    """
    NOT FINISHED! An attempt to vectorize the simulation and speed it up.
    :param data: historical data (additional required columns: 'ath')
    :return:
    """
    # add column with ATH
    data['ath'] = data['high'].cummax()
    data['ath_prev'] = data['ath'].shift(1)
    data['new_ath'] = data.apply(lambda x: x['ath'] > x['ath_prev'], axis=1)
    print('THIS FUNCTION IS NOT FINISHED!!! NO ACTUAL STRATEGY!!!')
    # TODO dodelat!
    return data

def idca_1st_approach(data: pd.DataFrame, wallet: Wallets.WalletIdca, quantum, profit_rate, upbuy=False):
    """
    Buys on drops, sells on ups.
    :param data: exchange data
    :param wallet: wallet object
    :param quantum: trading quantum in quote currency
    :param profit_rate: target profit rate in each trade
    :param upbuy: flag whether buys shall be executed during uptrend
    """

    print('Simulation STARTED')

    for index, row in data.iterrows():
        # nejakej vypis, aby bylo snesitelnejsi cekani
        #     if index.hour == 6 and index.minute == 0:
        #         print(f"{index}: {row['open']:.02f}", end='\r', flush=True)

        # BUY
        if row['low'] < wallet.buy_order[1] < row['high']:
            print(f'{index}: BUY   @ {wallet.buy_order[1]:.7f}, ', end='')
                  # f'balance = {wallet.balance_quote(wallet.buy_order[1]):5.7f} [quote]',
            wallet.buy_idca(quantum)
            print(f'{wallet.quote:05.7f} [quote], {wallet.base:05.7f} [base]')

        # SELL
        if len(wallet.sell_orders) != 0 and row['low'] < wallet.sell_orders[-1][1] < row['high']:
            print(f'{index}: SELL  @ {wallet.sell_orders[-1][1]:.7f}, ', end='')
                  # f'balance = {wallet.balance_quote(wallet.sell_order[1]):5.7f} [quote],',
            wallet.sell_idca(quantum)
            print(f'{wallet.quote:05.7f} [quote], {wallet.base:05.7f} [base]')

        if upbuy:  # prikupy smerem nahoru, prevzato z grid bota Trading Santy. Nelibi se mi to.
            if len(wallet.sell_order) == 0:
                wallet.buy_idca(quantum, row['close'], profit_rate)
                print(f"{index}: UPBUY @ {row['close']:.7f},",
                      f"balance = {wallet.balance_quote(wallet.buy_order[1]):5.7f} [quote]")

    print('Simulation FINISHED')


def fng(fng_df: pd.DataFrame, data_df: pd.DataFrame, wallet: Wallets.Wallet, quantum: float,
        buy_threshold=30, buy_threshold_filter=1, sell_threshold=60, sell_threshold_filter=1):
    """
    Strategy quoted on Fear & Greed index from alternative.me
    :param fng_df: fng data
    :param data_df: exchange data
    :param wallet: wallet object
    :param quantum: trading quantum in quote currency
    :param buy_threshold: buy if fng is more than
    :param buy_threshold_filter: for longer than
    :param sell_threshold: sell if fng is less than
    :param sell_threshold_filter: for longer than
    """
    buy = True  # wanna buy flag
    days_below_buy_threshold = 0
    days_above_sell_threshold = 0

    for index, row in fng_df.iterrows():

        days_below_buy_threshold += 1 if row.value <= buy_threshold else 0
        days_above_sell_threshold += 1 if row.value >= sell_threshold else 0

        if buy and days_below_buy_threshold >= buy_threshold_filter:
            buy_timestamp = index + pd.Timedelta(hours=10)
            rate = data_df.loc[buy_timestamp]['open']
            wallet.buy(quantum, rate)
            buy = False

            print(f'{buy_timestamp}: BUY   @ {rate:.7f}, {wallet.quote:05.7f} [quote], {wallet.base:05.7f} [base]')

        elif not buy and days_above_sell_threshold >= sell_threshold_filter:
            buy_timestamp = index + pd.Timedelta(hours=10)
            rate = data_df.loc[buy_timestamp]['open']
            wallet.sell(wallet.history[-1][2] / wallet.history[-1][1] * (1 - wallet.fee) - 0.0001 / rate, rate)
            buy = True

            print(f'{buy_timestamp}: SELL @ {rate:.7f}, {wallet.quote:05.7f} [quote], {wallet.base:05.7f} [base]')
