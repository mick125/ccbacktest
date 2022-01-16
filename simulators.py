import Wallets
import pandas as pd


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


def fng(fng_df: pd.DataFrame, data_df: pd.DataFrame, wallet: Wallets.Wallet, quantum: float,
        buy_threshold=30, buy_threshold_filter=1, sell_threshold=60, sell_threshold_filter=1):
    """
    Strategy based on Fear & Greed index from alternative.me
    :param fng_df: fng data
    :param data_df: exchange data
    :param wallet: wallet object
    :param quantum: trading quantum in base currency
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

            print(f'{buy_timestamp}: BUY   @ {rate:.7f}, {wallet.base:05.7f} [base], {wallet.quote:05.7f} [quote]')

        elif not buy and days_above_sell_threshold >= sell_threshold_filter:
            buy_timestamp = index + pd.Timedelta(hours=10)
            rate = data_df.loc[buy_timestamp]['open']
            wallet.sell(wallet.history[-1][2] / wallet.history[-1][1] * (1 - wallet.fee) - 0.0001 / rate, rate)
            buy = True

            print(f'{buy_timestamp}: SELL @ {rate:.7f}, {wallet.base:05.7f} [base], {wallet.quote:05.7f} [quote]')
