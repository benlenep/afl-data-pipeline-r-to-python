"""AFL match data pipeline: the Python version.

Reproduces r/pipeline.R step by step. Each function below matches one step of the
R script. Replace each `raise NotImplementedError` with your code, one function
at a time, and run the tests after each one:

    uv run pytest

Run the whole pipeline from the repository root:

    uv run python python/pipeline.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

NICKNAMES = {
    "Adelaide": "Crows",
    "Brisbane Lions": "Lions",
    "Carlton": "Blues",
    "Collingwood": "Magpies",
    "Essendon": "Bombers",
    "Fremantle": "Dockers",
    "Geelong": "Cats",
    "Gold Coast": "Suns",
    "GWS": "Giants",
    "Greater Western Sydney": "Giants",
    "Hawthorn": "Hawks",
    "Melbourne": "Demons",
    "North Melbourne": "Kangaroos",
    "Port Adelaide": "Power",
    "Richmond": "Tigers",
    "St Kilda": "Saints",
    "Sydney": "Swans",
    "West Coast": "Eagles",
    "Western Bulldogs": "Bulldogs",
}

EARLY = "Early (Rds 0-6)"


def load_raw(path):
    """Read the raw AFL Tables export (the read.csv step)."""
    return pd.read_csv(path)


def filter_regular(raw):
    """Keep home-and-away matches only: filter(Round.Type == "Regular").

    Column names keep R's dots, so use raw["Round.Type"]. Return a .copy() so later
    steps do not modify `raw`.
    """
    return raw[raw["Round.Type"] == "Regular"].copy()
    raise NotImplementedError


def opening_round_seasons(ha):
    """Return the seasons whose Round 1 has fewer than 7 games, as a sorted list of ints.

    R: filter(Round.Number == 1) %>% group_by(Season) %>% summarise(n()) %>% filter(< 7) %>% pull(Season)
    """
    opening = (
        ha[ha["Round.Number"] == 1]
        .groupby("Season")
        .size()
        .reset_index(name="count")
        .query("count < 7")
        .sort_values("Season")["Season"]
        .tolist()
    )
    return opening
    raise NotImplementedError


def build_match_data(ha, opening_seasons):
    """Build the match-level table, matching the mutate/select/arrange in r/pipeline.R.

    Columns, in this order: season, round, round_name, home_team, home_nickname,
    away_team, away_nickname, home_score, away_score, venue, combined_score,
    avg_team_score, margin, winning_team, home_100_plus, away_100_plus, season_phase.

    Hints:
    - case_when  -> np.select([cond1, cond2], [value1, value2], default=...)
    - %in%       -> ha["Season"].isin(opening_seasons)
    - nicknames  -> .map(NICKNAMES).fillna("")
    - arrange()  -> .sort_values([...], kind="stable"), then .reset_index(drop=True).
      R's arrange keeps tied rows in their original order. pandas does too when sorting
      on several columns, but not on a single column unless you pass kind="stable".

    """
    df = ha.copy()

    season  = df["Season"].astype(int)
    round   = df["Round.Number"].astype(int)

    in_opening = df["Season"].isin(opening_seasons)
    is_opening = in_opening & (round == 1)

    home_score = df["Home.Points"].astype(int)
    away_score = df["Away.Points"].astype(int)

    match_data = pd.DataFrame({
        "season":           season,
        "home_team":        df["Home.Team"],
        "home_nickname":    df["Home.Team"].map(NICKNAMES).fillna(""),
        "away_team":        df["Away.Team"],
        "away_nickname":    df["Away.Team"].map(NICKNAMES).fillna(""),
        "home_score":       home_score,
        "away_score":       away_score,
        "round_number":     round,
        "venue":            df["Venue"]
    })

    match_data["round"] = np.select(
        [is_opening, in_opening],
        [0, round - 1],
        default = round,
    )

    match_data["round_name"] = np.select(
        [is_opening, in_opening],
        ["Opening Round", "R" + (round - 1).astype(str)],
        default=df["Round"]
    )

    match_data["combined_score"]    = match_data["home_score"] + match_data["away_score"]
    match_data["avg_team_score"]    = match_data["combined_score"] / 2
    match_data["margin"]            = (match_data["home_score"] - match_data["away_score"]).abs()

    match_data["winning_team"] = np.select(
        [home_score > away_score, away_score > home_score],
        [match_data["home_team"], match_data["away_team"]],
        default="Draw"
    )

    match_data["home_100_plus"] = home_score >= 100
    match_data["away_100_plus"] = away_score >= 100
    match_data["season_phase"]  = np.where(
        match_data["round"] <= 6, "Early (Rds 0-6)", "Mid/Late Season"
    )

    match_data = (
        match_data[
            [
                "season",
                "round",
                "round_name",
                "home_team",
                "home_nickname",
                "away_team",
                "away_nickname",
                "home_score",
                "away_score",
                "venue",
                "combined_score",
                "avg_team_score",
                "margin",
                "winning_team",
                "home_100_plus",
                "away_100_plus",
                "season_phase",
            ]
        ]
        .sort_values(["season", "round"], kind="stable")
        .reset_index(drop=True)
    )

    return match_data
    raise NotImplementedError





def round_summary(match_data):
    """One row per season and round, as round_summary in app.R.

    Columns: season, round, games, avg_team_score, avg_combined, avg_margin,
    median_combined, max_combined, min_combined, pct_100_plus.
    """
    return (
        match_data
        .assign(any_100 = lambda d: d["home_100_plus"] | d["away_100_plus"])
        .groupby(["season", "round"], as_index=False)
        .agg(
            games           = ("round", "size"),
            avg_team_score  = ("avg_team_score", "mean"),
            avg_combined    = ("combined_score", "mean"),
            avg_margin      = ("margin", "mean"),
            median_combined = ("combined_score", "median"),
            max_combined    = ("combined_score", "max"),
            min_combined    = ("combined_score", "min"),
            pct_100_plus    = ("any_100", "mean"),
        )
        .assign(pct_100_plus=lambda d: d["pct_100_plus"] * 100)
    )
    raise NotImplementedError


def phase_summary(match_data):
    """One row per season and phase, as phase_summary in app.R.

    phase is "Early (Rds 0-6)" for round <= 6, otherwise "Rest of Season".
    (Note: match_data's season_phase says "Mid/Late Season". The two labels differ
    in the original R code, so keep them different here too.)

    Columns: season, phase, games, avg_team_score, avg_combined, avg_margin, pct_100_plus.
    """
    return (
            match_data
            .assign(any_100 = lambda d: d["home_100_plus"] | d["away_100_plus"])
            .assign(phase = lambda d: np.where(d["round"] <= 6, "Early (Rds 0-6)", "Rest of Season"))
            .groupby(["season", "phase"], as_index=False)
            .agg(
                games           = ("round", "size"),
                avg_team_score  = ("avg_team_score", "mean"),
                avg_combined    = ("combined_score", "mean"),
                avg_margin      = ("margin", "mean"),
                pct_100_plus    = ("any_100", "mean"),
            )
            .assign(pct_100_plus=lambda d: d["pct_100_plus"] * 100)
        )
    raise NotImplementedError


def run(raw_path):
    """Run the whole pipeline and return the three outputs by name."""
    ha = filter_regular(load_raw(raw_path))
    match_data = build_match_data(ha, opening_round_seasons(ha))
    return {
        "match_data": match_data,
        "round_summary": round_summary(match_data),
        "phase_summary": phase_summary(match_data),
    }


def write_outputs(outputs, out_dir):
    """Write each output to <out_dir>/<name>.csv."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in outputs.items():
        df.to_csv(out_dir / f"{name}.csv", index=False)


def main():
    outputs = run(ROOT / "data" / "raw_results.csv")
    write_outputs(outputs, ROOT / "py_outputs")
    print({name: len(df) for name, df in outputs.items()})


if __name__ == "__main__":
    main()
