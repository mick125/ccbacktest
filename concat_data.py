import os
from pathlib import Path
import pandas as pd


# functions
def concat_parquets(pair: str, data_folder=r'data_raw') -> pd.DataFrame:
    """
    Concatenate all parquet files for a given currency pair.
    :param pair: Currency pair name
    :param data_folder: Input folder
    :return: Data frame with concatenated data set
    """
    data_folder = Path(data_folder)
    files = os.listdir(data_folder)
    files = [f for f in files if (pair in f) and ('.parquet' in f)]
    print('Loading parquet files ...')
    frames = [pd.read_parquet(data_folder / file) for file in files]

    print('Concatenating data frames ... ', end='')
    df = pd.concat(frames)
    df.drop_duplicates(inplace=True)
    df.sort_index(inplace=True)
    print('Done')

    return df


def save_df_to_parquet(df: pd.DataFrame, pair: str, data_folder=r'data_crypto') -> None:
    """
    Saves data frame of a given pair to parquet.
    Output file name format: <pair>_<date_min>}__<date_max>.parquet
    :param df: Data frame with pair history
    :param pair: Currency pair name
    :param data_folder: Output folder
    """
    date_format = '%Y-%m-%d'
    date_min = df.index.min().strftime(date_format)
    date_max = df.index.max().strftime(date_format)

    data_folder = Path(data_folder)
    out_file_path = data_folder / f'{pair}_{date_min}_to_{date_max}.parquet'

    df.to_parquet(str(out_file_path))
    print(f'Concatenated data frame saved to:\n\t{out_file_path}')


# scripts
def concat_and_save_parquets(pair: str, input_folder=r'data_raw', output_folder=r'data_crypto') -> None:
    """
    Concatenates all parquet files for a given currency pair and saves to parquet file.
    :param output_folder: Input folder
    :param input_folder: Output folder
    :param pair: Currency pair name
    """
    df = concat_parquets(pair, input_folder)
    save_df_to_parquet(df, pair, output_folder)


if __name__ == '__main__':
    # concat_and_save_parquets('BTC-USD')
    concat_and_save_parquets('ETH-USD')
