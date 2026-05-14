# Infeasibility Resolution Plan: Handling Empty Courts and Exhibition Games

The current volleyball scheduling model is over-constrained because it demands a "perfect fit"—every available court must host a valid game, and every team must play exactly the target number of games. With an odd number of teams or odd scheduling days, mathematical perfection is impossible. This plan outlines how we will introduce flexibility to resolve these infeasibilities.

## 1. Handling Empty Courts (Byes)
Currently, `home_team`, `away_team`, and `ref` are constrained to valid team indices `[0, total_teams - 1]`. When we have excess match capacity (like having 126 slots for 113 required games), the solver is forced to assign teams to games they shouldn't play.

**Implementation Steps:**
* **Introduce a Dummy Team:** Add an artificial team index `DUMMY_TEAM = total_teams`. 
* **Expand Variable Domains:** Allow `home_team`, `away_team`, and `ref` variables to take values from `0` to `total_teams` (inclusive).
* **Define `match_active`:** Create a boolean variable `match_active[m]` for each match slot.
* **Link Activity to Teams:** 
  * If `match_active[m] == False`, then `home_team`, `away_team`, and `ref` MUST equal `DUMMY_TEAM`.
  * If `match_active[m] == True`, they must be valid teams `< total_teams`.
* **Update Metrics:** Ensure all constraint tracking matrices (like `is_playing`, `is_ref`, `games_per_day`) ignore the `DUMMY_TEAM`.

## 2. Handling Exhibition Games ("Doesn't Count")
In odd-team scenarios, one team may need to play an 8th game so that an opponent can get their 7th required game. Currently, `TotalPlayConstraint` enforces `sum(is_playing) == games_per_season`, which breaks the solver.

**Implementation Steps:**
* **Separate "Play" from "Official Play":** We will introduce a new boolean matrix `is_official_play[m, team]`.
* **Constrain Official Play:** `is_official_play[m, team] <= is_playing[m, team]`. A game can only be "official" if the team actually played.
* **Update `TotalPlayConstraint`:** Change the constraint from checking `is_playing` to checking `is_official_play`. This allows a team to have `is_playing = 1` but `is_official_play = 0` for an extra "exhibition" game.
* **Objective Function Penalty:** To prevent the solver from adding exhibition games unnecessarily, we will add an objective penalty: `Minimize sum(is_playing - is_official_play)`. This forces the solver to use the absolute minimum number of exhibition games needed.

## 3. Reporting and Export
* **Google Sheets Export:** Modify the export script. If a match is assigned to `DUMMY_TEAM`, output "NO PLAY" instead of a team name. For exhibition games, we will append an asterisk `*` (e.g., `rec_team_5*`) or label it so players know it's an exhibition that doesn't count toward their standings.
