#!/usr/bin/env python

import os
from os.path import abspath, dirname, join

import pandas as pd

from women import WOMEN
MIN_RATINGS = 5  # Minimum number of ratings required to show aggregate
COLUMNS = [
    'Speed',
    'Endurance',
    'Fitness',
    'Skill',
    'Throwing-Decision',
    'Mobility',
    'Cuts',
    'Receiving-Decision',
    'Zone',
    'Man-mark',
    'Sideline Support',
    'Team Player',
    'Spirit',
    'Attitude'
]
WEIGHTS = {
    # Physical Ability
    'Speed': 4,
    'Endurance': 4,
    'Fitness': 4,
    # Throwing
    'Skill': 6,
    'Throwing-Decision': 6,
    # Receiving
    'Mobility': 2,
    'Cuts': 5,
    'Receiving-Decision': 5,
    # Defense
    'Zone': 6,
    'Man-mark': 6,
    # Off-field
    'Sideline Support': 3,
    'Team Player': 3,
    'Spirit': 4,
    'Attitude': 2,
}
TOTAL = sum(WEIGHTS.values())
HERE = dirname(abspath(__file__))


def iter_data(root_dir):
    """Iterate over all the available ratings files."""
    for root, dirs, files in os.walk(root_dir):
        for name in files:
            if not name.endswith('.csv') and not name.endswith('.xlsx'):
                continue
            yield join(root, name)


def read_ratings(csv_path):
    """Read peer ratings from a single CSV/xlsx file."""
    reader = pd.read_excel if csv_path.endswith('.xlsx') else pd.read_csv
    data = reader(csv_path, skiprows=9, header=None, index_col=0, names=COLUMNS)
    data.index = [name.strip() for name in data.index]
    data.index.name = 'Players'
    data = normalize_ratings(data)
    return data


def normalize_ratings(data):
    """Normalize the ratings

    Scores for men & women are normalized separately - the problems with men &
    women being rated on same scale by some people and on different scales by
    others, would be fixed this way. Some women on the team felt women should
    have a separate scale at least for the Physical Ability parameters - Speed,
    Endurance, Fitness.

    Also, We normalize each column separately, instead of normalizing the
    aggregated scores.

    """

    MEN = [name for name in data.index if name not in WOMEN]

    data_men = data.loc[MEN]
    data_women = data.loc[WOMEN]

    def normalize_column(x):
        "Scale to the column to the range 1 - 5."
        return (x - x.min()) / (x.max() - x.min()) * 4 + 1

    n_data_men = data_men.apply(normalize_column)
    n_data_women = data_women.apply(normalize_column)

    return n_data_men.append(n_data_women)


def aggregate_ratings():
    """Calculate the aggregate ratings for players.

    Average the ratings every player obtained for all the parameters.

    The aggregates are computed/shown only for players with at least
    MIN_RATINGS number of ratings

    """
    root = join(HERE, '../data/peer-review/')
    DATA = {csv: read_ratings(csv) for csv in iter_data(root)}

    sample = list(DATA.values())[0]

    total = sample.copy()
    total[:] = 0

    counts = sample.copy()
    counts[:] = 0

    for csv, d in DATA.items():
        total += d.fillna(0)
        counts += d.notna()

    aggregate = total/counts
    return aggregate[counts >= MIN_RATINGS]


def compute_cumulative(ratings, weighted=True):
    """Computes the cumulative rating based on weights for each column."""

    if not weighted:
        scores = ratings.mean(axis=1)

    else:
        def weighted_column(x):
            return x * WEIGHTS[x.name] / TOTAL

        scores = ratings.apply(weighted_column).sum(axis=1)

    return scores


def ranks(scores):
    MEN = [name for name in ratings.index if name not in WOMEN]
    print(scores.loc[MEN].rank(ascending=False).sort_values())
    print(scores.loc[WOMEN].rank(ascending=False).sort_values())


if __name__ == '__main__':
    ratings = aggregate_ratings()
    scores = compute_cumulative(ratings)
    ranks(scores)
