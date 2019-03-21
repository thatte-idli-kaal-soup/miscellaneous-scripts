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

from collections import Counter

import pandas as pd


# Data-helpers #########################################################


def iter_points(data):
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


def point_num_players(point):
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


# On-field scoring #####################################################


def is_all_touch(point):
    """Is it an all-touch point?"""

    n = point_num_players(point)

    # How is all-touch defined? Between turns? Or between scores? To keep it
    # simple, let's say between scores. The idea is to see if everyone on the
    # field is involved. So, between scores is fine!
    passers = point["Passer"].dropna()
    catchers = point["Receiver"].dropna()
    touches = (set(passers) | set(catchers)) - {"Anonymous"}
    return len(touches) == n


def has_no_turnovers(point):
    """Check if the team remains on offense since they first got on offense."""
    offense = point[point["Event Type"] == "Offense"]
    idx = offense.index
    return (
        # Team keeps possession till the end
        point.index.max() == idx.max()
        # Team didn't lose possession in between, once on Offense
        and idx.min() + len(offense) == idx.max() + 1
    )


def is_perfect_score(point):
    """Check if all players have touched the disc, and exactly once!"""

    n = point_num_players(point)
    num_touches = n - 1
    events = point[-num_touches:]
    passers = set(events["Passer"].dropna()) - {"Anonymous"}
    catchers = set(events["Receiver"].dropna()) - {"Anonymous"}
    return num_touches == len(passers) == len(catchers)


def on_field_score_team(points):
    """Compute on-field score of a team.

    Return (Goals, Additional Points)
    """
    additional_points = 0
    for score, point in points:
        if is_all_touch(point):
            additional_points += 0.5

            if is_perfect_score(point):
                additional_points += 0.5

        if has_no_turnovers(point):
            additional_points += 0.5

    ours, theirs = score
    return (ours, additional_points)


# Off-field scoring ####################################################


def passes_by_gender(data):
    """Return count of passes by gender (M-M, M-F, F-M, F-F)."""
    from gender import FEMALE, ALL

    def player_gender(name):
        assert name in ALL, "{} not listed".format(name)
        return "F" if name in FEMALE else "M"

    def f(row):
        passer, catcher = row
        return "{}-{}".format(player_gender(passer), player_gender(catcher))

    catches = data[data["Action"] == "Catch"]  # FIXME: Only completions?
    gender_passes = catches[["Passer", "Receiver"]].apply(f, axis=1)
    return Counter(gender_passes)


def pullers(data):
    # Pull or PullOb for out-of-bounds
    return set(data[data["Action"].str.startswith("Pull")]["Defender"])


def no_turn_score_pass_count(point):
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


def longest_no_turn_score(points):
    return max(no_turn_score_pass_count(point) for _, point in points)


def off_field_scoring(data_1, data_2):
    x = passes_by_gender(data_1)
    y = passes_by_gender(data_2)
    # FIXME: How do we score?
    print(x, y)
    x = pullers(data_1)
    y = pullers(data_2)
    # FIXME: Take into account total number of pulls made by each team?
    print(x, y)
    x = longest_no_turn_score(iter_points(data_1))
    y = longest_no_turn_score(iter_points(data_2))
    print(x, y)
    return


# Main  ################################################################


def main(game_urls):
    game_data = [pd.read_csv(url) for url in game_urls]
    data_1, data_2 = game_data
    score_1 = on_field_score_team(iter_points(data_1))
    score_2 = on_field_score_team(iter_points(data_2))
    name_1 = data_2["Opponent"].iloc[0]
    name_2 = data_1["Opponent"].iloc[0]
    print("{name}: {s[0]:d} + {s[1]:.1f}".format(name=name_1, s=score_1))
    print("{name}: {s[0]:d} + {s[1]:.1f}".format(name=name_2, s=score_2))
    off_field_scoring(data_1, data_2)


if __name__ == "__main__":
    urls = ["/tmp/stats.csv", "/tmp/stats-1.csv"]
    main(urls)
