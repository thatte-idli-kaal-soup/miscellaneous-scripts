#!/usr/bin/env python

from collections import OrderedDict
import os
from os.path import abspath, basename, dirname, join

import matplotlib.pyplot as plt
import pandas as pd

from players import (
    MEN, MEN_CUTTERS, MEN_HANDLERS,
    WOMEN, WOMEN_CUTTERS, WOMEN_HANDLERS,
)
MIN_RATINGS = 5  # Minimum number of ratings required to show aggregate
HANDLER_WEIGHTS = OrderedDict([
    # Physical Ability - 15
    ('Speed', 5),
    ('Endurance', 5),
    ('Fitness', 5),

    # Throwing - 30
    ('Skill', 15),
    ('Throwing-Decision', 15),

    # Receiving - 15
    ('Mobility', 5),
    ('Cuts', 5),
    ('Receiving-Decision', 5),

    # Defense - 20
    ('Zone', 10),
    ('Man-mark', 10),

    # Off-field - 20
    ('Sideline Support', 5),
    ('Team Player', 5),
    ('Spirit', 5),
    ('Attitude', 5)
])

CUTTER_WEIGHTS = OrderedDict([
    # Physical Ability - 20
    ('Speed', 5),
    ('Endurance', 10),
    ('Fitness', 5),

    # Throwing - 25
    ('Skill', 10),
    ('Throwing-Decision', 15),

    # Receiving - 15
    ('Mobility', 5),
    ('Cuts', 5),
    ('Receiving-Decision', 5),

    # Defense - 25
    ('Zone', 13),
    ('Man-mark', 12),

    # Off-field - 15
    ('Sideline Support', 5),
    ('Team Player', 5),
    ('Spirit', 2.5),
    ('Attitude', 2.5)
])
TOTAL = sum(HANDLER_WEIGHTS.values())
HERE = dirname(abspath(__file__))


def iter_data(root_dir):
    """Iterate over all the available ratings files."""
    for root, dirs, files in os.walk(root_dir):
        for name in files:
            if not name.endswith('.csv') and not name.endswith('.xlsx'):
                continue
            yield join(root, name)


def read_ratings(csv_path, normalize_columns=True):
    """Read peer ratings from a single CSV/xlsx file."""
    reader = pd.read_excel if csv_path.endswith('.xlsx') else pd.read_csv
    data = reader(csv_path, skiprows=9, header=None, index_col=0, names=HANDLER_WEIGHTS.keys())
    data.index = [name.strip() for name in data.index]
    data.index.name = 'Players'
    if normalize_columns:
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

    data_men = data.loc[MEN]
    data_women = data.loc[WOMEN]

    def normalize_column(x):
        "Scale to the column to the range 1 - 5."
        return (x - x.min()) / (x.max() - x.min()) * 4 + 1

    n_data_men = data_men.apply(normalize_column)
    n_data_women = data_women.apply(normalize_column)

    return n_data_men.append(n_data_women)


def aggregate_ratings(normalize_columns=True):
    """Calculate the aggregate ratings for players.

    Average the ratings every player obtained for all the parameters.

    The aggregates are computed/shown only for players with at least
    MIN_RATINGS number of ratings

    """
    root = join(HERE, '../data/peer-review/')
    DATA = {csv: read_ratings(csv, normalize_columns=normalize_columns) for csv in iter_data(root)}

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


def compute_cumulative(ratings, weights=None):
    """Computes the cumulative rating based on weights for each column."""

    if weights is None:
        scores = ratings.mean(axis=1)
        scores.name = 'Average Score'

    else:
        def weighted_column(x):
            return x * weights[x.name] / TOTAL

        scores = ratings.apply(weighted_column).sum(axis=1)
        scores.name = 'Weighted Score'

    return scores


def plot_correlations(ratings):
    """Plots the correlations between different ratings columns."""

    ax = plt.matshow(ratings.corr())
    ax.figure.set_size_inches(10, 10)
    loc = pd.np.arange(len(HANDLER_WEIGHTS))
    labels = HANDLER_WEIGHTS.keys()
    plt.xticks(loc, labels, rotation=90)
    plt.yticks(loc, labels)
    plt.colorbar()
    plt.show()


def accumulate_ratings():
    """Create one Excel file with all the ratings."""

    root = join(HERE, '../data/peer-review/')
    DATA = {csv: read_ratings(csv, normalize_columns=False) for csv in iter_data(root)}

    export_path = join(HERE, '..', 'data', 'all-ratings.xlsx')
    writer = pd.ExcelWriter(export_path)
    for csv_path, data in DATA.items():
        name = basename(csv_path).split('.', 1)[0]
        data.to_excel(writer, sheet_name=name)
    writer.save()


if __name__ == '__main__':
    ratings = aggregate_ratings()
    export_path = join(HERE, '..', 'data', 'rankings.xlsx')
    writer = pd.ExcelWriter(export_path)
    for role in ('cutter', 'handler'):
        for gender in ('men', 'women'):
            if gender == 'men' and role == 'cutter':
                weights = CUTTER_WEIGHTS
                players = ratings.loc[MEN_CUTTERS]
            elif gender == 'men' and role == 'handler':
                weights = HANDLER_WEIGHTS
                players = ratings.loc[MEN_HANDLERS]
            elif gender == 'women' and role == 'cutter':
                weights = CUTTER_WEIGHTS
                players = ratings.loc[WOMEN_CUTTERS]
            elif gender == 'women' and role == 'handler':
                weights = HANDLER_WEIGHTS
                players = ratings.loc[WOMEN_HANDLERS]
            scores = compute_cumulative(players, weights)
            cumulative = players.copy()
            cumulative[scores.name] = scores
            rankings = cumulative.sort_values(by=scores.name, ascending=False)
            rankings.to_excel(writer, sheet_name='{}-{}'.format(role, gender))
    writer.save()
