def idca_1st_approach(data, wallet, quantum, profit_rate, upbuy=False):
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
        if row['low'] < wallet.buys[-1] < row['high']:
            print(f'{index}: BUY   @ {wallet.buys[-1]:.7f},',
                  f'ballance = {wallet.get_balance_base(wallet.buys[-1]):5.7f} [base]')
            wallet.buy(quantum, wallet.buys[-1], profit_rate)
        #         print(wallet.buys, wallet.sells)

        # SELL
        if len(wallet.sells) != 0 and row['low'] < wallet.sells[-1] < row['high']:
            print(f'{index}: SELL  @ {wallet.sells[-1]:.7f},',
                  f'ballance = {wallet.get_balance_base(wallet.sells[-1]):5.7f} [base],',
                  f'{wallet.base:05.7f} [base], {wallet.quote:05.7f} [quote]')
            wallet.sell(quantum, wallet.sells[-1], profit_rate)
        #         print(wallet.buys, wallet.sells)

        if upbuy:   # prikupy smerem nahoru, prevzato z grid bota Trading Santy. Nelibi se mi to.
            if len(wallet.sells) == 0:
                wallet.buy(quantum, row['close'], profit_rate)
                print(f"{index}: UPBUY @ {row['close']:.7f},",
                      f"ballance = {wallet.get_balance_base(wallet.buys[-1]):5.7f} [base]")

    print('Simulation FINISHED')
