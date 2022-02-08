import pandas as pd


def add_top(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds column with current top value to the historical data.
    :param df: input historical data
    :return: df with added column
    """
    df['top'] = df['high'].cummax()
    return df


def add_prev_top(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds column with top value from previous row to the historical data.
    :param df: input historical data
    :return: df with added column
    """
    df['prev_top'] = df['top'].shift(1)
    return df


def add_new_top(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds column with bool value. True - new top was reached now. False - otherwise.
    :param df: input historical data
    :return: df with added column
    """
    df['new_top'] = df['top'].values > df['prev_top'].values
    return df


if __name__ == '__main__':
    ...