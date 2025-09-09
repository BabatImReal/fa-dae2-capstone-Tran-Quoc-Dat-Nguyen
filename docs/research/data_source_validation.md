## Data Schema Overview

This project uses two main data sources for basketball analytics:

### 1. Batch/Static Source: Kaggle Basketball Dataset
- Contains extensive basketball statistics, player information, and game records.
- Suitable for historical analysis, player and team profiling, and machine learning applications.
- Main CSV files included:
  - common_player_info.csv: Basic information about players (e.g., name, birthdate, nationality, height, weight).
  - draft_combine_stats.csv: NBA draft combine results and physical/athletic stats for draft prospects.
  - draft_history.csv: Historical NBA draft picks and related details.
  - game.csv: Core game metadata (game IDs, dates, teams, locations).
  - game_info.csv: Additional game-level information (attendance, officials, arena, etc.).
  - game_summary.csv: Summary statistics for each game (totals, scores, etc.).
  - inactive_players.csv: List of players who were inactive for specific games.
  - line_score.csv: Line scores for each team in every game (quarter-by-quarter and totals).
  - officials.csv: Information about game officials (referees) for each game.
  - other_stats.csv: Additional player or team statistics not covered elsewhere.
  - play_by_play.csv: Detailed play-by-play event logs for each game (actions, timestamps, players involved).
  - player.csv: Player roster and career information (IDs, team associations, positions, etc.).
  - team.csv: Team roster and basic team information.
  - team_details.csv: Extended team details (ownership, location, founding year, etc.).
  - team_history.csv: Historical changes in team names, locations, or franchises.
  - team_info_common.csv: Common team metadata (abbreviations, conference, division, etc.).

### 2. Real-Time Source: API-NBA (RapidAPI)
- Provides real-time and historical NBA basketball data, including games, teams, players, statistics, and standings.
- Enables advanced analytics such as player performance tracking and game outcome prediction.

For details on the evaluation and validation of data sources used in this project, see the research notes in [docs/research/data_source_validation.md](docs/research/data_source_validation.md).
