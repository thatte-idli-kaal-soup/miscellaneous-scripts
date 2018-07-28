#!/usr/bin/env python
from collections import OrderedDict
import glob
from os.path import abspath, basename, dirname, join

import pandas as pd

MIN_RATINGS = 5  # Minimum number of ratings required to show aggregate
PLAYER_ROLES = None
HANDLER_WEIGHTS = OrderedDict(
    # Throwing - 30
    # Receiving - 15
    # Defense - 30
    # Off-field - 5
    [
        ('Skill', 15),
        ('Throwing-Decision', 15),
        ('Mobility', 5),
        ('Cuts', 5),
        ('Receiving-Decision', 5),
        ('Zone', 10),
        ('Person defense', 10),
        ('Disc-mark', 10),
        ('Sideline Support', 5),
        ('Team Player', 0),
        ('Spirit & Attitude', 0),
    ]
)
CUTTER_WEIGHTS = HANDLER_WEIGHTS
WEIGHTS = {'cutter': CUTTER_WEIGHTS, 'handler': HANDLER_WEIGHTS}
TOTAL = sum(HANDLER_WEIGHTS.values())
HERE = dirname(abspath(__file__))


def read_ratings(csv_path, normalize_columns=True):
    """Read peer ratings from a single CSV/xlsx file."""
    all_data = []
    for sheet in ('Men', 'Women'):
        data = pd.read_excel(
            csv_path,
            sheet_name=sheet,
            skiprows=4,
            header=None,
            index_col=0,
            names=HANDLER_WEIGHTS.keys(),
        )
        data.index = [name.strip() for name in data.index]
        data.index.name = 'Players'
        if normalize_columns:
            data = normalize_ratings(data)
        all_data.append(data)
    return all_data


def normalize_ratings(data):
    """Normalize the ratings

    Scores for men & women *MUST* be passed separately to this function - the
    problems with men & women being rated on same scale by some people and on
    different scales by others, would be fixed this way. Some women on the team
    felt women should have a separate scale at least for the Physical Ability
    parameters - Speed, Endurance, Fitness.

    Also, We normalize each column separately, instead of normalizing the
    aggregated scores.

    """

    def normalize_column(x):
        "Scale to the column to the range 1 - 5."
        return (x - x.min()) / (x.max() - x.min()) * 4 + 1

    return data.apply(normalize_column)


def aggregate_ratings(data_dir, normalize_columns=True):
    """Calculate the aggregate ratings for players.

    Average the ratings every player obtained for all the parameters.

    The aggregates are computed/shown only for players with at least
    MIN_RATINGS number of ratings

    """
    root = join(HERE, data_dir)
    DATA = {
        csv: read_ratings(csv, normalize_columns=normalize_columns)
        for csv in sorted(glob.glob(join(root, '*.xlsx')))
    }
    sample = list(DATA.values())[0]
    totals = [s.copy() for s in sample]  # Men and Women
    counts = [s.copy() for s in sample]
    for gender, total in enumerate(totals):
        total[:] = 0
        counts[gender][:] = 0
    for csv, data in DATA.items():
        for gender, d in enumerate(data):
            totals[gender] += d.fillna(0)
            counts[gender] += d.notna()
    aggregates = [
        total / counts[gender] for gender, total in enumerate(totals)
    ]
    return [
        aggregate[counts[gender] >= MIN_RATINGS]
        for gender, aggregate in enumerate(aggregates)
    ]


def iter_players(ratings, player_roles=None):
    for i, gender in enumerate(('men', 'women')):
        if player_roles:
            for role in ('cutter', 'handler'):
                weights = WEIGHTS[role]
                players = ratings[i].loc[player_roles[gender][role]]
                yield gender, role, players, weights

        else:
            role = 'all'
            players = ratings[i]
            weights = HANDLER_WEIGHTS
            yield gender, role, players, weights


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


def accumulate_ratings(data_dir):
    """Create one Excel file with all the ratings."""
    root = join(HERE, data_dir)
    DATA = {
        csv: read_ratings(csv, normalize_columns=False)
        for csv in sorted(glob.glob(join(root, '*.xlsx')))
    }
    export_path = join(root, 'output', 'all-ratings.xlsx')
    writer = pd.ExcelWriter(export_path)
    for csv_path, data in DATA.items():
        for i, gender in enumerate(('men', 'women')):
            name = basename(csv_path).split('.', 1)[0]
            data[i].to_excel(writer, sheet_name='{}-{}'.format(name, gender))
    writer.save()
    print('Exported single file with all inputs: {}'.format(export_path))


def main(data_dir):
    accumulate_ratings(data_dir)
    ratings = aggregate_ratings(data_dir)
    export_path = join(HERE, data_dir, 'output', 'rankings.xlsx')
    writer = pd.ExcelWriter(export_path)
    for gender, role, players, weights in iter_players(ratings, PLAYER_ROLES):
        scores = compute_cumulative(players, weights)
        cumulative = players.copy()
        cumulative[scores.name] = scores
        rankings = cumulative.sort_values(by=scores.name, ascending=False)
        rankings.to_excel(writer, sheet_name='{}-{}'.format(role, gender))
    writer.save()
    print('Exported rankings: {}'.format(export_path))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir', type=str)
    args = parser.parse_args()
    main(args.data_dir)
