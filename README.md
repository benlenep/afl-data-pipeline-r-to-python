# AFL match data pipeline: R and Python, tested for parity

**Work in progress.** The data pipeline behind my AFL early-season scoring dashboard, being rebuilt in Python and tested against the original R version. The goal is for every Python output to match R exactly, checked automatically with pytest.

## Progress

- [x] Raw 2016 to 2025 results exported from AFL Tables via fitzRoy (`r/export_raw.R`)
- [x] R pipeline producing the three reference outputs (`r/pipeline.R`)
- [x] Python: home-and-away filter
- [x] Python: Opening Round detection (seasons whose Round 1 has fewer than 7 games)
- [x] Python: match table (17 columns), matching R on every row and column
- [x] Python: round and phase summaries
- [x] Parity tests passing for all three outputs
- [ ] Charts ported to plotnine
- [ ] Full write-up

## Findings so far

1. **A bug in the original R pipeline, surfaced by the port.** AFL Tables names the Western Bulldogs "Footscray", but the nickname lookup only covered "Western Bulldogs". Every Bulldogs match since 2016 has had a blank nickname, in the dashboard too. Python reproduces the blank for now, because parity means matching R. The fix will go into both languages together, with the tests confirming they stay in sync.
2. **`mutate` sees its own new columns; pandas does not.** In dplyr, `season_phase = ifelse(round <= 6, ...)` uses the `round` recoded earlier in the same `mutate`. In pandas, a reference to the raw round column silently keeps the old values, which misclassified matches in the Opening Round seasons until I pointed it at the recoded round.
3. **`case_when`'s fallback has to be carried over exactly.** R's `round_name` falls back to the original text label ("R1"), not the round number. Translating it with `np.select` meant making the `default` the original label column, not the number.
4. **Missing values never equal each other.** A quick `==` comparison flagged 109 matching rows as different, because `NaN == NaN` is false in pandas (and `NA == NA` gives `NA` in R). `pandas.testing.assert_frame_equal` treats matching missing values as equal, so the parity tests use it.
5. **Two labels for one phase, kept on purpose.** The original R code labels the later phase "Mid/Late Season" in the match table but "Rest of Season" in the summaries. Python reproduces both, because parity means matching R, quirks included. Like the Footscray nickname, it is a candidate for a coordinated fix in both languages later.

## Run what exists so far

```bash
uv sync
Rscript r/pipeline.R                      # writes r_outputs/
uv run pytest tests/test_pipeline.py -v   # unit tests for the functions ported so far
```

## Data

Match results from [AFL Tables](https://afltables.com) via the [fitzRoy](https://github.com/jimmyday12/fitzRoy) R package.