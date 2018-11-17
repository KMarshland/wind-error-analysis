import os
from pathlib import Path
import requests
import json

DATA_DIR = 'data/habmc'


def directory_for(mission_number):
    return '%s/ssi-%s' % (DATA_DIR, str(mission_number))


def download_data_for_mission(mission_number, debug=True):
    if debug:
        print('\t[HABMC Downloader] Downloading data for SSI-%d' % mission_number)

    directory = directory_for(mission_number)

    if not os.path.exists(directory):
        os.makedirs(directory)

    mission_id = get_id(mission_number, debug)

    return get_data(mission_number, mission_id, debug)


def get_id(mission_number, debug):
    id_file = directory_for(mission_number) + '/id.txt'
    if Path(id_file).is_file():
        if debug:
            print('\t\t[ID] Id loading from cache')

        with open(id_file) as f:
            contents = f.read()
        return contents

    data = requests.get('https://habmc.stanfordssi.org/missions.json').json()

    mission_id = None

    for mission in data['missions']:
        if mission['number'] == str(mission_number):
            mission_id = mission['id']

    if mission_id is None:
        raise Exception('Could not find mission')

    with open(id_file, 'w') as f:
        f.write(str(mission_id))

    if debug:
        print('\t\t[ID] ID found: %d' % mission_id)

    return mission_id


def get_data(mission_number, mission_id, debug):
    data_file = directory_for(mission_number) + '/habmc_data.json'
    if Path(data_file).is_file():
        if debug:
            print('\t\t[Data] Data loading from cache')

        with open(data_file) as f:
            contents = f.read()

        return json.loads(contents)

    page = 1
    limit = 500
    url = 'https://habmc.stanfordssi.org/missions/%s/transmissions/all.json' % str(mission_id)
    data = []

    while True:
        if debug:
            print('\t\t[Data] Downloading page %d (limit %d)' % (page, limit))

        response = requests.get(url, params={
            'page': page,
            'max': limit
        }, headers={
            'Authorization': 'Basic %s' % os.environ['HABMC_KEY']
        })

        if response.status_code != 200:
            print(url)
            raise Exception('Bad response: %d' % response.status_code)

        transmissions = response.json()
        data += transmissions

        if len(transmissions) == 0:
            break

        page += 1

    print('\t\t[Data] Download complete (%d transmissions)' % len(data))

    with open(data_file, 'w') as f:
        f.write(json.dumps(data))

    return data
