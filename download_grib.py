import os
import subprocess
from pathlib import Path

DATA_DIR = 'data/grib'


def download_dataset(dataset_url, debug=True):

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    output_path = DATA_DIR + '/' + dataset_url.split('/')[-1]
    if Path(output_path).is_file():
        if debug:
            print('\t[GRIB Downloader] Already downloaded %s' % dataset_url)
        return output_path

    if debug:
        print('\t[GRIB Downloader] Downloading %s to %s' % (dataset_url, output_path))

    remote_bytes = get_remote_bytes(dataset_url, debug)

    if debug:
        print('\t[GRIB Downloader] Downloading %d bytes' % remote_bytes)

    partial_name = output_path.split('.')[0] + '.grb2.partial'

    call = subprocess.run(['curl', '-o', partial_name, dataset_url])
    call.check_returncode()

    local_bytes = os.path.getsize(partial_name)

    if local_bytes != remote_bytes:
        raise Exception('Local bytes does not match remote bytes')

    os.rename(partial_name, output_path)

    if debug:
        print('\t[GRIB Downloader] Download complete: %s' % output_path)

    return output_path


def get_remote_bytes(dataset_url, _debug):
    call = subprocess.run(['curl', '-I', dataset_url], stdout=subprocess.PIPE)
    call.check_returncode()
    lines = call.stdout.decode('utf-8').split("\n")

    for line in lines:
        if not line.startswith('Content-Length:'):
            continue

        return int(line.split(': ')[-1])

    raise Exception('Could not find the number of remote bytes')
