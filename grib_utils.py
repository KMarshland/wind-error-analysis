import pygrib
import bisect
import numpy as np
from download_grib import download_dataset

"""
Major credits to https://github.com/stanford-ssi/valbal-trajectory/blob/master/atmo/atmotools.py, where much of this
code was adapted from
"""

cache = {}
latitudes = None
longitudes = None
levels = None


def get_uv(time, latitude, longitude, altitude):
    # print('Bounds for', (latitude, longitude + 180, altitude_to_hpa(altitude)), get_aligned_positions(latitude, longitude, altitude))
    positions = get_aligned_positions(latitude, longitude, altitude)
    return 0, 0


def get_aligned_positions(latitude, longitude, altitude):
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

    return [
        (lat_lower, lng_lower, level_lower),
        (lat_lower, lng_upper, level_lower),
        (lat_upper, lng_lower, level_lower),
        (lat_upper, lng_upper, level_lower),
        (lat_lower, lng_lower, level_upper),
        (lat_lower, lng_upper, level_upper),
        (lat_upper, lng_lower, level_upper),
        (lat_upper, lng_upper, level_upper),
    ]


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
    print(levels)

def altitude_to_hpa(altitude):
    return 1013.25 * ((1.0 - altitude/44330.0)**5.255)
