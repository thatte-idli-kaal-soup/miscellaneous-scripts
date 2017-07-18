#!/usr/bin/env python3

from collections import OrderedDict
import os
from os.path import abspath, dirname, exists, join

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.figure_factory as ff
import flask
import pandas

HERE = dirname(abspath(__file__))
STATS_FILE = join(HERE, '..', 'data', 'stats.csv')
TOURNAMENT = 'BUO 2017'
TEAM = 'TIKS'
markers = ['circle', 'square', 'cross', 'diamond']

if exists(STATS_FILE):
    DATA = pandas.read_csv(STATS_FILE)
else:
    from io import BytesIO
    from cryptography.fernet import Fernet
    key = os.environ.get('CRYPT_KEY', 'secret')
    with open('{}.crypt'.format(STATS_FILE), 'rb') as g:
        crypt_data = g.read()
    DATA = pandas.read_csv(BytesIO(Fernet(key).decrypt(crypt_data)))
OPPONENTS = sorted(DATA[DATA['Tournament'] == TOURNAMENT]['Opponent'].unique())


def get_match_events(tournament, opponent):
    points = DATA[(DATA['Tournament'] == tournament) &
                  (DATA['Opponent'] == opponent)]
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
    traces = []
    for i, opponent in enumerate(OPPONENTS):
        events = get_match_events(TOURNAMENT, opponent)
        theirs, ours = get_score_line(events)
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
    players = set(list(DATA[columns].fillna('V').values.flatten()))
    players.remove('V')
    players = sorted(players)
    goals = DATA[(DATA['Tournament'] == TOURNAMENT) &
                 (DATA['Action'] == 'Goal')]

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


def time_between_points():
    table = []
    columns = ['Opponent', 'Median Time (secs)', 'Actual times (secs)']
    for opponent in OPPONENTS:
        events = get_match_events(TOURNAMENT, opponent)
        our_goals = events[(events['Action'] == 'Goal') &
                           (events['Event Type'] == 'Offense')]
        pull_times = []
        for row_index in our_goals.index:
            goal = DATA.loc[row_index]
            next_event = DATA.loc[row_index+1]
            # Ignore if match changed, or half-time
            if (
                    next_event['Opponent'] != opponent or
                    next_event['Event Type'] != 'Defense' or
                    not next_event['Action'].startswith('Pull')  # Pull(Ob)
            ):
                continue
            pull_time = (
                next_event['Elapsed Time (secs)'] - goal['Elapsed Time (secs)']
            )
            pull_times.append(pull_time)
        table.append([
            opponent,
            int(pandas.Series(pull_times).median()),
            ', '.join(map(str, pull_times))
        ])
    table = ff.create_table(pandas.DataFrame(table, columns=columns),)
    # FIXME: This is a plot.ly bug - headings are not visible, by default
    for annotation in table['layout']['annotations']:
        annotation['font']['color'] = '#000000'
    return table


def time_between_points_div():
    return html.P(
        "We look at median time (and not mean time) to compensate for not"
        " knowing how accurate the data is -- timeouts, data entry delay, etc."
        " can add outliers"
    )


graph_types = OrderedDict(
    [('Score Line', score_line_figure),
     ('O-D Lines', o_d_lines_figure),
     ('Time between points', time_between_points), ]
)

div_types = OrderedDict(
    [('Time between points', time_between_points_div)]
)


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
        options=[{'label': key, 'value': key}
                 for key in list(graph_types.keys())],
        value='Score Line',
    ),
    dcc.Graph(id='my-graph'),
    html.Div(id='my-div')
], className="container")

app.css.append_css({
    'external_url': "https://codepen.io/chriddyp/pen/bWLwgP.css"
})


@app.callback(Output('my-graph', 'figure'),
              [Input('graph-type-dropdown', 'value'), ])
def update_graph(graph_type):
    return graph_types[graph_type]() if graph_type in graph_types else ''


@app.callback(Output('my-div', 'children'),
              [Input('graph-type-dropdown', 'value'), ])
def update_div(div_type):
    return div_types[div_type]() if div_type in div_types else None


if __name__ == '__main__':
    app.run_server()
