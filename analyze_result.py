import numpy as np
import math
import json
from pathlib import Path
from mission_config import ANALYZED_MISSIONS
from numpy_encoder import NumpyEncoder

# latitudes over which it is sea, by mission
SEA_LONGITUDES = {
    71: [-70.8, -1.4],
    77: [-77.39, -7.7]
}

def analyze_result(result, mission, ellapsed=None, debug=True):
    def average(key, values=result):
        filtered = [d[key] for d in values if d[key] is not None]
        if len(filtered) == 0:
            return float('NaN')

        return float(np.mean(filtered))

    def rms(values):
        if len(values) == 0:
            return float('NaN')

        return float(math.sqrt(np.mean([error**2 for error in values])))

    sea_start_longitude = -65.0
    sea_end_longitude = -8.0
    if mission in SEA_LONGITUDES:
        longitudes = SEA_LONGITUDES[mission]
        if isinstance(longitudes, list):
            sea_start_longitude = longitudes[0]
            sea_end_longitude = longitudes[1]
        else:
            sea_start_longitude = longitudes

    over_land = [d for d in result if d['longitude'] < sea_start_longitude or d['longitude'] > sea_end_longitude]
    over_sea = [d for d in result if sea_start_longitude <= d['longitude'] <= sea_end_longitude]

    analysis = {
        'ellapsed': ellapsed,

        'speed': {
            'net_speed_error': abs(average('data_speed') - average('model_speed')),
            'average_data_speed': average('data_speed'),
            'average_model_speed': average('model_speed'),
            'average_speed_error': average('speed_error'),
            'rms_speed_error': rms([d['speed_error'] for d in result if d['speed_error'] is not None]),
            'over_land': {
                'net_speed_error_over_land': abs(average('data_speed', values=over_land) - average('model_speed', values=over_land)),
                'average_data_speed_over_land': average('data_speed', values=over_land),
                'average_model_speed_over_land': average('model_speed', values=over_land),
                'rms_speed_error_over_land': rms([d['speed_error'] for d in over_land if d['speed_error'] is not None]),
            },
            'over_sea': {
                'net_speed_error_over_sea': abs(average('data_speed', values=over_sea) - average('model_speed', values=over_sea)),
                'average_data_speed_over_sea': average('data_speed', values=over_sea),
                'average_model_speed_over_sea': average('model_speed', values=over_sea),
                'rms_speed_error_over_sea': rms([d['speed_error'] for d in over_sea if d['speed_error'] is not None]),
            }
        },

        'bearing': {
            'net_bearing_error': abs(average('data_bearing') - average('model_bearing')),
            'average_data_bearing': average('data_bearing'),
            'average_model_bearing': average('model_bearing'),
            'average_bearing_error': float(np.mean([abs(d['data_bearing'] - d['model_bearing']) for d in result if d['data_bearing'] is not None])),

            'rms_bearing_error': rms([d['data_bearing'] - d['model_bearing'] for d in result if d['data_bearing'] is not None]),
            'over_land': {
                'net_bearing_error_over_land': abs(average('data_bearing', values=over_land) - average('model_bearing', values=over_land)),
                'average_data_bearing_over_land': average('data_bearing', values=over_land),
                'average_model_bearing_over_land': average('model_bearing', values=over_land),
                'rms_bearing_error_over_land': rms([d['data_bearing'] - d['model_bearing'] for d in over_land if d['speed_error'] is not None]),
            },
            'over_sea': {
                'net_bearing_error_over_sea': abs(average('data_bearing', values=over_sea) - average('model_bearing', values=over_sea)),
                'average_data_bearing_over_sea': average('data_bearing', values=over_sea),
                'average_model_bearing_over_sea': average('model_bearing', values=over_sea),
                'rms_bearing_error_over_sea': rms([d['data_bearing'] - d['model_bearing'] for d in over_sea if d['speed_error'] is not None]),
            }
        }
    }

    if debug:
        print('\t[Analysis]')
        for line in json.dumps(analysis, cls=NumpyEncoder, indent=4).split('\n'):
            print('\t[Analysis]\t %s' % line)
        print('\t[Analysis]')

    return analysis

def analyze_result_from_disk(mission, habmc):
    output_dir = 'data/analyzed'
    result_file = output_dir + '/ssi-' + str(mission) + '-%s.json' % ('habmc' if habmc else 'dataframe')
    if not Path(result_file).is_file():
        print('\t[Analysis] Cannot analyze %s as it does not exist' % result_file.split('/')[-1])
        return

    print('\t[Analysis] Analyzing %s' % result_file.split('/')[-1])

    with open(result_file, 'r') as f:
        analysis = analyze_result(json.loads(f.read()), mission)

    with open(output_dir + '/ssi-' + str(mission) + '-%s-analysis.json' % ('habmc' if habmc else 'dataframe'), 'w') as f:
        f.write(json.dumps(analysis, cls=NumpyEncoder, indent=4))


def analyze_all():
    for mission, has_dataframe in ANALYZED_MISSIONS.items():
        analyze_result_from_disk(mission, habmc=True)
        if has_dataframe:
            analyze_result_from_disk(mission, habmc=False)

if __name__ == "__main__":
    analyze_all()