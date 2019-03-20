#!/usr/bin/env python3
"""Script to process the data collected in Ulti-Analytics for the TIKS league.

Computes the scores for games, and also the additional on-field and off-field
scoring.

NOTE: The Elapsed Time is assumed to be not accurate since the data was entered
from videos that were recorded.

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

import pandas as pd


def parse_match(url):
    data = pd.read_csv(url)
    points = data.groupby(
        ["Our Score - End of Point", "Their Score - End of Point"]
    )
    additional_points = 0
    for score, point in points:
        if is_all_touch(point):
            additional_points += 0.5

            if is_perfect_score(point):
                additional_points += 0.5

        if has_no_turnovers(point):
            additional_points += 0.5

    print(additional_points)


def is_all_touch(point):
    """Is it an all-touch point?"""

    n = point_num_players(point)

    # How is all-touch defined? Between turns? Or between scores? To keep it
    # simple, let's say between scores. The idea is to see if everyone on the
    # field is involved. So, between scores is fine!
    passers = point["Passer"]
    touchers = passers.dropna()
    return len(touchers) == n


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


def has_no_turnovers(point):
    """Check if the team remains on offense since they first got on offense."""
    offense = point[point["Event Type"] == "Offense"]
    idx = offense.index
    return idx.min() + len(offense) == idx.max() + 1


def is_perfect_score(point):
    """Check if all players have touched the disc, and exactly once!"""

    n = point_num_players(point)
    num_touches = n - 1
    events = point[-num_touches:]
    return (
        num_touches
        == len(set(events["Passer"]))
        == len(set(events["Receiver"]))
    )


def main(url):
    parse_match()


if __name__ == "__main__":
    url = "/tmp/stats.csv"
    main()
