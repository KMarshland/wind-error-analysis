import pygrib
import bisect
import numpy as np
from download_grib import download_dataset

"""
Major credits to https://github.com/stanford-ssi/valbal-trajectory/blob/master/atmo/atmotools.py, where much of this
code was adapted from
"""

opened_cache = {}
cache = {}

latitudes = None
longitudes = None
levels = None

cache_hits = 0
call_count = 0

NAMES = ['u', 'v']

# closes all open grib files
def close_open_grib_files():
    global opened_cache

    for grb in opened_cache.values():
        grb.close()

    opened_cache = {}


def get_wind_velocity(time, latitude, longitude, altitude):
    # print('Bounds for', (latitude, longitude + 180, altitude_to_hpa(altitude)), get_aligned_positions(latitude, longitude, altitude))
    dataset_1 = download_dataset('https://nomads.ncdc.noaa.gov/data/gfs4/201811/20181101/gfs_4_20181101_0000_000.grb2')
    dataset_2 = dataset_1

    lat_lower, lng_lower, level_lower, lat_upper, lng_upper, level_upper = get_aligned_bounds(latitude, longitude, altitude)
    positions = [
        (lat_lower, lng_lower, level_lower), # 0: 000
        (lat_lower, lng_lower, level_upper), # 1: 001
        (lat_lower, lng_upper, level_lower), # 2: 010
        (lat_lower, lng_upper, level_upper), # 3: 011
        (lat_upper, lng_lower, level_lower), # 4: 100
        (lat_upper, lng_lower, level_upper), # 5: 101
        (lat_upper, lng_upper, level_lower), # 6: 110
        (lat_upper, lng_upper, level_upper), # 7: 111
    ]

    values1 = [get_uv_aligned(dataset_1, lat, lng, level) for lat, lng, level in positions]
    values2 = [get_uv_aligned(dataset_2, lat, lng, level) for lat, lng, level in positions]

    # interpolate within each dataset
    percent_lat = calc_percent(latitude, lat_lower, lat_upper)
    percent_lng = calc_percent(longitude, lng_lower, lng_upper)
    percent_lev = calc_percent(altitude_to_hpa(altitude), level_lower, level_upper)

    velocities = []
    for values in [values1, values2]:
        vel = (
            percent_lat * (
                percent_lng * (
                    percent_lev*values[0b000] + (1.0-percent_lev)*values[0b001]
                ) +
                (1.0 - percent_lng) * (
                    percent_lev*values[0b010] + (1.0-percent_lev)*values[0b011]
                )
            ) +
            (1.0 - percent_lat) * (
                percent_lng * (
                    percent_lev*values[0b100] + (1.0-percent_lev)*values[0b101]
                ) +
                (1.0 - percent_lng) * (
                    percent_lev*values[0b110] + (1.0-percent_lev)*values[0b111]
                )
            )
        )
        velocities.append(vel)

    # TODO: interpolate by time
    percent_time = 0

    return percent_time*velocities[0] + (1.0 - percent_time)*velocities[1]

PRELOAD_RANGE = 20

def get_uv_aligned(dataset, latitude, longitude, level):
    global call_count
    global cache_hits
    global cache

    call_count += 1

    values = []
    miss = False
    for name in NAMES:
        found = cache.get((dataset, latitude, longitude, level, name))
        if found is None:
            miss = True
            break
        else:
            values.append(found)

    if miss:
        print('\t[GRIB] Cache miss (hit rate: %f, calls: %d, hits: %d) for (%f, %f, %f)' % ((cache_hits/(call_count + 1)), call_count, cache_hits, latitude, longitude, level))
    else:
        cache_hits += 1
        return np.array(values)

    if dataset in opened_cache:
        grbs = opened_cache[dataset]
    else:
        grbs = pygrib.open(dataset)
        opened_cache[dataset] = grbs

    for name in NAMES:
        for i, grb in enumerate(grbs.select(shortName=name,typeOfLevel='isobaricInhPa',level=levels)):
            data = grb.data(latitude - PRELOAD_RANGE, latitude + PRELOAD_RANGE, longitude - PRELOAD_RANGE, longitude + PRELOAD_RANGE)

            data_values = data[0].flatten()
            data_latitudes = data[1].flatten()
            data_longitudes = data[2].flatten()

            for j in range(len(data_values)):
                data_val = data_values[j]
                data_lat = data_latitudes[j]
                data_lng = data_longitudes[j]

                cache[(dataset, data_lat, data_lng, levels[i], name)] = data_val

    result = np.array([ cache[(dataset, latitude, longitude, level, name)] for name in NAMES])

    return result

def get_aligned_bounds(latitude, longitude, altitude):
    find_grib_params()

    global latitudes
    global longitudes
    global levels

    lat_i = bisect.bisect_right(latitudes, latitude)
    lng_i = bisect.bisect_right(longitudes, longitude + 180)
    level_i = bisect.bisect_right(levels, altitude_to_hpa(altitude))

    lat_lower = latitudes[max(lat_i - 1, 0)]
    lat_upper = latitudes[min(level_i, len(latitudes) - 1)]

    lng_lower = longitudes[max(lng_i - 1, 0)]
    lng_upper = longitudes[min(level_i, len(longitudes) - 1)]

    level_lower = levels[max(level_i - 1, 0)]
    level_upper = levels[min(level_i, len(levels) - 1)]

    return lat_lower, lng_lower, level_lower, lat_upper, lng_upper, level_upper


def find_grib_params(shortname='u'):
    global latitudes
    global longitudes
    global levels

    if latitudes is not None and longitudes is not None and levels is not None:
        return

    source = download_dataset('https://nomads.ncdc.noaa.gov/data/gfs4/201811/20181113/gfs_4_20181113_0000_000.grb2')
    grb = pygrib.open(source)
    lats,lons = grb.select(shortName=shortname,typeOfLevel='isobaricInhPa',level=250)[0].latlons() # arbitrary data, doing this for latlons
    latitudes = lats[:,0]
    longitudes = lons[0,:]

    latitudes.sort()
    longitudes.sort()

    levels = []
    for message in grb:
        if message.shortName == shortname:
            if message.typeOfLevel == "isobaricInhPa":
                levels.append(message.level)
    levels.sort()

    grb.close()

# 1.0 -> all lower, 0.0 -> all upper
def calc_percent(value, lower, upper):
    if lower == upper:
        return 0

    # note that we invert these percentages cause I don't wanna rewrite the interpolation code
    return 1.0 - min(max((value - lower) / (upper - lower), 0.0), 1.0)

def altitude_to_hpa(altitude):
    return 1013.25 * ((1.0 - altitude/44330.0)**5.255)
