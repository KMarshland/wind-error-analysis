import numpy as np
import json
import os
import plotly.offline as py
import plotly.graph_objs as go
import sys

def plot_map(data):
    layout = go.Layout(
        autosize=True,
        hovermode='closest',
        mapbox=dict(
            accesstoken=os.environ['MAPBOX_TOKEN'],
            bearing=0,
            center=dict(
                lat=45,
                lon=-73
            ),
            pitch=0,
            zoom=3
        ),
    )

    fig = dict(data=data, layout=layout)

    py.plot(fig, filename='plots/speed_error.html')

def plot_speed_error_map(info):
    max_error = np.array(list(map(lambda point: point['speed_error'], info))).max()

    data = [
        go.Scattermapbox(
            lat=list(map(lambda point: point['latitude'], info)),
            lon=list(map(lambda point: point['longitude'], info)),
            mode='markers',
            marker=dict(
                size=list(map(lambda point: point['speed_error']/6.0 + 3.0, info)),
                color=list(map(lambda point: 1.0 - (1.0 - point['speed_error']/max_error)**2, info)),
                colorscale='Reds'
            ),
            text=list(map(lambda point: 'Error: %.2fm/s (%.2f m/s measured vs %.2f m/s predicted)' % (point['speed_error'], point['data_speed'], point['model_speed']), info)),
        ),
    ]

    plot_map(data)

def plot_speed_map(info):
    max_data_speed = np.array(list(map(lambda point: point['data_speed'], info))).max()
    max_model_speed = np.array(list(map(lambda point: point['model_speed'], info))).max()

    data = [
        go.Scattermapbox(
            lat=list(map(lambda point: point['latitude'], info)),
            lon=list(map(lambda point: point['longitude'], info)),
            mode='markers',
            marker=dict(
                size=list(map(lambda point: point['data_speed']/6.0 + 3.0, info)),
                color=list(map(lambda point: point['data_speed']/max_data_speed, info)),
                colorscale='Reds'
            ),
            text=list(map(lambda point: 'Error: %.2fm/s (%.2f m/s measured vs %.2f m/s predicted)' % (point['speed_error'], point['data_speed'], point['model_speed']), info)),
        ),
        go.Scattermapbox(
            lat=list(map(lambda point: point['latitude'], info)),
            lon=list(map(lambda point: point['longitude'], info)),
            mode='markers',
            marker=dict(
                size=list(map(lambda point: point['model_speed']/6.0 + 3.0, info)),
                color=list(map(lambda point: point['model_speed']/max_model_speed, info)),
                colorscale='Reds'
            ),
            text=list(map(lambda point: 'Error: %.2fm/s (%.2f m/s measured vs %.2f m/s predicted)' % (point['speed_error'], point['data_speed'], point['model_speed']), info)),
        )
    ]

    plot_map(data)

def plot_histogram(info):
    histogram = go.Histogram(x=list(map(lambda point: point['speed_error'], info)))

    py.plot([histogram], filename='plots/speed_error_histogram.html')


def plot_speed_comparison(info):
    py.plot([
        go.Scatter(
            y = np.array(list(map(lambda point: point['data_speed'], info))),
            name = 'data speed'
        ),
        go.Scatter(
            y = np.array(list(map(lambda point: point['model_speed'], info))),
            name = 'model speed'
        )
    ], filename='plots/speed_error_chart.html')

def plot_bearing_comparison(info):
    py.plot([
        go.Scatter(
            y = np.array(list(map(lambda point: point['data_bearing'], info))),
            name = 'data bearing'
        ),
        go.Scatter(
            y = np.array(list(map(lambda point: point['model_bearing'], info))),
            name = 'model bearing'
        )
    ], filename='plots/speed_error_chart.html')

def plot_velocity_comparison(info):
    py.plot([
        go.Scatter(
            y = np.array(list(map(lambda point: point['data_speed'], info))),
            name = 'data speed'
        ),
        go.Scatter(
            y = np.array(list(map(lambda point: point['model_speed'], info))),
            name = 'model speed'
        ),
        go.Scatter(
            y = np.array(list(map(lambda point: point['data_bearing'], info))),
            name = 'data bearing'
        ),
        go.Scatter(
            y = np.array(list(map(lambda point: point['model_bearing'], info))),
            name = 'model bearing'
        )
    ], filename='plots/speed_error_chart.html')

def plot_analysis(info, which=None):
    if which is None:
        which = 'speed'

    if which == 'speed':
        plot_speed_comparison(info)
    elif which == 'velocity':
        plot_velocity_comparison(info)
    elif which == 'bearing':
        plot_bearing_comparison(info)
    elif which == 'histogram':
        plot_histogram(info)
    elif which == 'map':
        plot_speed_error_map(info)
    elif which == 'speed_map':
        plot_speed_map(info)
    else:
        print('No such plot available: %s' % which)

# just test the plotting
if __name__ == "__main__":
    with open('data/analyzed/ssi-77.json') as f:
        contents = json.loads(f.read())
    plot_analysis(contents, sys.argv[1] if len(sys.argv) >= 2 else None)
