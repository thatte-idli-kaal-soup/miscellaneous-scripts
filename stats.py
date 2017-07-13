#!/usr/bin/env python3

import os
from os.path import abspath, dirname, join

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import flask
import pandas

HERE = dirname(abspath(__file__))
STATS_FILE = join(HERE, '..', 'data', 'stats.csv')
TOURNAMENT = 'BUO 2017'
TEAM = 'TIKS'
markers = ['circle', 'square', 'cross', 'diamond']


def get_match_points(tournament, opponent):
    points = data[(data['Tournament'] == tournament) &
                  (data['Opponent'] == opponent)]
    # FIXME: Disambiguate by date if there are multiple matches!
    assert len(points['Date/Time'].unique()) == 1, 'Multiple matches!'
    return points


def get_score_line(points):
    goals = points[points['Action'] == 'Goal']
    return (
        goals['Their Score - End of Point'],
        goals['Our Score - End of Point']
    )


def score_line_figure():
    opponents = data[data['Tournament'] == TOURNAMENT]['Opponent'].unique()
    traces = []
    for i, opponent in enumerate(sorted(opponents)):
        points = get_match_points(TOURNAMENT, opponent)
        theirs, ours = get_score_line(points)
        traces.append({
            'x': ours,
            'y': theirs,
            'name': opponent,
            'line': {'dash': 'dashdot', },
            'marker': {'symbol': markers[i % 4], 'size': 8},
            'mode': 'lines+markers',
        })
    traces.append({
        'x': list(range(16)),
        'y': list(range(16)),
        'name': 'Scores level',
        'type': 'lines',
        'mode': 'lines'
    })

    figure = {
        'data': traces,
        'layout': {
            'height': 800,
            'width': 800,
            'xaxis': {
                'title': 'Our score',
            },
            'yaxis': {
                'title': 'Opponent score',
            },
            'font': {
                'color': 'black'
            }
        }
    }

    return figure


data = pandas.read_csv(STATS_FILE)

graph_types = {
    'Score Line': score_line_figure,
}

server = flask.Flask('app')
server.secret_key = os.environ.get('secret_key', 'secret')

app = dash.Dash('app', server=server)
app.title = '{} Statistics'.format(TOURNAMENT)

app.scripts.config.serve_locally = False
dcc._js_dist[0]['external_url'] = (
    'https://cdn.plot.ly/plotly-basic-latest.min.js'
)

app.layout = html.Div([
    html.H1('{} - {}'.format(TOURNAMENT, TEAM)),
    dcc.Dropdown(
        id='graph-type-dropdown',
        options=[{'label': key, 'value': key} for key in graph_types.keys()],
        value='Score Line',
    ),

    dcc.Graph(id='my-graph')
], className="container")

app.css.append_css({
    'external_url': "https://codepen.io/chriddyp/pen/bWLwgP.css"
})


@app.callback(Output('my-graph', 'figure'),
              [Input('graph-type-dropdown', 'value'), ])
def update_graph(graph_type):
    return graph_types[graph_type]()


if __name__ == '__main__':
    app.run_server()
