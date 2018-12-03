from download_grib import download_dataset
from bs4 import BeautifulSoup
import requests
import re
import os
import json
from pathlib import Path
from datetime import timezone, datetime
import bisect

index = {}
index_built = False

HOURS_TO_MS = 60*60*1000

def find_datasets(timestamp):
    build_index()

    selected_datasets = [value for value in index.values() if value['offset'] == 0 or value['offset'] == 3]
    # selected_datasets = [value for value in index.values() if value['month'] == 10 and value['day'] == 31 and value['hour'] == 6]
    selected_datasets.sort(key=lambda value: value['timestamp'] + HOURS_TO_MS*value['offset'])
    timestamps = [value['timestamp'] + HOURS_TO_MS*value['offset'] for value in selected_datasets]

    timestamp_i = bisect.bisect_right(timestamps, timestamp)
    lower = selected_datasets[max(timestamp_i - 1, 0)]
    upper = selected_datasets[min(timestamp_i, len(selected_datasets) - 1)]

    return (
               download_dataset(lower['url']),
               download_dataset(upper['url'])
           ), (
               lower['timestamp'] + HOURS_TO_MS*lower['offset'],
               upper['timestamp'] + HOURS_TO_MS*upper['offset']
           )

def build_index(debug=True):
    global index
    global index_built

    if index_built:
        return

    output_dir = 'data/index'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = output_dir + '/index.json'

    if Path(output_file).is_file():
        with open(output_file) as f:
            index = json.loads(f.read())
        index_built = True

        if debug:
            print('\t[DatasetManager] Loaded index from disk')
        return

    if debug:
        print('\t[DatasetManager] Building index')

    # TODO: stop hardcoding this
    build_index_for_month(2017, '04', debug)
    build_index_for_month(2017, 12, debug)
    build_index_for_month(2018, 10, debug)
    build_index_for_month(2018, 11, debug)

    with open(output_file, 'w') as f:
        f.write(json.dumps(index))

    index_built = True

def build_index_for_month(year, month, debug):
    output_dir = 'data/index/%s%s' % (year, month)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = output_dir + '/index.json'

    if Path(output_file).is_file():
        with open(output_file) as f:
            contents = json.loads(f.read())

        for key, value in contents.items():
            index[key] = value

        if debug:
            print('\t\t[DatasetManager] %s-%s already indexed' % (year, month))
        return contents

    if debug:
        print('\t\t[DatasetManager] Building index for %s-%s' % (year, month))

    url = 'https://nomads.ncdc.noaa.gov/data/gfs4/' + str(year) + str(month) + '/'

    response = requests.get(url)
    if response.status_code != 200:
        print(url)
        raise Exception('Bad response: %d' % response.status_code)

    soup = BeautifulSoup(response.text, 'html.parser')
    partial_index = {}
    for link in soup.find_all('a'):
        href = link.get('href')

        matches = re.search(r'^(\d{4})(\d{2})(\d{2})/$', href)
        if not matches:
            continue

        partial_index = {
            **partial_index,
            **build_index_for_day(matches.group(1), matches.group(2), matches.group(3), debug)
        }

    with open(output_file, 'w') as f:
        f.write(json.dumps(partial_index))

def build_index_for_day(year, month, day, debug):
    output_dir = 'data/index/%s%s/%s' % (year, month, day)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = output_dir + '/index.json'

    if Path(output_file).is_file():
        with open(output_file) as f:
            contents = json.loads(f.read())

        for key, value in contents.items():
            index[key] = value

        if debug:
            print('\t\t\t[DatasetManager] %s-%s-%s already indexed' % (year, month, day))
        return contents

    if debug:
        print('\t\t\t[DatasetManager] Building index for %s-%s-%s' % (year, month, day))

    url = 'https://nomads.ncdc.noaa.gov/data/gfs4/' + str(year) + str(month) + '/' + str(year) + str(month) + str(day) + '/'

    response = requests.get(url)
    if response.status_code != 200:
        print(url)
        raise Exception('Bad response: %d' % response.status_code)

    soup = BeautifulSoup(response.text, 'html.parser')
    partial_index = {}
    for link in soup.find_all('a'):
        href = link.get('href')
        if not href.endswith('.grb2'):
            continue

        hour = int(href.split('_')[-2])/100
        offset = href.split('_')[-1].split('.grb2')[0]

        dt = datetime(int(year), int(month), int(day), int(hour))
        timestamp = dt.replace(tzinfo=timezone.utc).timestamp()

        full_url = url + href
        partial_index[full_url] = index[full_url] = {
            'url': full_url,
            'year': int(year),
            'month': int(month),
            'day': int(day),
            'hour': int(hour),
            'offset': int(offset),
            'timestamp': timestamp*1000
        }

    with open(output_file, 'w') as f:
        f.write(json.dumps(partial_index))

    return partial_index

def get_sample_dataset():
    return download_dataset('https://nomads.ncdc.noaa.gov/data/gfs4/201811/20181113/gfs_4_20181113_0000_000.grb2')

if __name__ == "__main__":
    build_index()