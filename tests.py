import pandas as pd
import pickle as pkl

from Wallets import *
import simulators as sim

# init wallet
# wallet = Wallet()
wallet = WalletIdca()

# wallet.buy(100, 1.3)
# wallet.sell(10, 1.4)

wallet.init_buy_order(1600, 1.5)
wallet.buy_idca(100)
wallet.sell_idca(100)

print(wallet.balance())
print(*wallet.history, sep='\n')
