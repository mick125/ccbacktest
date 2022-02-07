import pandas as pd


def add_ath(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds column with current ATH value to the historical data.
    :param df: input historical data
    :return: df with added column
    """
    df['ath'] = df['high'].cummax()
    return df


if __name__ == '__main__':
    ...