import math
from download_habmc_data import download_data_for_mission
from download_grib import download_dataset
from grib_utils import get_uv
from plot import plot_analysis

MAX_COMM_GAP = 10*60*1000  # max time between transmissions
MAX_SPEED = 100  # max speed, in m/s before it throws out the data

def distance_between(lat1, lng1, lat2, lng2):
    """
    Distance in meters between two sets of coordinates
    """
    earth_radius = 6371000
    deg_to_rad = math.pi / 180

    lat_from = lat1 * deg_to_rad
    lat_to = lat2 * deg_to_rad
    lon_from = lng1 * deg_to_rad
    lon_to = lng2 * deg_to_rad

    lat_delta = lat_to - lat_from
    lon_delta = lon_to - lon_from

    partial_angle = math.sin(lat_delta/2) * math.sin(lat_delta/2) + math.sin(lon_delta/2) * math.sin(lon_delta/2) * math.cos(lat_from) * math.cos(lat_to)
    angle = 2 * math.atan2(math.sqrt(partial_angle), math.sqrt(1-partial_angle))
    
    return angle * earth_radius

def compare_against_habmc(mission):
    transmissions = download_data_for_mission(mission)

    result = []
    for i in range(1, len(transmissions)):
        prev = transmissions[i - 1]
        curr = transmissions[i]

        # over long comm gaps it's no longer useful
        delta_ms = curr['transmit_time'] - prev['transmit_time']
        if delta_ms > MAX_COMM_GAP:
            continue

        # when gps is off it's not useful
        if curr['latitude'] == prev['latitude'] and curr['longitude'] == prev['longitude']:
            continue

        # also filter it out if the gps just turned back on
        if i >= 2:
            two_ago = transmissions[i - 2]
            if two_ago['latitude'] == prev['latitude'] and two_ago['longitude'] == prev['longitude']:
                continue

        model_u, model_v = get_uv(curr['transmit_time'], curr['latitude'], curr['longitude'], curr['altitude_barometer'])
        model_speed = math.sqrt(model_u**2 + model_v**2)

        distance = distance_between(prev['latitude'], prev['longitude'], curr['latitude'], curr['longitude'])
        data_speed = distance / (delta_ms/1000)

        # simple filter to throw out trash
        if data_speed > MAX_SPEED:
            continue

        result.append(abs(data_speed - model_speed))

    plot_analysis(result)

def main():
    mission = 77
    compare_against_habmc(mission)

    download_dataset('https://nomads.ncdc.noaa.gov/data/gfs4/201811/20181113/gfs_4_20181113_0000_000.grb2')


if __name__ == "__main__":
    main()
