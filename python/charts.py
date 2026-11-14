"""Charts for the AFL pipeline, ported from app.R to plotnine.

Fill in each function, then run from the repository root, after the pipeline:

    uv run python python/charts.py

Use the round_by_round_plot and comparison_plot code in your app.R as the reference.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from plotnine import (
    aes, element_blank, element_line, element_rect, element_text, geom_col, geom_hline,
    geom_line, geom_point, geom_vline, ggplot, labs, scale_fill_manual, scale_x_continuous,
    theme, theme_minimal,
)

ROOT = Path(__file__).resolve().parents[1]

COL_GOLD, COL_BLUE, COL_RED = "#F5A623", "#3B82F6", "#EF4444"
COL_DARK, COL_TEXT, COL_TEXT_LIGHT = "#0F172A", "#94A3B8", "#CBD5E1"
EARLY, REST = "Early (Rds 0-6)", "Rest of Season"


def theme_afl():
    """The dark theme from app.R. Copy your version from Session 11."""
    raise NotImplementedError


def round_labels(rounds):
    """Round 0 is the Opening Round, shown as 'Open', as in the app."""
    return ["Open" if r == 0 else str(r) for r in rounds]


def round_by_round_chart(match_data, season):
    """Average points per team by round for one season, coloured by phase.

    1. Filter match_data to the season and average avg_team_score by round
    2. Add a phase column: EARLY for round <= 6, otherwise REST
    3. Bars with fill="phase", a dashed line at the season average, the theme
    4. scale_x_continuous(breaks=rounds, labels=round_labels(rounds)) to show "Open"
    """
    raise NotImplementedError


def season_comparison_chart(round_summary, seasons):
    """Round-by-round average points per team for several seasons, overlaid.

    Convert season to a string first, so plotnine treats it as a category
    (the equivalent of as.factor(season) in your app).
    """
    raise NotImplementedError


def main():
    out_dir = ROOT / "charts"
    out_dir.mkdir(exist_ok=True)
    match_data = pd.read_csv(ROOT / "py_outputs" / "match_data.csv")
    round_summary = pd.read_csv(ROOT / "py_outputs" / "round_summary.csv")
    latest = int(match_data["season"].max())

    round_by_round_chart(match_data, latest).save(
        out_dir / f"round_by_round_{latest}.png", width=10, height=5, dpi=150, verbose=False)
    season_comparison_chart(round_summary, [latest - 2, latest - 1, latest]).save(
        out_dir / "season_comparison.png", width=10, height=5, dpi=150, verbose=False)
    print("Saved charts to", out_dir)


if __name__ == "__main__":
    main()
