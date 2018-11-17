import numpy as np
import plotly.offline as py
import plotly.graph_objs as go


def plot_analysis(errors):
    x = np.array(errors)
    data = [go.Histogram(x=x)]

    py.plot(data, filename='plots/speed_error.html')
