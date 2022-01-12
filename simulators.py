import Wallets
import json
import pandas as pd
from datetime import datetime


def idca_1st_approach(data: pd.DataFrame, wallet: Wallets.WalletIdca, quantum, profit_rate, upbuy=False):
    """
    Buys on drops, sells on ups.
    :param data: exchange data
    :param wallet: wallet object
    :param quantum: trading quantum in base currency
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
                  # f'balance = {wallet.balance_base(wallet.buy_order[1]):5.7f} [base]',
            wallet.buy_idca(quantum)
            print(f'{wallet.base:05.7f} [base], {wallet.quote:05.7f} [quote]')

        # SELL
        if len(wallet.sell_orders) != 0 and row['low'] < wallet.sell_orders[-1][1] < row['high']:
            print(f'{index}: SELL  @ {wallet.sell_orders[-1][1]:.7f}, ', end='')
                  # f'balance = {wallet.balance_base(wallet.sell_order[1]):5.7f} [base],',
            wallet.sell_idca(quantum)
            print(f'{wallet.base:05.7f} [base], {wallet.quote:05.7f} [quote]')

        if upbuy:  # prikupy smerem nahoru, prevzato z grid bota Trading Santy. Nelibi se mi to.
            if len(wallet.sell_order) == 0:
                wallet.buy_idca(quantum, row['close'], profit_rate)
                print(f"{index}: UPBUY @ {row['close']:.7f},",
                      f"balance = {wallet.balance_base(wallet.buy_order[1]):5.7f} [base]")

    print('Simulation FINISHED')


def fng(fng_json_path: str, data: pd.DataFrame, wallet: Wallets.Wallet, quantum, buy_threshold=30, sell_threshold=60):
    """
    Strategy based on Fear & Greed index from alternative.me
    :param fng_json_path: path to json with historical FnG data
    :param data: exchange data
    :param wallet: wallet object
    :param quantum: trading quantum in base currency
    :param buy_threshold: buy if fng is more than
    :param sell_threshold: sell if fng is less than
    """
    fng_df = json.load(open(fng_json_path))
    fng_df = pd.DataFrame(fng_df['data'])
    fng_df['value'] = fng_df['value'].astype(int)
    fng_df['timestamp'] = fng_df['timestamp'].astype(int)
    fng_df['timestamp'] = fng_df['timestamp'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d'))
    fng_df = fng_df.set_index(pd.to_datetime(fng_df['timestamp']))
    fng_df = fng_df.drop(['value_classification', 'time_until_update', 'timestamp'], axis=1)
    fng_df = fng_df.sort_index()

    # reduce the dataset temporarily
    fng_df = fng_df[(fng_df.index < '2022-01-01') & (fng_df.index > '2021-01-01')]

    buy = True  # wanna buy flag

    for index, row in fng_df.iterrows():

        # print(index, row.value)

        if buy and row.value <= buy_threshold:
            timestamp = (index + pd.Timedelta(hours=10)).strftime('%Y-%m-%d-%H-%M')
            rate = data.loc[timestamp]['open']
            wallet.buy(quantum, rate)
            buy = False

            print(f'{timestamp}: BUY   @ {rate:.7f}, {wallet.base:05.7f} [base], {wallet.quote:05.7f} [quote]')

        elif not buy and row.value >= sell_threshold:
            timestamp = (index + pd.Timedelta(hours=10)).strftime('%Y-%m-%d-%H-%M')
            rate = data.loc[timestamp]['open']
            wallet.sell(wallet.history[-1][2] / wallet.history[-1][1] * (1 - wallet.fee) - 0.0001 / rate, rate)
            buy = True

            print(f'{timestamp}: SELL @ {rate:.7f}, {wallet.base:05.7f} [base], {wallet.quote:05.7f} [quote]')
