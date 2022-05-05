import pandas as pd
from threading import Thread
from Historic_Crypto import HistoricalData

date_format = '%Y-%m-%d-%H-%M'


def retrieve_and_save_hist_data(pair: str, t_start: pd.Timestamp, t_end: pd.Timestamp) -> None:
    """
    Helper function for threading purposes. Can be also used for small downloads
    :param pair: Currency pair
    :param t_start: Get data from exchange from this date (format %Y-%m-%d-%H-%M)
    :param t_end: Get data from exchange to this date (format %Y-%m-%d-%H-%M)
    """
    date_format_file = '%Y-%m-%d'
    data_df = HistoricalData(pair, 60,
                             start_date=t_start.strftime(date_format),
                             end_date=t_end.strftime(date_format)
                             ).retrieve_data()
    pd.DataFrame(data_df). \
        to_parquet(
        f'data_raw/{pair}_{t_start.strftime(date_format_file)}_to_{t_end.strftime(date_format_file)}.parquet')


def retrieve_and_save_hist_data_parallel(pair: str, start_datetime: str, end_datetime: str, chunk_size='6M') -> None:
    """
    Retrieves historical crypto data from coin quote and saves them year-wise into parquet files. In parallel!
    :param pair: Currency pair
    :param start_datetime: Get data from exchange from this date (format %Y-%m-%d-%H-%M)
    :param end_datetime: Get data from exchange to this date (format %Y-%m-%d-%H-%M)
    :param chunk_size: Time length of a data chunk to be downloaded in one thread
    """
    start_datetime = pd.to_datetime(start_datetime, format=date_format)
    end_datetime = pd.to_datetime(end_datetime, format=date_format)

    start_times = list()
    # end_times = list()

    end_times = pd.date_range(start_datetime, end_datetime, freq=chunk_size).tolist()
    end_times = [time + pd.Timedelta(hours=23, minutes=59) for time in end_times]
    if end_datetime != end_times[-1]:
        end_times.append(end_datetime)

    start_times.append(pd.to_datetime(start_datetime, format=date_format))
    start_times.extend([time + pd.Timedelta(minutes=1) for time in end_times])
    start_times.pop()

    # download data from CoinBase
    # using threading
    threads = []
    for t_start, t_end in zip(start_times, end_times):
        process = Thread(target=retrieve_and_save_hist_data, args=(pair, t_start, t_end))
        process.start()
        threads.append(process)

    for process in threads:
        process.join()

    print('Historical data download and saving finished')


if __name__ == '__main__':
    # pair = 'BTC-USD'
    # pair = 'ETH-USD'
    # pair = 'LTC-USD'
    pair = 'ETH-BTC'
    start_datetime = '2016-06-01-00-00'
    end_datetime = '2022-04-30-23-59'
    chunk_length = '3M'
    # retrieve_and_save_hist_data(pair,
    #                             pd.to_datetime(start_datetime, format=date_format),
    #                             pd.to_datetime(end_datetime, format=date_format))

    retrieve_and_save_hist_data_parallel(pair, start_datetime, end_datetime, chunk_size=chunk_length)
