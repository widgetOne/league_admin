# League Admin — Volleyball Schedule Optimizer

A constraint-programming-based schedule generator for the Stonewall Volleyball League's
sand volleyball season. Given a facility configuration (courts, time slots, dates) and
team rosters, it produces a balanced schedule that satisfies hard constraints (every team
plays the right number of games, no conflicts) and optimizes soft objectives (time variety,
bye week distribution, reffing balance, etc.).

Results are exported directly to a shared Google Sheet for league-wide distribution.

## Quick Start

```bash
# 1. Activate the venv (direnv does this automatically via .envrc)
source venv/bin/activate

# 2. Verify Google Sheets access still works
python -m manual_tests.test_sheets_access

# 3. Generate a schedule (single run)
python -m solver.manual_runs.volleyball_2026

# 3-alt. Generate a schedule (multi-run optimization, uploads best result)
python -m solver.manual_runs.volleyball_2026_multi_run

# 4. Post-processing exports (run after schedule is on Sheets)
python -m solver.manual_runs.make_league_apps_schedule_2026
python -m solver.manual_runs.make_teamwise_schedules_2026
```

All commands run from the **project root** (`league_admin/`).

## Yearly Workflow

Each season you will:

1. **Update `auth/gsheets_config.yaml`** — point `sheet_url` at the new year's Google
   Sheet, update `team_names` with the new rosters, and confirm tab names.

2. **Create a new facility config** in `solver/facilities/configs/` (e.g.
   `volleyball_2026.yaml`) — set team counts, court layouts, time slots, and game dates.

3. **Create a new manual run script** in `solver/manual_runs/` (e.g.
   `volleyball_2026.py`) — point it at your new facility config. Use a prior year's
   script as a template.

4. **Run the scheduler** — either a single run or multi-run to search for the best
   objective score.

5. **Run post-processing exports** — League Apps CSV format and per-team schedules.
   Create new year-specific versions of these scripts as needed.

6. **Archive the old config** — move the prior year's `gsheets_config.yaml` into
   `auth/old_files/`.

### Mid-Season Revisions

If facility availability changes mid-season, use the revision workflow
(see `make_volleyball_2025_rev_1.py` for an example):

- Create a new facility config with the updated dates/courts.
- Load the existing schedule as a "canned" schedule.
- Use `PreserveOldSchedule` to lock already-played weekends.
- Re-solve only the remaining weekends.

## Project Structure

```
league_admin/
├── auth/                          # Google Sheets credentials (gitignored)
│   ├── gsheets_config.yaml        #   Sheet URL, tab names, team names
│   ├── stonewall-...-token.json   #   Service account auth token
│   └── old_files/                 #   Archived configs from prior years
│
├── solver/                        # Active scheduling system (OR-Tools CP-SAT)
│   ├── facilities/
│   │   ├── facility.py            #   Facility model (loads YAML configs)
│   │   └── configs/               #   Season-specific facility YAML files
│   ├── components/                #   Pluggable constraint & optimization components
│   ├── component_sets/            #   Pre-built bundles of components
│   │   └── sand_volleyball_template.py
│   ├── schedule.py                #   Core Schedule model
│   ├── schedule_creator.py        #   Factory: assembles components, solves, validates
│   ├── schedule_component.py      #   Base class for all components
│   ├── exports/
│   │   └── gsheets_export.py      #   Google Sheets read/write (used by solver)
│   ├── manual_runs/               #   Year-specific run scripts (entry points)
│   │   ├── volleyball_2025.py
│   │   ├── volleyball_2025_multi_run.py
│   │   ├── make_volleyball_2025_rev_1.py
│   │   ├── make_league_apps_schedule_2025.py
│   │   ├── make_teamwise_schedules_2025.py
│   │   └── manual_runner.py       #   Shared run/debug-file logic
│   ├── manual_tests/              #   Solver-specific manual tests
│   ├── scratch/                   #   Debug output files (gitignored)
│   └── templates/                 #   Alternate component templates
│
├── scheduler/                     # Legacy scheduling system (heuristic optimizer)
│   ├── run_regular_season.py      #   Old entry point (last used: 2024 sand season)
│   ├── sheets_access.py           #   Old Google Sheets access (runs from scheduler/)
│   └── ...
│
├── manual_tests/                  # Project-wide manual tests
│   └── test_sheets_access.py      #   Verify Sheets config & auth token
│
├── .envrc                         # direnv: activates venv, sets PYTHONPATH
├── requirements.txt               # pip dependencies
└── setup.py                       # Package setup (editable install)
```

## Schedule Components

The solver uses a pluggable component system. The standard sand volleyball template
(`component_sets/sand_volleyball_template.py`) includes:

| Component | Type | Purpose |
|---|---|---|
| `TotalPlayConstraint` | Constraint | Every team plays the configured number of games |
| `VsPlayBalanceConstraint` | Constraint | Balance head-to-head matchups |
| `BalanceReffingConstraint` | Constraint | Distribute ref duties evenly |
| `OneThingAtATimeConstraint` | Constraint | No team plays and refs at the same time |
| `PlayNearRefConstraint` | Constraint | Teams ref near their own game times |
| `RefSameDivisionConstraint` | Constraint | Teams ref games in their own division |
| `NoThreeHoursDays` | Constraint | No team has a 3+ hour day |
| `TimeVarietyOptimization` | Optimization | Vary each team's game times across the season |
| `ByeWeekOptimization` | Optimization | Spread bye weeks evenly |
| `RecInLowCourtsProcessor` | Post-process | Assign rec division to lower-numbered courts |

Custom components can be added per the `SchedulerComponent` base class.

## Google Sheets Integration

The system uses a service account to read from and write to a shared Google Sheet.
The auth token and config are stored in `auth/` (gitignored).

**Tabs used:**
- `auto_export_schedule` — the main schedule output
- `debug_report_tab` — component debug reports
- `Intermediate Schedule` — cached schedule for post-processing reads
- `league_apps_schedule` — League Apps CSV export
- `teamwise_schedules` — individual team schedules (side-by-side)
- `scratch` — best objective score tracking (multi-run)

## Dependencies

Core: `ortools`, `numpy`, `pandas`, `pyyaml`
Sheets: `gspread-pandas`, `oauth2client`

```bash
pip install -r requirements.txt
pip install gspread-pandas oauth2client pyyaml
pip install -e .  # editable install for the solver package
```

## Legacy System (`scheduler/`)

The `scheduler/` directory contains the original heuristic-based optimizer, last used
for the 2024 sand season. It runs from within the `scheduler/` directory (paths are
relative to `../auth/`). It is functionally replaced by the `solver/` system but
retained for reference.
