#!/usr/bin/env python3
""" A script to process the data collected for the TIKS league.

- Export a CSV that can be used with other team generators out there
- Try to generate teams by ourselves

"""

import csv
import math

COLUMNS = [
    'timestamp',
    'name',
    'captain',
    'gender',
    'age',
    'height',
    'tournaments',
    'throwing',
    'catching',
    'defense',
    'handler-cutter',
    'offense-defense',
    'availability',
    'comments'
]

TOURNAMENTS_SCORE = [
    '0',
    '1-3',
    '4-9',
    '10-19',
    '20 or more',
]


def get_players(data_file):
    with open(data_file) as f:
        players = [
            dict(zip(COLUMNS, row))
            for row in csv.reader(f)
        ][1:]
    return players


def normalize_player(player):
    player = {
        key: (value.strip() if isinstance(value, str) else value)
        for key, value in player.items()
    }
    player['tournaments'] = TOURNAMENTS_SCORE.index(player['tournaments']) + 1
    return player


def munge_player_dangood(player):
    player = normalize_player(player)
    h = float(player['height'])
    player['height'] = (math.floor(h/12), int(h - 12*math.floor(h/12)))
    player['captain'] = ''  # if player['captain'] == 'No' else '*'
    return player


def export_ultimate_hat(players):
    """Exports data for dangoodspeed.com/ultimate/hat

    - Team size (make sure each team has as close to the same number of players
      as possible).

    - Captains (it makes sure that no two designated captains are placed on the
      same team).

    - Gender ratio (make sure each team has as close to the same number of
      ladies as possible).

    - Baggage (everyone who wants to be on the same team as a friend, can).

    - Skill (every team will be as close as possible in skill rank).

    - Height (make sure no team isn't 6" taller on average than any another
      team).

    - Age (when all else is said and done, try to even out the ages some).

    """

    print("tournaments:throwing:catching:defense")
    for player in players:
        p = munge_player_dangood(player)
        print("{captain}{name}:{gender}:{age}:{height[0]}'{height[1]}\":{tournaments}:{throwing}:{catching}:{defense}".format(**p))


def main():
    players = get_players('data/TIKS-league-masala-idli.csv')
    export_ultimate_hat(players)


if __name__ == '__main__':
    main()
