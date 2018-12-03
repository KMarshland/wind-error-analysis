
This repository provides tools to analyze to accuracy of the GFS model based on measurements using ValBal, a long-endurance balloon platform. For findings, read [Characterizing GFS Error](docs/Characterizing%20GFS%20Error.pdf)

## Usage

### Setup

You will first need to install the python dependencies: beautifulsoup4, numpy, pandas, requests, plotly, and pygrib. You will also need curl.

You will also need to set the environment variable `HABMC_KEY` to the HABMC key downloaded from the preferences page on [habmc](https://habmc.stanfordssi.org). Note that you will have to be logged in and marked as a full member of SSI in order to do so. If you are unaffiliated with SSI, but still wish to run the code, please contact the owner of this repository.

### Running it

You can run the full analysis with `python main.py all`. You can also specify a single mission to analyze, either with HABMC data or with the full dataframe: `python main.py [mission number] ["dataframe" or "habmc"]`.

After running it, you can re-run the summary tools with `python analyze_result.py`.

You may also use the plotting tools: `python plot.py [plot type] [mission number] ["dataframe" or "habmc"]`, where plot type is speed, velocity, bearing, histogram, map, or speed_map.  

## Project Structure

- `analyze_result.py` After an analysis has been run, this file can analyze the analysis to generate numbers about things like average speed.
- `dataset_manager.py` This file is responsible for indexing which GFS datasets are available, exposing a function that can find the closest datasets to a given time.
- `download_dataframes.py` Provides utilities to get data from logged SD card data if any processed datasets for the given mission exist.
- `download_grib.py` Gives utilities to download the specified GRIB file (GRIB is the format in which GFS releases datasets).
- `download_habmc_data.py` Provides utilities to get the data from HABMC for a given mission.
- `download_utilities` A small helper function to make download files to disk easier.
- `grib_utils.py` Functions to get the wind data at a given point in space in time. Parses, caches, and interpolates to expose a clean interface.
- `main.py` Main entry point into the code, calculating the differences in velocity between measured and predicted.
- `mission_config.py` Configuration of which missions have full dataframes from the SD card and which do not.
- `numpy_encoder.py` Class to make serializing as json easier.
- `plot.py` Code to make plots of different parts of the analysis.

## License
MIT