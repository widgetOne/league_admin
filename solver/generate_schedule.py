"""
Core schedule generation engine.

Runs the volleyball scheduler one or more times, caching every valid schedule.
This module contains the logic; CLI argument handling lives in the run scripts.
"""

import pathlib
import time
from datetime import datetime
from . import Facilities
from .component_sets.sand_volleyball_template import get_sand_volleyball_template
from .manual_runs.manual_runner import make_schedule
from .cache_manager import save_schedule_to_cache


def generate_schedules(
    solve_time_minutes: float = 4.0,
    num_schedules: int = None,
    total_time_minutes: float = None,
    update_sheet: bool = False,
):
    """Run the volleyball scheduler multiple times and cache the results.

    Args:
        solve_time_minutes: How long each individual solver run is allowed
            to take, in minutes.  Default 4 minutes.
        num_schedules: How many schedules to generate.  Mutually exclusive
            with ``total_time_minutes``.
        total_time_minutes: Total wall-clock budget for generating schedules.
            Mutually exclusive with ``num_schedules``.
        update_sheet: If True, upload the best cached schedule to Google
            Sheets after generation completes.  Default False.

    If both ``num_schedules`` and ``total_time_minutes`` are None, defaults
    to generating 1 schedule.

    Raises:
        ValueError: If both num_schedules and total_time_minutes are provided.
    """
    # ── Validation ────────────────────────────────────────────────────
    if num_schedules is not None and total_time_minutes is not None:
        raise ValueError(
            "Cannot specify both num_schedules and total_time_minutes. "
            "Pick one strategy."
        )
    if num_schedules is None and total_time_minutes is None:
        num_schedules = 1  # sensible default

    solve_time_seconds = solve_time_minutes * 60.0

    # ── Setup ─────────────────────────────────────────────────────────
    print("Running Multi-Run Volleyball Scheduler...")
    if num_schedules is not None:
        print(f"  Strategy: generate {num_schedules} schedule(s), {solve_time_minutes:.1f} min each")
    else:
        print(f"  Strategy: generate schedules for {total_time_minutes:.1f} min total, {solve_time_minutes:.1f} min each")

    solver_dir = pathlib.Path(__file__).parent  # solver/
    facilities_yaml_path = solver_dir / "facilities" / "configs" / "volleyball.yaml"

    # For final schedule prep, uncomment to fetch team_counts from Google Sheets:
    # from .exports.gsheets_export import get_team_counts_from_sheets
    # team_counts = get_team_counts_from_sheets()
    # facilities = Facilities.from_yaml(str(facilities_yaml_path), team_counts=team_counts)

    facilities = Facilities.from_yaml(str(facilities_yaml_path))
    print(f"Team counts from YAML: {facilities.team_counts}")
    print("Facilities loaded.")

    schedule_components = get_sand_volleyball_template()

    best_score = float('inf')
    improved_runs = 0
    completed_runs = 0
    session_start = time.monotonic()

    # ── Run loop ──────────────────────────────────────────────────────
    run_num = 0
    while True:
        run_num += 1

        # Check termination condition
        if num_schedules is not None:
            if run_num > num_schedules:
                break
            label = f"RUN {run_num}/{num_schedules}"
        else:
            elapsed_minutes = (time.monotonic() - session_start) / 60.0
            if elapsed_minutes >= total_time_minutes:
                break
            remaining = total_time_minutes - elapsed_minutes
            label = f"RUN {run_num} ({remaining:.1f} min remaining)"

        print(f"\n{'=' * 60}")
        print(label)
        print(f"{'=' * 60}")

        try:
            run_start_time = datetime.now()
            schedule, creator = make_schedule(
                facilities, schedule_components,
                solve_time_seconds=solve_time_seconds,
            )

            if not schedule.has_solution:
                print(f"❌ Run {run_num} found no solution — skipping.")
                continue

            current_score = schedule.solver.ObjectiveValue()
            completed_runs += 1
            print(f"Run {run_num} completed with objective score: {current_score:,.2f}")

            # Cache every valid schedule
            try:
                save_schedule_to_cache(schedule, run_start_time, current_score, creator)
            except Exception as e:
                print(f"⚠️ Failed to cache schedule locally: {e}")

            if current_score < best_score:
                print(
                    f"🎉 NEW BEST SCORE for this session! "
                    f"Improved from {best_score if best_score != float('inf') else 'inf'} "
                    f"to {current_score:,.2f}"
                )
                best_score = current_score
                improved_runs += 1
            else:
                print(f"No improvement. Session best remains: {best_score:,.2f}")

        except Exception as e:
            print(f"❌ Run {run_num} failed: {e}")
            continue

    # ── Summary ───────────────────────────────────────────────────────
    elapsed = (time.monotonic() - session_start) / 60.0
    print(f"\n{'=' * 60}")
    print("MULTI-RUN SUMMARY")
    print(f"{'=' * 60}")
    print(f"Runs attempted: {run_num - 1}")
    print(f"Valid schedules cached: {completed_runs}")
    print(f"Improvements found: {improved_runs}")
    print(f"Session best score: {best_score if best_score != float('inf') else 'None'}")
    print(f"Total elapsed time: {elapsed:.1f} min")

    if update_sheet and completed_runs > 0:
        print("\n📤 Uploading best cached schedule to Google Sheets...")
        try:
            from .cache_manager import get_best_cached_schedule
            from .exports.gsheets_export import (
                export_cached_schedule_to_sheets,
                test_sheets_connection,
                get_team_counts_from_sheets,
            )

            # Validate team counts match before uploading
            sheet_team_counts = get_team_counts_from_sheets()
            if list(facilities.team_counts) != list(sheet_team_counts):
                print(
                    f"⚠️  Team count mismatch! YAML has {facilities.team_counts} "
                    f"but Sheet has {sheet_team_counts}. Skipping upload."
                )
            elif test_sheets_connection():
                csv_path, debug_path = get_best_cached_schedule(facilities)
                if csv_path:
                    export_cached_schedule_to_sheets(csv_path, debug_path)
                    print("✅ Sheet updated!")
                else:
                    print("⚠️  No cached schedule found to upload.")
            else:
                print("⚠️  Google Sheets connection failed. Skipping upload.")
        except Exception as e:
            print(f"⚠️  Sheet upload failed: {e}")
    elif update_sheet:
        print("\n⚠️  No valid schedules generated — nothing to upload.")
    else:
        print(
            f"\nDone! Run get_volleyball_schedule.py to upload the "
            f"best cached result to Google Sheets."
        )
