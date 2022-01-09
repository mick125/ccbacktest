import Wallets


def idca_1st_approach(data, wallet: Wallets.WalletIdca, quantum, profit_rate, upbuy=False):
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
