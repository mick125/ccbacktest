import os
import pandas as pd

from pathlib import Path


def load_crypto_data(pair: str, start_date: str, end_date: str, data_folder='data_crypto') -> pd.DataFrame:
    """
    Loads historical crypto data from parquet file into data frame in given time range.
    :param pair: Currency pair
    :param start_date: Start date
    :param end_date: End date
    :param data_folder: Folder where to look for historical data.
    :return:
    """
    data_folder = Path(data_folder)
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # get file name
    try:
        data_file = [f for f in os.listdir(data_folder) if pair in f][0]
    except IndexError:
        raise IndexError(f'No data file found for pair {pair}!')  # tohle nevim, jestli se tak spravne dela

    return pd.read_parquet(data_folder / data_file).loc[start_date:end_date]
