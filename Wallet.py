from collections import deque


class Wallet:
    """
    Wallet of two currencies.
    Base - currency I hold initially.
    Quote - currency I intend to buy.
    """

    def __init__(self, init_buy_rate, init_cash_base=1000, fee=0.001):
        self.fee = fee              # fee per trade
        self.base = init_cash_base  # primary currency
        self.quote = 0              # currency to buy
        self.sells = deque()        # stack of sell orders
        self.buys = deque()         # stack of buy orders
        self.buys.append(init_buy_rate)
        self.bought_base = deque()          # stack of rates at which quote currency was bought
        self.bought_vol_quote = deque()     # stack of bought volumes

    def buy(self, amount_base, rate, profit_rate):
        """
        Buy quote currency.
        :param amount_base: volume of base currency to be used
        :param rate: buy exchange rate
        :param profit_rate: target profit rate
        """
        self.base -= amount_base
        self.quote += amount_base / rate * (1 - self.fee)

        self.sells.append(rate * (1. + profit_rate))
        self.bought_base.append(self.buys.pop())
        self.buys.append(rate * (1. - profit_rate))
        self.bought_vol_quote.append(amount_base / rate * (1 - self.fee))

    def sell(self, amount_base, rate, profit_rate):
        """
        Sell quote currency.
        :param amount_base: UNUSED
        :param rate: sell exchange rate
        :param profit_rate: target profit rate
        """
        amount_quote = self.bought_vol_quote.pop()
        self.base += amount_quote * rate * (1 - self.fee)
        self.quote -= amount_quote

        self.sells.pop()
        self.bought_base.pop()
        self.buys.append(rate * (1. - profit_rate))     # tohle je mozna problem, nejak se mi hromadi buy ordery

    def get_balance_base(self, current_rate):
        """
        Get current wallet balance in base currency.
        :param current_rate: current exchange rate
        :return: current wallet balance
        """
        return self.base + self.quote * current_rate

    def get_balance(self):
        """
        Get wallet balance in both currencies.
        :return: balance in base and quote currency
        """
        return self.base, self.quote
