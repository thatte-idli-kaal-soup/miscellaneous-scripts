#!/usr/bin/env python3
"""Script to process the data collected in Ulti-Analytics for the TIKS league.

Computes the scores for games, and also the additional on-field and off-field
scoring.

NOTE: The Elapsed Time column should be ignored, since all the data was entered
from recorded videos.

Off field scoring(Counts towards League points) +2.5
1. Team with equal number of passes betweeen M-M, M-W, W-M, W-W
2. Fastest D
3. Most pull participation across the team
4. Longest O-Point without a turn
5. Women huck score

On field scoring(Counts towards goal tally, per game)
1. All touch +0.5
2. No turnovers +0.5
3. Callahan +0.5
4. 6 Pass score with all touch(After turn or after pull) +1

"""

from argparse import ArgumentParser
from collections import Counter, defaultdict
import glob
from os.path import basename, join, splitext
from pprint import pprint
from typing import (  # noqa
    Tuple,
    List,
    Generator,
    Dict,
    Set,
    Counter as TCounter,
    Any,
)

import pandas as pd
from pandas import DataFrame as DF, Series

from gender import FEMALE, ALL

# Data-helpers #########################################################


def find_match_data(
    data_dir: str
) -> Generator[Tuple[str, List[str]], None, None]:
    """Returns pairs of CSV file paths - one file per each team.

    This function assumes that the files are named in the format:
    `<team1>-<team2>-<game-id>.csv` and `<team2>-<team1>-<game-id>.csv`.

    If a match has only one file, the match is skipped.

    """
    csv_files = glob.glob(join(data_dir, "*.csv"))
    matches = defaultdict(list)  # type: Dict[str, List[str]]
    for path in csv_files:
        name = splitext(basename(path))[0]
        key = "-".join(tuple(sorted(name.split("-"))))
        matches[key].append(path)
    for game_id, match in matches.items():
        if len(match) < 2:
            print("Skipping match: {}".format(match))
            continue
        yield game_id, match


def iter_points(data: DF) -> Generator[Tuple[Tuple[int, int], DF], None, None]:
    """Iterator over match score and points tuples"""
    points = data.groupby(
        ["Our Score - End of Point", "Their Score - End of Point"]
    )
    for score, point in points:
        if point["Action"].iloc[-1] != "Goal":
            idx = point[point["Action"] == "Goal"].index[0]
            point = point.loc[:idx]
        assert point["Action"].iloc[-1] == "Goal"
        yield score, point


def player_gender(name: str) -> str:
    assert name in ALL, "{} not listed".format(name)
    return "F" if name in FEMALE else "M"


def point_gender_ratio(point: DF) -> Tuple[int, int]:
    """Get gender ratio for a point.

    NOTE: This is also computed per point, intentionally! We allow changing
    gender ratios based on squad size.

    """

    players = point_players(point)
    counts = Counter(map(player_gender, players))
    ratio = [c for _, c in sorted(counts.items())]
    return ratio[0], ratio[1]


def point_num_players(point: DF) -> int:
    """Get number of players playing in a point.

    NOTE: This is computed per point, instead of per game, intentionally! We
    allow the number of players to change during games, based on squad size.

    """
    player_columns = [c for c in point.columns if c.startswith("Player ")]
    players = sum(
        [
            1
            for column in player_columns
            if len(point[column].dropna()) == len(point)
        ]
    )
    return players


def point_players(point: DF) -> Set[str]:
    """Return the names of players who played a point."""
    n = point_num_players(point)
    select_columns = point.columns.map(lambda x: x.startswith("Player "))
    columns = point.loc[:, select_columns]
    players = columns.iloc[0][:n]
    return set(players)


def read_game_data(game_urls: List[str]) -> Dict[str, DF]:
    """Read the CSV file pair for the match and a data dict."""
    game_data = [pd.read_csv(url) for url in game_urls]
    data_1, data_2 = game_data
    name_1 = data_2["Opponent"].iloc[0]
    name_2 = data_1["Opponent"].iloc[0]
    return {name_1: data_1, name_2: data_2}


# On-field scoring #####################################################


def is_all_touch(point: DF) -> bool:
    """Is it an all-touch point?"""

    n = point_num_players(point)

    # How is all-touch defined? Between turns? Or between scores? To keep it
    # simple, let's say between scores. The idea is to see if everyone on the
    # field is involved. So, between scores is fine!
    passers = point["Passer"].dropna()
    catchers = point["Receiver"].dropna()
    touches = (set(passers) | set(catchers)) - {"Anonymous"}
    return len(touches) == n


def has_no_turnovers(point: DF) -> bool:
    """Check if the team remains on offense since they first got on offense."""
    offense = point[point["Event Type"] == "Offense"]
    idx = offense.index
    return bool(
        # Team keeps possession till the end
        (point.index.max() == idx.max())
        # Team didn't lose possession in between, once on Offense
        and ((idx.min() + len(offense)) == (idx.max() + 1))
    )


def is_perfect_score(point: DF) -> bool:
    """Check if all players have touched the disc, and exactly once!"""

    n = point_num_players(point)
    num_touches = n - 1
    events = point[-num_touches:]
    passers = set(events["Passer"].dropna()) - {"Anonymous"}
    catchers = set(events["Receiver"].dropna()) - {"Anonymous"}
    return num_touches == len(passers) == len(catchers)


def on_field_score_team(
    points: Generator[Tuple[Tuple[int, int], DF], None, None]
) -> Tuple[int, float]:
    """Compute on-field score of a team.

    Return (Goals, Additional Points)
    """
    additional_points = 0.0
    for score, point in points:
        if is_all_touch(point):
            additional_points += 0.5

            if is_perfect_score(point):
                additional_points += 0.5

        if has_no_turnovers(point):
            additional_points += 0.5

    ours, theirs = score
    return (ours, additional_points)


def on_field_score_game(game_data: Dict[str, DF]) -> None:
    scores = {
        name: on_field_score_team(iter_points(data))
        for name, data in game_data.items()
    }
    for name, score in scores.items():
        print("{name}: {score[0]} + {score[1]}".format(name=name, score=score))


# Off-field scoring ####################################################


def passes_by_gender(data: DF) -> TCounter[str]:
    """Return count of passes by gender (M-M, M-F, F-M, F-F)."""

    def f(row: Series) -> str:
        passer, catcher = row
        return "{}-{}".format(player_gender(passer), player_gender(catcher))

    offense = data[data["Event Type"] == "Offense"]
    # Included unsuccessful passes too, since we are looking for the intent to pass
    passes = offense[
        offense["Action"].str.startswith(("Catch", "Goal", "Drop"))
    ]
    gender_passes = passes[["Passer", "Receiver"]].apply(f, axis=1)
    return Counter(gender_passes)


def expected_passes_count(data: DF) -> Dict[str, float]:
    """Return the count of expected passes by gender."""

    gender_ratio_passes = defaultdict(
        lambda: 0
    )  # type: Dict[Tuple[int, int], float]
    expected_passes = defaultdict(lambda: 0)  # type: Dict[str, float]

    for score, point in iter_points(data):
        offense = point[point["Event Type"] == "Offense"]
        passes = offense[
            offense["Action"].str.startswith(("Catch", "Goal", "Drop"))
        ]
        g_ratio = point_gender_ratio(point)
        gender_ratio_passes[g_ratio] += len(passes)

    for (f, m), count in gender_ratio_passes.items():
        n = m + f
        m_m = (m / n) * ((m - 1) / (n - 1)) * count
        m_f = (m / n) * (f / (n - 1)) * count
        f_m = (f / n) * (m / (n - 1)) * count
        f_f = (f / n) * ((f - 1) / (n - 1)) * count
        expected_passes["M-M"] += m_m
        expected_passes["M-F"] += m_f
        expected_passes["F-M"] += f_m
        expected_passes["F-F"] += f_f

    return expected_passes


def pullers(data: DF) -> Set[str]:
    # Pull or PullOb for out-of-bounds
    return set(data[data["Action"].str.startswith("Pull")]["Defender"])


def no_turn_score_pass_count(point: DF) -> int:
    """Number of passes made before score, without a turnover.

    The team could start on O or D. We count number of passes after the team
    gained possession for the first time.

    """

    count = (
        len(point[point["Event Type"] == "Offense"])
        if has_no_turnovers(point)
        else 0
    )
    return count


def longest_no_turn_score(data: DF) -> int:
    return max(
        no_turn_score_pass_count(point) for _, point in iter_points(data)
    )


def split_posession_change(point: DF) -> List[DF]:
    """Split a point by posession change.

    Events which happened between two turnovers are grouped together.

    """
    change_events = ("Throwaway", "D", "Drop", "Goal")
    changes = point[point["Action"].str.startswith(change_events)]
    start = [point.index[0]] + list(changes.index + 1)
    end = changes.index
    split_point = [point.loc[x:y] for x, y in zip(start, end)]
    return split_point


def d_pass_count(team_a: DF, team_b: DF) -> Tuple[int, int]:
    """Return number of passes before which each team got a D.

    Returns a tuple (count_a, count_b) where count_a is the number of passes
    Team B had before Team A got a D.

    """
    count_a = count_b = pd.np.inf

    split_point = zip(
        split_posession_change(team_a), split_posession_change(team_b)
    )
    for A, B in split_point:
        if len(A) == 1 and A.Action.iloc[0] == "D":
            count_a = min(count_a, len(B) - 1)

        elif len(B) == 1 and B.Action.iloc[0] == "D":
            count_b = min(count_b, len(A) - 1)

        else:
            continue

    return count_a, count_b


def fastest_d(game_data: List[Tuple[str, DF]]) -> Dict[str, int]:
    """Returns the fastest D for each team in a game."""

    names = [name for name, _ in game_data]
    team_wise_points = [
        [point for _, point in iter_points(team_data)]
        for _, team_data in game_data
    ]
    points = zip(*team_wise_points)

    passes_before_d = defaultdict(
        lambda: pd.np.inf
    )  # type: Dict[str, pd.np.float]
    for point in points:
        for name, count in zip(names, d_pass_count(*point)):
            passes_before_d[name] = min(count, passes_before_d[name])

    return passes_before_d


def off_field_scoring(
    tournament_data: Dict[str, List[Tuple[str, DF]]]
) -> None:
    """Compute the off-field scores for the whole tournament."""

    tournament_pullers = defaultdict(set)  # type: Dict[str, Set[str]]
    tournament_passes_by_gender = defaultdict(
        lambda: defaultdict(lambda: 0)
    )  # type: Dict[str, Dict[str, int]]
    expected_passes_by_gender = defaultdict(
        lambda: defaultdict(lambda: 0)
    )  # type: Dict[str, Dict[str, float]]
    tournament_longest_o_point = defaultdict(lambda: 0)  # type: Dict[str, int]
    tournament_d_pass_count = defaultdict(
        lambda: pd.np.inf
    )  # type: Dict[str, pd.np.float]

    for game_id, game in tournament_data.items():
        for team, team_data in game:
            # Passes by Gender
            for player_genders, count in passes_by_gender(team_data).items():
                tournament_passes_by_gender[team][player_genders] += count

            # Expected passes by Gender
            for genders, e_count in expected_passes_count(team_data).items():
                expected_passes_by_gender[team][genders] += e_count

            # Pullers
            tournament_pullers[team].update(pullers(team_data))

            # Longest no turn scores
            score = longest_no_turn_score(team_data)
            previous = tournament_longest_o_point[team]
            tournament_longest_o_point[team] = max(score, previous)

        for team, d_pass_count in fastest_d(game).items():
            previous = tournament_d_pass_count[team]
            tournament_d_pass_count[team] = min(previous, d_pass_count)

    # FIXME: How do we score?
    print(
        "Division of passes by gender for each team: "
        "(followed by expected distribution)"
    )
    for team, pass_data in tournament_passes_by_gender.items():
        pprint(team)
        pprint(dict(pass_data))
        pprint(dict(expected_passes_by_gender[team]))

    # FIXME: Take into account total number of pulls made by each team?
    print("Pullers by team:")
    pprint(dict(tournament_pullers))

    print("Longest number of passes before a score:")
    pprint(
        sorted(
            tournament_longest_o_point.items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )

    print("Number of passes before the team got a D:")
    pprint(dict(tournament_d_pass_count))


# Main  ################################################################


def main(data_dir: str) -> None:
    matches = find_match_data(data_dir)
    tournament_data = defaultdict(
        list
    )  # type: Dict[str, List[Tuple[str, DF]]]
    for game_id, urls in matches:
        game_data = read_game_data(urls)
        on_field_score_game(game_data)
        print("*" * 40)
        for team, data in game_data.items():
            tournament_data[game_id].append((team, data))
    off_field_scoring(tournament_data)


if __name__ == "__main__":
    parser = ArgumentParser(prog=__file__, usage=__doc__.splitlines()[0])
    parser.add_argument("data_dir", help="Directory with .csv data")
    args = parser.parse_args()
    main(args.data_dir)
