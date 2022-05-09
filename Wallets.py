from collections import deque


class Wallet:
    """
    Wallet of two currencies.
    Base - base currency (first in the currency pair)
    Quote - quote currency (second in the currency pair)
    """

    epsilon = 0.0001

    def __init__(self, init_cash_quote=1000, init_cash_base=0, fee=0.001):
        """
        :param init_cash_quote: initial amount of quote currency in the wallet
        :param init_cash_base: initial amount of base currency in the wallet
        :param profit_rate: target profit in each trade
        :param fee: transaction fee
        """
        self.quote = init_cash_quote     # currency to buy
        self.base = init_cash_base       # primary currency
        self.fee = fee

        # list of executed transactions; element structure (buy/sell, rate, amount_quote,  amount_base)
        self.history = list()

    def buy(self, amount_quote, rate, date=0):
        """
        Buy base currency.
        :param amount_quote: volume of quote currency to be sold
        :param rate: exchange rate
        :param date: time stamp of the transaction
        """
        if self.quote - amount_quote >= 0:
            self.quote -= amount_quote
            self.base += amount_quote / rate * (1 - self.fee)

            self.history.append(('buy', date, rate,
                                 amount_quote * (1 - self.fee),
                                 amount_quote / rate * (1 - self.fee),
                                 self.balance_quote(rate)))
            return 0
        else:
            print('Not enough quote currency, cannot buy!')
            return 1

    def sell(self, amount_base, rate, date=0):
        """
        Sell base currency.
        :param amount_base: volume of base currency to be sold
        :param rate: exchange rate
        :param date: time stamp of the transaction
        """
        if self.base - amount_base >= 0:
            self.quote += amount_base * rate * (1 - self.fee)
            self.base -= amount_base

            self.history.append(('sell', date, rate,
                                 amount_base * rate * (1 - self.fee),
                                 amount_base * (1 - self.fee),
                                 self.balance_quote(rate)))
            return 0
        else:
            print('Not enough base currency, cannot sell!')
            return 1

    def balance_quote(self, current_rate):
        """
        Get current wallet balance in quote currency.
        :param current_rate: current exchange rate
        :return: current wallet balance
        """
        return self.quote + self.base * current_rate

    def balance(self):
        """
        Get wallet balance in both currencies.
        :return: balance in quote and base currency
        """
        return self.quote, self.base


class WalletIdca(Wallet):
    """
    Wallet with extended buy and sell methods and order books.
    """
    def __init__(self, init_cash_quote=1500, init_cash_base=0, fee=0.001, profit_rate=0.1, crypto_sell_frac=1.):
        """
        :param crypto_sell_frac: fraction of crypto associated with current operation which shall be sold
        """
        super().__init__(init_cash_quote, init_cash_base, fee)
        self.crypto_sell_frac = crypto_sell_frac
        self.profit_rate = profit_rate

        self.buy_order = None
        self.sell_order = None

        self.sell_orders = deque()

    def init_buy_order(self, amount_quote, rate):
        """
        Set the first buy order
        """
        self.buy_order = (amount_quote, rate)
        self.sell_order = None

    def buy_idca(self, next_buy_order_amount_quote):
        """
        Buy base currency and place new orders quoted on last buy order.
        """
        amount_quote, rate = self.buy_order

        if self.buy(amount_quote, rate) == 0:    # if there's enough quote...
            self.buy_order = (next_buy_order_amount_quote, rate * (1. - self.profit_rate))
            self.sell_orders.append((amount_quote / rate * self.crypto_sell_frac * (1 - self.fee - self.epsilon / rate),
                                     rate * (1. + self.profit_rate)))
            # self.sell_order = (amount_quote / rate * self.crypto_sell_frac * (1 - self.fee - self.epsilon / rate),
            #                    rate * (1. + self.profit_rate))

    def sell_idca(self, next_buy_order_amount_quote):
        """
        Sell base currency and place new orders quoted on last buy order.
        """
        amount_base, rate = self.sell_orders.pop()

        if self.sell(amount_base, rate) == 0:    # if there's enough base...
            self.buy_order = (next_buy_order_amount_quote, rate * (1 - self.profit_rate))
            # self.sell_order = None
