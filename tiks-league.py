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

NUMBER_FIELDS = {
    'age',  # 'height'
    'throwing', 'catching', 'defense',
    'handler-cutter', 'offense-defense',
    'availability'
}


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

    print("skill_score")
    for player in players:
        p = munge_player_dangood(player)
        p = munge_player(p)
        p['skill_score'] = int(player_skill(p))
        print("{captain}{name}:{gender}:{age}:{height[0]}'{height[1]}\":{skill_score}".format(**p))


def create_teams(N, players):
    """Create N balanced teams from the given players.

    - Equal number of players in teams (but also take availability into
      consideration). So, probably, equal availability of players, rather than
      equal number of players.

    - Balanced number of women players

    - Balance out the potential captains

    - Equal total skill level

    - Handling skill balance

    - Defense skill balance

    """

    players = [munge_player(p) for p in players]
    teams = {i: [] for i in range(1, N+1)}
    return teams


def munge_player(player):
    # player = normalize_player(player)
    player = {
        key: (float(value) if key in NUMBER_FIELDS else value)
        for key, value in player.items()
    }
    return player


def player_skill(player):
    skill = player['throwing'] + player['catching'] + player['defense']
    t = player['tournaments']
    experience = sum(3 - int(x/2) for x in range(2, t+1)) * 5
    # availability = player['availability'] / 5
    return (experience_multiplier(player) * skill + experience)


def experience_multiplier(player):
    t = player['tournaments']
    return math.sqrt(t) / math.sqrt(5)


def main():
    players = get_players('data/TIKS-league-masala-idli.csv')
    export_ultimate_hat(players)


if __name__ == '__main__':
    main()
