import os
from pathlib import Path
from download_utilities import download_file

DATA_DIR = 'data/grib'
cache = {}

def download_dataset(dataset_url, debug=True):
    # avoid calls to disk
    if dataset_url in cache:
       return cache[dataset_url]

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    output_path = DATA_DIR + '/' + dataset_url.split('/')[-1]
    if Path(output_path).is_file():
        if debug:
            print('\t[GRIB Downloader] Already downloaded %s' % dataset_url)
        cache[dataset_url] = output_path
        return output_path

    cache[dataset_url] = download_file(dataset_url, output_path, debug)

    return output_path

