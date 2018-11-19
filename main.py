import math
import numpy as np
import json
import os
import time
from download_habmc_data import download_data_for_mission
from grib_utils import get_wind_velocity, close_open_grib_files
from plot import plot_analysis
from numpy_encoder import NumpyEncoder

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
    
    distance = angle * earth_radius

    y = math.sin(lon_to-lon_from) * math.cos(lat_to)
    x = math.cos(lat_from)*math.sin(lat_to) - math.sin(lat_from)*math.cos(lat_to)*math.cos(lon_to-lon_from)

    bearing = math.atan2(y, x)

    return np.array([ distance * math.cos(bearing), distance * math.sin(bearing) ]), distance, math.degrees(bearing)


def compare_against_habmc(mission):
    transmissions = download_data_for_mission(mission)

    print('\t[Analysis] Beginning analysis')

    result = []
    analysis_start_time = time.time()
    last_ellapsed = 0

    def generate_empty(transmission):
        return {
            'latitude': transmission['latitude'],
            'longitude': transmission['longitude'],
            'altitude': transmission['altitude_barometer'],
            'timestamp': transmission['transmit_time'],
            'data_speed': None,
            'speed_upper': None,
            'speed_lower': None,
            'model_speed': None,
            'data_bearing': None,
            'model_bearing': None,
            'data_velocity': None,
            'model_velocity': None,
            'speed_error': None
        }

    for i in range(1, len(transmissions)):
        prev = transmissions[i - 1]
        curr = transmissions[i]

        # over long comm gaps it's no longer useful
        delta_ms = (curr['time'] - prev['time']) * 1000  # convert to ms so that it's interoperable with transmit_time
        if delta_ms > MAX_COMM_GAP:
            result.append(generate_empty(curr))
            continue

        # when gps is off it's not useful
        if curr['latitude'] == prev['latitude'] and curr['longitude'] == prev['longitude']:
            result.append(generate_empty(curr))
            continue

        # also filter it out if the gps just turned back on
        if i >= 2:
            two_ago = transmissions[i - 2]
            if two_ago['latitude'] == prev['latitude'] and two_ago['longitude'] == prev['longitude']:
                result.append(generate_empty(curr))
                continue

        model_velocity = get_wind_velocity(curr['transmit_time'], curr['latitude'], curr['longitude'], curr['altitude_barometer'])
        model_speed = float(np.linalg.norm(model_velocity))
        model_bearing = math.degrees(math.atan2(model_velocity[0], model_velocity[1]))

        distance, displacement, data_bearing = distance_between(prev['latitude'], prev['longitude'], curr['latitude'], curr['longitude'])
        data_velocity = distance / (delta_ms/1000.0)
        data_speed = float(np.linalg.norm(data_velocity))
        speed_upper = displacement / (delta_ms/1000.0 - 60.0)
        speed_lower = displacement / (delta_ms/1000.0 + 60.0)

        # simple filter to throw out trash
        # if data_speed > MAX_SPEED:
        #     result.append(generate_empty(curr))
        #     continue

        result.append({
            'latitude': curr['latitude'],
            'longitude': curr['longitude'],
            'altitude': curr['altitude_barometer'],
            'timestamp': curr['transmit_time'],
            'data_speed': data_speed,
            'speed_upper': speed_upper,
            'speed_lower': speed_lower,
            'model_speed': model_speed,
            'data_bearing': data_bearing,
            'model_bearing': model_bearing,
            'data_velocity': data_velocity,
            'model_velocity': model_velocity,
            'speed_error': abs(data_speed - model_speed)
        })

        ellapsed = time.time() - analysis_start_time
        if ellapsed - last_ellapsed > 1:
            print('\t[Analysis] %.1f%% (%d/%d) complete, %.2f per second avg (%.2fs ellapsed)' %
                  (100.0*(i / float(len(transmissions))), i, len(transmissions), i / ellapsed, ellapsed))
            last_ellapsed = ellapsed

    ellapsed = time.time() - analysis_start_time
    print('Average error: %.2fm/s (analysis took %.2f seconds)' %
          (np.mean([d['speed_error'] for d in result if d['speed_error'] is not None]), ellapsed))

    output_dir = 'data/analyzed'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_dir + '/ssi-' + str(mission) + '.json', 'w') as f:
        f.write(json.dumps(result, cls=NumpyEncoder))

    return result

def main():
    mission = 77
    result = compare_against_habmc(mission)
    plot_analysis(result)

    close_open_grib_files()

if __name__ == "__main__":
    main()
