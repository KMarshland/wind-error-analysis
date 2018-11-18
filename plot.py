import numpy as np
import json
import os
import plotly.offline as py
import plotly.graph_objs as go


def plot_analysis(info):
    speed_errors = np.array(list(map(lambda point: point['speed_error'], info)))
    max_error = speed_errors.max()

    mapbox = go.Scattermapbox(
        lat=list(map(lambda point: point['latitude'], info)),
        lon=list(map(lambda point: point['longitude'], info)),
        mode='markers',
        marker=dict(
            size=list(map(lambda point: point['speed_error']/2.0 + 1.0, info)),
            color=list(map(lambda point: point['speed_error']/max_error, info)),
            colorscale='Jet'
        ),
        text=['Data'],
    )

    histogram = go.Histogram(x=speed_errors)

    data = [
        mapbox,
    ]

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
    py.plot([histogram], filename='plots/speed_error_histogram.html')

# just test the plotting
if __name__ == "__main__":
    with open('data/analyzed/ssi-77.json') as f:
        contents = json.loads(f.read())
    plot_analysis(contents)
