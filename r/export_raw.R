# =============================================================================
# One-off: download raw AFL Tables results via fitzRoy and save them as a CSV,
# so the R and Python pipelines read exactly the same input.
#
# Run once from the repository root:  Rscript r/export_raw.R
# =============================================================================

library(fitzRoy)

raw_results <- fetch_results_afltables(season = 2016:2025)

dir.create("data", showWarnings = FALSE)
write.csv(raw_results, "data/raw_results.csv", row.names = FALSE)

cat("Wrote", nrow(raw_results), "rows to data/raw_results.csv\n")
