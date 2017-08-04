#!/usr/bin/env python3
""" A script to process the data collected for the TIKS league.

- Export a CSV that can be used with other team generators out there
- Try to generate teams by ourselves

"""

import csv
import json
import math
from pprint import pprint

from baggage import BAGGAGE


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


class Player(dict):
    def __repr__(self):
        return self['name']


def get_players(data_file):
    with open(data_file) as f:
        players = [
            Player(zip(COLUMNS, row))
            for row in csv.reader(f)
        ][1:]
    return players


def normalize_player(player):
    player = {
        key: (value.strip() if isinstance(value, str) else value)
        for key, value in player.items()
    }
    player['tournaments'] = TOURNAMENTS_SCORE.index(player['tournaments']) + 1
    return Player(player)


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
    """Create N balanced teams from the given players. """

    def sort_key(x):
        return (x['availability'], x['tournaments'])
    players = [munge_player(p) for p in players]
    men = filter(lambda x: x['gender'] == 'M', players)
    women = filter(lambda x: x['gender'] == 'F', players)
    sorted_men = sorted(men, key=sort_key, reverse=True)
    sorted_women = sorted(women, key=sort_key, reverse=True)
    teams = [[] for _ in range(N)]
    for i, player in enumerate(sorted_men):
        teams[i % 4].append(player)
    for i, player in enumerate(sorted_women, start=i+1):
        teams[i % 4].append(player)

    return teams




def evaluate_team(team):
    """Evaluate the scores for a team, based on the following criteria.

    - Equal number of players in teams (but also take availability into
      consideration). So, probably, equal availability of players, rather than
      equal number of players.

    - Balanced number of women players

    - Balance out the potential captains

    - Equal total skill level

    - Handling skill balance

    - Defense skill balance

    - Player baggage

    - Age?

    - Height?

    """

    n = len(team)
    availability = sum(p['availability'] for p in team) / 5
    women = sum(1 for p in team if p['gender'] == 'F')
    captains = sum(1 for p in team if p['captain'] == 'Yes')
    skill = sum(p['skill_score'] for p in team) / n
    handling = sum(
        p['throwing'] * (6 - p['handler-cutter'])/2 if p['handler-cutter'] <= 3
        else p['throwing']
        for p in team
    ) / n
    defense = sum(
        p['defense'] * p['offense-defense']/2 if p['offense-defense'] >= 3
        else p['defense']
        for p in team
    ) / n
    # How many players don't have their baggage player in the team?
    baggage = sum(
        1 for player, other in BAGGAGE
        if
        (player_in_team(player, team) and not player_in_team(other, team)) or
        (player_in_team(other, team) and not player_in_team(player, team))
    )

    return (
        n, availability, women, captains, skill, handling, defense, baggage
    )


def player_in_team(player_name, team):
    return player_name in {x['name'] for x in team}


def create_team_from_names(players, names):
    return [p for p in players if p['name'] in names]


def munge_player(player):
    player = normalize_player(player)
    player = {
        key: (float(value) if key in NUMBER_FIELDS else value)
        for key, value in player.items()
    }
    player['skill_score'] = player_skill(player)
    return Player(player)


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
    teams = create_teams(4, players)
    KEYS = ['age', 'comments', 'height', 'handler-cutter', 'offense-defense',
            'timestamp', 'defense', 'catching', 'throwing', 'skill_score',
            'tournaments', ]
    for team in teams:
        for player in team:
            for key in KEYS:
                player.pop(key)

    print(json.dumps(teams))

if __name__ == '__main__':
    main()
