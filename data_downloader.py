import pandas as pd
from threading import Thread
from Historic_Crypto import HistoricalData

date_format = '%Y-%m-%d-%H-%M'


def retrieve_and_save_hist_data(pair, t_start, t_end) -> None:
    """
    Helper function for threading purposes. Can be also used for small downloads
    """
    date_format_file = '%Y-%m-%d'
    data_df = HistoricalData(pair, 60,
                             start_date=t_start.strftime(date_format),
                             end_date=t_end.strftime(date_format)
                             ).retrieve_data()
    pd.DataFrame(data_df). \
        to_parquet(
        f'data_raw/{pair}_{t_start.strftime(date_format_file)}_to_{t_end.strftime(date_format_file)}.parquet')


def retrieve_and_save_hist_data_parallel(pair, start_datetime, end_datetime) -> None:
    """
    Retrieves historical crypto data from coin base and saves them year-wise into parquet files. In parallel!
    :param pair:
    :param start_datetime:
    :param end_datetime:
    """
    start_datetime = pd.to_datetime(start_datetime, format=date_format)
    end_datetime = pd.to_datetime(end_datetime, format=date_format)

    start_times = list()
    end_times = list()

    end_times = pd.date_range(start_datetime, end_datetime, freq='Y').tolist()
    end_times = [time + pd.Timedelta(hours=23, minutes=59) for time in end_times]
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
    pair = 'ETH-USD'
    start_datetime = '2015-09-10-00-00'
    # start_datetime = '2018-12-20-00-00'
    end_datetime = '2015-12-31-23-59'
    # end_datetime = '2018-12-31-23-59'
    retrieve_and_save_hist_data(pair,
                                pd.to_datetime(start_datetime, format=date_format),
                                pd.to_datetime(end_datetime, format=date_format))
