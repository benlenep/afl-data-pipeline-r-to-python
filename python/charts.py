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
    theme, theme_minimal, annotate, scale_color_manual, scale_y_continuous
)

ROOT = Path(__file__).resolve().parents[1]

COL_GOLD, COL_BLUE, COL_RED = "#F5A623", "#3B82F6", "#EF4444"
COL_DARK, COL_TEXT, COL_TEXT_LIGHT = "#0F172A", "#94A3B8", "#CBD5E1"
EARLY, REST = "Early (Rds 0-6)", "Rest of Season"
COL_GREEN, COL_TEAL = "#22C55E", "#14B8A6"


def theme_afl():
    """The dark theme from app.R. Copy your version from Session 11."""
    return theme_minimal(base_size = 13) + theme(
        plot_background   = element_rect(fill = COL_DARK, colour = "none"),
        panel_background  = element_rect(fill = COL_DARK, colour = "none"),
        panel_grid_major  = element_line(colour = "#404040", size = 0.3),
        panel_grid_minor  = element_blank(),
        text              = element_text(colour = COL_TEXT_LIGHT),
        axis_text         = element_text(colour = COL_TEXT),
        plot_title        = element_text(colour = "white", face = "bold", size = 15),
        legend_background = element_rect(fill = COL_DARK, colour = "none"),
        legend_title      = element_blank(),
        legend_position   = "top",
    )
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
    season_matches = match_data[match_data["season"] == season]
    season_avg = season_matches["avg_team_score"].mean()

    df = (
        season_matches
        .groupby("round", as_index=False)
        .agg(avg_team_score=("avg_team_score", "mean"))
        .assign(phase=lambda d: np.where(d["round"] <= 6, EARLY, REST))
    )
    rounds = df["round"].tolist()
    n_rounds = len(rounds)

    gg = (
        ggplot(df, aes(x="round", y="avg_team_score", fill="phase"))
            + geom_col(width=0.85, alpha=0.85)
            + scale_fill_manual(values={EARLY: COL_GOLD, REST: COL_BLUE})
            + scale_x_continuous(breaks=rounds, labels=round_labels(rounds))
            + geom_hline(yintercept=season_avg, linetype="dashed", color=COL_RED)
            + labs(x="Round", y="Avg Points Per Team")
            + theme_afl()
            + theme(axis_text_x=element_text(
                    size=8 if n_rounds > 15 else 10,
                    angle=45 if n_rounds > 18 else 0,
                    ha="right" if n_rounds > 18 else "center",
                    ))
    )
    return gg


def season_comparison_chart(round_summary, seasons):
    """Round-by-round average points per team for several seasons, overlaid."""
    seasons = sorted(seasons, reverse=True)
    df = (
        round_summary[round_summary["season"].isin(seasons)]
        .assign(season=lambda d: d["season"].astype(str))
    )

    # Each season's average across all its matches: weight each round by its games,
    # so short rounds (the Opening Round, byes) don't count as much as full ones
    season_avgs = (
        df.assign(points=lambda d: d["avg_team_score"] * d["games"])
        .groupby("season", as_index=False)
        .agg(points=("points", "sum"), games=("games", "sum"))
        .assign(season_avg=lambda d: d["points"] / d["games"])
    )

    # Colours as in app.R: green, gold, blue for up to three seasons (newest first),
    # otherwise a blue-to-red ramp
    if len(seasons) <= 3:
        palette = [COL_GREEN, COL_GOLD, COL_BLUE][: len(seasons)]
    else:
        ramp = [COL_BLUE, COL_TEAL, COL_GREEN, COL_GOLD, COL_RED]
        palette = [ramp[round(i * (len(ramp) - 1) / (len(seasons) - 1))] for i in range(len(seasons))]
    season_cols = dict(zip([str(s) for s in seasons], palette))

    rounds = sorted(df["round"].unique().tolist())
    top = df["avg_team_score"].max()

    return (
        ggplot(df, aes(x="round", y="avg_team_score", color="season"))
        + geom_line(size=1.1, alpha=0.85)
        + geom_point(size=2.5, alpha=0.85)
        + geom_hline(season_avgs, aes(yintercept="season_avg", color="season"),
                     linetype="dashed", size=0.4, alpha=0.5)
        + geom_vline(xintercept=6.5, linetype="dotted", color="grey", size=0.5)
        + annotate("text", x=6.5, y=top + 3, label="Early | Rest", color="grey", size=9)
        + scale_color_manual(values=season_cols, breaks=list(season_cols))
        + scale_x_continuous(breaks=rounds, labels=round_labels(rounds))
        + scale_y_continuous(labels=lambda ys: [f"{y:g} pts" for y in ys])
        + labs(x="Round", y="Avg points per team", color="Season",
               title="Round-by-round scoring comparison",
               subtitle="Comparing: " + ", ".join(str(s) for s in sorted(seasons)))
        + theme_afl()
        + theme(legend_position="right", plot_subtitle=element_text(color=COL_TEXT, size=11))
    )


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
