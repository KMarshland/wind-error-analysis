import os
from pathlib import Path
from download_utilities import download_file
from numpy_encoder import NumpyEncoder
import pandas as pd
import json

DATA_DIR = 'data/dataframes'

def directory_for(mission_number):
    return '%s/ssi-%s' % (DATA_DIR, str(mission_number))

def download_dataframe_for_mission(mission_number, debug=True):
    directory = directory_for(mission_number)

    if not os.path.exists(directory):
        os.makedirs(directory)

    data_file = directory + ('/ssi%s-processed.json' % mission_number)

    if Path(data_file).is_file():
        if debug:
            print('\t\t[Data] Data loading from cache')

        with open(data_file) as f:
            contents = f.read()

        return json.loads(contents)

    df = get_dataframe(mission_number, debug)
    result = process_dataframe(df, debug)

    with open(data_file, 'w') as f:
        f.write(json.dumps(result, cls=NumpyEncoder))

    return result


def process_dataframe(dataframe, debug):
    result = []

    if debug:
        print('\t\t[Dataset processing] Dataset goes from %s to %s' % (dataframe.index[0], dataframe.index[-1]))

    for i in range(len(dataframe.index)):
        # downsample further
        if i % 180 != 0:
            continue

        result.append({
            'transmit_time': float(dataframe.index[i].timestamp() * 1000.0),
            'time': float((dataframe.index[i] - dataframe.index[0]).total_seconds()),
            'latitude': float(dataframe['lat_gps'][i]),
            'longitude': float(dataframe['long_gps'][i]),
            'altitude_barometer': float(dataframe['altitude_barometer'][i]),
        })

    return result


def get_dataframe(mission_number, debug):
    if debug:
        print('\t[Dataframe Downloader] Downloading data for SSI-%d' % mission_number)

    dataset_url = 'http://128.12.62.54/vbdata/smoldf/ssi%s_smol.h5' % mission_number

    output_path = directory_for(mission_number) + '/' + dataset_url.split('/')[-1]
    if Path(output_path).is_file():
        if debug:
            print('\t[Dataframe Downloader] Already downloaded %s' % dataset_url)
    else:
        download_file(dataset_url, output_path, debug)

    df = pd.read_hdf(output_path)

    if debug:
        print('\t[Dataframe Downloader] Read %s.' % output_path)

    return df

