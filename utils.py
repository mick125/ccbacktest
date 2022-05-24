import os
import json
import pandas as pd

from pathlib import Path
from datetime import datetime


date_format_short = '%Y-%m-%d'
date_format_long = '%Y-%m-%d-%H-%M'


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

    return pd.read_parquet(data_folder / data_file).loc[start_date:end_date + pd.Timedelta(hours=23, minutes=59)]


def load_fng_data(fng_json_path: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Loads FnG data from json.
    :param fng_json_path: path to json with historical FnG data
    :param start_date: Start date
    :param end_date: End date
    :return:  FnG data
    """
    fng_json_path = Path(fng_json_path)
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    fng_df = json.load(open(fng_json_path))
    fng_df = pd.DataFrame(fng_df['data'])
    fng_df['value'] = fng_df['value'].astype(int)
    fng_df['timestamp'] = fng_df['timestamp'].astype(int)
    fng_df['timestamp'] = fng_df['timestamp'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d'))
    fng_df = fng_df.set_index(pd.to_datetime(fng_df['timestamp']))
    fng_df = fng_df.drop(['value_classification', 'time_until_update', 'timestamp'], axis=1)
    fng_df = fng_df.sort_index()

    # reduce the dataset temporarily
    return fng_df.loc[start_date:end_date]

