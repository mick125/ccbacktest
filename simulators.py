import Wallets

import time
import pandas as pd
import numpy as np
from collections import deque


def a_grid(data: pd.DataFrame, wallet: Wallets.Wallet, quantum, init_buy_rate, profit_rate, n_buy_steps,
           sell_under_top, buy_under_top, verbose=True):
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
    if verbose:
        print('Simulation STARTED')
    start_time = time.time()

    enrich.add_top(data)
    enrich.add_prev_top(data)
    enrich.add_new_top(data)

    def calc_orders(first_buy_rate, first_sell_rate=np.nan):
        column_names = ["buy_rate", "sell_rate", "buy_vol", "sell_vol"]

        buy_order_list = np.array([first_buy_rate * (1 - profit_rate * step) for step in range(n_buy_steps)] + [np.nan])
        sell_order_list = np.array([np.nan, first_sell_rate] +
                                   buy_order_list[1:-1].tolist()) * (1 + profit_rate + wallet.fee)
        buy_vol_list = np.array([quantum for _ in range(n_buy_steps)] + [np.nan])
        sell_vol_list = np.array([np.nan] +
                                 np.multiply(np.divide(buy_vol_list[:-1], buy_order_list[:-1]),
                                             (1 - wallet.fee)).tolist())

        all_cols = np.column_stack((buy_order_list, sell_order_list, buy_vol_list, sell_vol_list))
        return pd.DataFrame(data=all_cols, columns=column_names)

    order_book = calc_orders(init_buy_rate)
    idx = 0

    bought = False
    new_top = False

    portf_max_val = 0
    portf_min_val = float('inf')
    n_levels_used = 0
    n_grid_resets = 0

    for index, row in data.iterrows():

        mid = (row['high'] + row['low']) / 2

        # BUY at lower price
        if row['high'] < order_book["buy_rate"][idx]:
            wallet.buy(order_book["buy_vol"][idx], mid, index)
            if verbose:
                print(f'{index}: BUY low  [{idx}] @ {mid:.7f}, '
                      f'{wallet.quote:05.7f} [quote], {wallet.base:05.7f} [base]')
            idx += 1
            n_levels_used = max(n_levels_used, idx)
            bought = True

        # BUY
        if row['low'] < order_book["buy_rate"][idx] < row['high']:
            wallet.buy(order_book["buy_vol"][idx], order_book["buy_rate"][idx], index)
            if verbose:
                print(f'{index}: BUY  [{idx}] @ {order_book["buy_rate"][idx]:.7f}, '
                      f'{wallet.quote:05.7f} [quote], {wallet.base:05.7f} [base]')
            idx += 1
            n_levels_used = max(n_levels_used, idx)
            bought = True

        # SELL
        if row['low'] < order_book["sell_rate"][idx] < row['high']:
            wallet.sell(order_book["sell_vol"][idx], order_book["sell_rate"][idx] * (1 - 4 * wallet.epsilon), index)
            if verbose:
                print(f'{index}: SELL [{idx - 1}] @ {order_book["sell_rate"][idx]:.7f}, '
                  f'{wallet.quote:05.7f} [quote], {wallet.base:05.7f} [base]')
            idx -= 1

        # --- recalculate grid levels after new top
        # check if upper sell level has been reached
        if row['new_top'] and \
                (order_book["buy_rate"][0] * (1 + profit_rate + wallet.fee) < row['top'] * (1 - sell_under_top)):
            new_top = True
            if verbose:
                print(f'NEW TOP: Min. target: {order_book["buy_rate"][0] * (1 + profit_rate + wallet.fee):.4f}'
                      f' < current: {row["high"]:.4f}'
                      f' < potential sell target {row["top"] * (1 - sell_under_top):.4f}')

        # if so, sell and recalculate grid levels
        # if new_top and bought and (order_book["buy_rate"][0] * (1 + profit_rate + wallet.fee) < row['high'] < row['top'] * (1 - sell_under_top)):
        if new_top and bought and (row['high'] < row['top'] * (1 - sell_under_top)):
            if verbose:
                print(wallet.balance())
                print(f'vol: {order_book["sell_vol"][1]}, '
                      f'rate: {row["top"] * (1 - sell_under_top)}')
            wallet.sell(order_book["sell_vol"][1], row['top'] * (1 - sell_under_top))
            order_book = calc_orders(row['top'] * (1 - buy_under_top))
            bought = False
            new_top = False
            idx = 0
            n_grid_resets += 1
            if verbose:
                print(f'{index}: TOP! Recalculate levels @ {row["high"]:.7f}')

        # update metrics
        portf_min_val = min(portf_min_val, wallet.balance_quote(mid))
        portf_max_val = max(portf_max_val, wallet.balance_quote(mid))

    end_time = time.time()
    if verbose:
        print(f'Simulation FINISHED\nit took {end_time - start_time:.2f} seconds')

    return portf_max_val, portf_min_val, n_levels_used, n_grid_resets


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


import enrich
