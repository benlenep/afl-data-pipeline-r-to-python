# =============================================================================
# AFL match data pipeline: the R version
#
# Adapted from fetch_afl_data.R and app.R. Reads the raw AFL Tables export and
# writes the three outputs the Python pipeline must reproduce exactly:
#   r_outputs/match_data.csv     one row per home-and-away match
#   r_outputs/round_summary.csv  one row per season and round
#   r_outputs/phase_summary.csv  one row per season and phase
#
# Run from the repository root:  Rscript r/pipeline.R
# =============================================================================

suppressPackageStartupMessages(library(dplyr))

raw <- read.csv("data/raw_results.csv", stringsAsFactors = FALSE)

# ---- 1. Home-and-away matches only --------------------------------------------
ha_results <- raw %>%
  filter(Round.Type == "Regular")

# ---- 2. Nicknames ----------------------------------------------------------------
nickname_lookup <- c(
  "Adelaide"               = "Crows",
  "Brisbane Lions"         = "Lions",
  "Carlton"                = "Blues",
  "Collingwood"            = "Magpies",
  "Essendon"               = "Bombers",
  "Fremantle"              = "Dockers",
  "Geelong"                = "Cats",
  "Gold Coast"             = "Suns",
  "GWS"                    = "Giants",
  "Greater Western Sydney" = "Giants",
  "Hawthorn"               = "Hawks",
  "Melbourne"              = "Demons",
  "North Melbourne"        = "Kangaroos",
  "Port Adelaide"          = "Power",
  "Richmond"               = "Tigers",
  "St Kilda"               = "Saints",
  "Sydney"                 = "Swans",
  "West Coast"             = "Eagles",
  "Western Bulldogs"       = "Bulldogs"
)

get_nickname <- function(team) {
  nick <- unname(nickname_lookup[team])
  ifelse(is.na(nick), "", nick)
}

# ---- 3. Opening Round detection --------------------------------------------------
# A Round 1 with fewer than 7 games is a partial Opening Round (2024 onwards).
r1_game_counts <- ha_results %>%
  filter(Round.Number == 1) %>%
  group_by(Season) %>%
  summarise(r1_games = n(), .groups = "drop")

opening_round_seasons <- r1_game_counts %>%
  filter(r1_games < 7) %>%
  pull(Season)

# ---- 4. Match-level table --------------------------------------------------------
match_data <- ha_results %>%
  mutate(
    season         = as.integer(Season),
    home_team      = Home.Team,
    home_nickname  = get_nickname(Home.Team),
    away_team      = Away.Team,
    away_nickname  = get_nickname(Away.Team),
    home_score     = as.integer(Home.Points),
    away_score     = as.integer(Away.Points),
    venue          = Venue,
    is_opening     = (Season %in% opening_round_seasons & Round.Number == 1),
    round          = case_when(
      is_opening ~ 0L,
      Season %in% opening_round_seasons ~ as.integer(Round.Number) - 1L,
      TRUE ~ as.integer(Round.Number)
    ),
    round_name     = case_when(
      is_opening ~ "Opening Round",
      Season %in% opening_round_seasons ~ paste0("R", as.integer(Round.Number) - 1L),
      TRUE ~ Round
    ),
    combined_score = home_score + away_score,
    avg_team_score = combined_score / 2,
    margin         = abs(home_score - away_score),
    winning_team   = case_when(
      home_score > away_score ~ home_team,
      away_score > home_score ~ away_team,
      TRUE ~ "Draw"
    ),
    home_100_plus  = home_score >= 100,
    away_100_plus  = away_score >= 100,
    season_phase   = ifelse(round <= 6, "Early (Rds 0-6)", "Mid/Late Season")
  ) %>%
  select(
    season, round, round_name,
    home_team, home_nickname, away_team, away_nickname,
    home_score, away_score, venue,
    combined_score, avg_team_score, margin,
    winning_team, home_100_plus, away_100_plus, season_phase
  ) %>%
  arrange(season, round)

# ---- 5. Summaries (as in app.R) --------------------------------------------------
round_summary <- match_data %>%
  group_by(season, round) %>%
  summarise(
    games           = n(),
    avg_team_score  = mean(avg_team_score),
    avg_combined    = mean(combined_score),
    avg_margin      = mean(margin),
    median_combined = median(combined_score),
    max_combined    = max(combined_score),
    min_combined    = min(combined_score),
    pct_100_plus    = mean(home_score >= 100 | away_score >= 100) * 100,
    .groups = "drop"
  )

phase_summary <- match_data %>%
  mutate(phase = ifelse(round <= 6, "Early (Rds 0-6)", "Rest of Season")) %>%
  group_by(season, phase) %>%
  summarise(
    games          = n(),
    avg_team_score = mean(avg_team_score),
    avg_combined   = mean(combined_score),
    avg_margin     = mean(margin),
    pct_100_plus   = mean(home_score >= 100 | away_score >= 100) * 100,
    .groups = "drop"
  )

# ---- 6. Write outputs ------------------------------------------------------------
dir.create("r_outputs", showWarnings = FALSE)
write.csv(match_data,    "r_outputs/match_data.csv",    row.names = FALSE)
write.csv(round_summary, "r_outputs/round_summary.csv", row.names = FALSE)
write.csv(phase_summary, "r_outputs/phase_summary.csv", row.names = FALSE)

cat("Opening Round seasons:", paste(opening_round_seasons, collapse = ", "), "\n")
cat("Wrote", nrow(match_data), "matches,", nrow(round_summary), "rounds and",
    nrow(phase_summary), "season phases to r_outputs/\n")
