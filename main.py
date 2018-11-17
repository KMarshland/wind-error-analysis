from download_habmc_data import download_data_for_mission
from download_grib import download_dataset


def main():
    mission = 77
    download_data_for_mission(mission)
    download_dataset('https://nomads.ncdc.noaa.gov/data/gfs4/201811/20181113/gfs_4_20181113_0000_000.grb2')


if __name__ == "__main__":
    main()
