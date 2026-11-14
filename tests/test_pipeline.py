"""Unit tests: small, hand-made inputs where the right answer is obvious.

These pin down the tricky logic (Opening Round detection and recoding, draws)
independently of the real data, so a failure points straight at the cause.
"""
import pandas as pd

import pipeline


def make_raw(rows):
    """Build a tiny raw table in the AFL Tables format from (season, round_number, round_type, home_pts, away_pts)."""
    return pd.DataFrame([
        {
            "Season": season, "Round.Number": rnd, "Round": f"R{rnd}", "Round.Type": rtype,
            "Home.Team": "Geelong", "Away.Team": "Brisbane Lions",
            "Home.Points": hp, "Away.Points": ap, "Venue": "Kardinia Park",
        }
        for season, rnd, rtype, hp, ap in rows
    ])


def test_filter_regular_drops_finals():
    raw = make_raw([(2023, 1, "Regular", 90, 80), (2023, 25, "Finals", 70, 60)])
    assert len(pipeline.filter_regular(raw)) == 1


def test_opening_round_detected_only_when_round_one_is_short():
    full_round = [(2023, 1, "Regular", 90, 80)] * 9
    partial_round = [(2024, 1, "Regular", 90, 80)] * 4
    ha = make_raw(full_round + partial_round)
    assert pipeline.opening_round_seasons(ha) == [2024]


def test_rounds_recoded_in_opening_round_season():
    ha = make_raw([(2024, 1, "Regular", 90, 80), (2024, 2, "Regular", 90, 80)])
    md = pipeline.build_match_data(ha, [2024])
    assert list(md["round"]) == [0, 1]
    assert list(md["round_name"]) == ["Opening Round", "R1"]


def test_rounds_unchanged_in_normal_season():
    ha = make_raw([(2023, 1, "Regular", 90, 80), (2023, 2, "Regular", 90, 80)])
    md = pipeline.build_match_data(ha, [])
    assert list(md["round"]) == [1, 2]
    assert list(md["round_name"]) == ["R1", "R2"]


def test_winner_draw_and_derived_fields():
    ha = make_raw([(2023, 1, "Regular", 100, 80), (2023, 1, "Regular", 70, 70)])
    md = pipeline.build_match_data(ha, [])
    assert list(md["winning_team"]) == ["Geelong", "Draw"]
    assert list(md["margin"]) == [20, 0]
    assert list(md["avg_team_score"]) == [90.0, 70.0]
    assert list(md["home_100_plus"]) == [True, False]
    assert list(md["away_nickname"]) == ["Lions", "Lions"]
