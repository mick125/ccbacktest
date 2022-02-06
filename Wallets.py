from collections import deque


class Wallet:
    """
    Wallet of two currencies.
    Base - currency I hold initially.
    Quote - currency I intend to buy.
    """

    def __init__(self, init_cash_base=1000, init_cash_quote=0, profit_rate=0.1, fee=0.001):
        """
        :param init_cash_base: initial amount of base currency in the wallet
        :param init_cash_quote: initial amount of quote currency in the wallet
        :param profit_rate: target profit in each trade
        :param fee: transaction fee
        """
        self.base = init_cash_base      # primary currency
        self.quote = init_cash_quote    # currency to buy
        self.profit_rate = profit_rate
        self.fee = fee

        self.history = list()           # list of executed transactions; element structure (buy/sell, rate, amount_base)

    def buy(self, amount_base, rate):
        """
        Buy quote currency.
        :param amount_base: volume of base currency to be sold
        :param rate: exchange rate
        """
        if self.base - amount_base >= 0:
            self.base -= amount_base
            self.quote += amount_base / rate * (1 - self.fee)

            self.history.append(('buy', rate, amount_base * (1 - self.fee)))
            return 0
        else:
            print('Not enough base currency, cannot buy!')
            return 1

    def sell(self, amount_quote, rate):
        """
        Sell quote currency.
        :param amount_quote: volume of quote currency to be sold
        :param rate: exchange rate
        """
        if self.quote - amount_quote >= 0:
            self.base += amount_quote * rate * (1 - self.fee)
            self.quote -= amount_quote

            self.history.append(('sell', rate, amount_quote * rate * (1 - self.fee)))
            return 0
        else:
            print('Not enough quote currency, cannot sell!')
            return 1

    def balance_base(self, current_rate):
        """
        Get current wallet balance in base currency.
        :param current_rate: current exchange rate
        :return: current wallet balance
        """
        return self.base + self.quote * current_rate

    def balance(self):
        """
        Get wallet balance in both currencies.
        :return: balance in base and quote currency
        """
        return self.base, self.quote


class WalletIdca(Wallet):
    """
    Wallet with extended buy and sell methods and order books.
    """
    def __init__(self, init_cash_base=1500, init_cash_quote=0, fee=0.001, profit_rate=0.1, crypto_sell_frac=1.):
        """
        :param crypto_sell_frac: fraction of crypto associated with current operation which shall be sold
        """
        super().__init__(init_cash_base, init_cash_quote, profit_rate, fee)
        self.crypto_sell_frac = crypto_sell_frac

        self.buy_order = None
        # self.sell_order = None

        self.sell_orders = deque()

        self.epsilon = 0.0001

    def init_buy_order(self, amount_base, rate):
        """
        Set the first buy order
        """
        self.buy_order = (amount_base, rate)
        self.sell_order = None

    def buy_idca(self, next_buy_order_amount_base):
        """
        Buy quote currency and place new orders based on last buy order.
        """
        amount_base, rate = self.buy_order

        if self.buy(amount_base, rate) == 0:    # if there's enough base...
            self.buy_order = (next_buy_order_amount_base, rate * (1. - self.profit_rate))
            self.sell_orders.append((amount_base / rate * self.crypto_sell_frac * (1 - self.fee - self.epsilon / rate),
                                     rate * (1. + self.profit_rate)))
            # self.sell_order = (amount_base / rate * self.crypto_sell_frac * (1 - self.fee - self.epsilon / rate),
            #                    rate * (1. + self.profit_rate))

    def sell_idca(self, next_buy_order_amount_base):
        """
        Sell quote currency and place new orders based on last buy order.
        """
        amount_quote, rate = self.sell_orders.pop()

        if self.sell(amount_quote, rate) == 0:    # if there's enough quote...
            self.buy_order = (next_buy_order_amount_base, rate * (1 - self.profit_rate))
            # self.sell_order = None
