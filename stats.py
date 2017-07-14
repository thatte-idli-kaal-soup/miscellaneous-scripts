#!/usr/bin/env python3

import os
from os.path import abspath, dirname, exists, join

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
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


def o_d_lines_figure():
    columns = ['Player {}'.format(i) for i in range(7)]
    players = set(list(data[columns].fillna('V').values.flatten()))
    players.remove('V')
    players = sorted(players)
    goals = data[(data['Tournament'] == TOURNAMENT) &
                 (data['Action'] == 'Goal')]

    player_stats = {}
    for player in players:
        points = goals[(goals[columns] == player).any(axis=1)]
        o_points = points[points['Line'] == 'O']
        if len(points) < 5:
            continue
        player_stats[player] = (
            len(points), len(o_points), len(points) - len(o_points)
        )
    scatter_data = {
        'x': [o for _, o, _ in player_stats.values()],
        'y': [d for _, _, d in player_stats.values()],
        'text': ['{} - {}'.format(name, t)
                 for name, (t, o, d) in player_stats.items()],
        'mode': 'markers+text',
        'hoverinfo': 'text',
        'showlegend': False,
        'marker': {
            'size': [t for t, _, _ in player_stats.values()],
            'color': [t/5 for t, _, _ in player_stats.values()],
        }
    }

    traces = [go.Scatter(scatter_data)]
    traces.append({
        'x': list(range(60)),
        'y': list(range(60)),
        'name': 'O-D split',
        'mode': 'lines',
        'showlegend': False,
    })

    figure = {
        'data': traces,
        'layout': {
            'height': 800,
            'width': 900,
            'xaxis': {
                'title': 'Offense',
            },
            'yaxis': {
                'title': 'Defense',
            },
        }
    }

    return figure


if exists(STATS_FILE):
    data = pandas.read_csv(STATS_FILE)
else:
    from io import BytesIO
    from cryptography.fernet import Fernet
    key = os.environ.get('CRYPT_KEY', 'secret')
    with open('{}.crypt'.format(STATS_FILE), 'rb') as g:
        crypt_data = g.read()
    data = pandas.read_csv(BytesIO(Fernet(key).decrypt(crypt_data)))


graph_types = {
    'Score Line': score_line_figure,
    'O-D Lines': o_d_lines_figure,
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
