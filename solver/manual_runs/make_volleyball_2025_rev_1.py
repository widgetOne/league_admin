#!/usr/bin/env python3
"""
Volleyball 2025 Rev 1 - Load and work with a canned schedule.

This script loads a previously generated schedule from a text file
and creates a schedule object with the key dataframes for further analysis.
It also has functionality to generate a new schedule from the revision 1 facilities.
"""

import pathlib
from ortools.sat.python import cp_model
from ..schedule import Schedule
from ..facilities.facility import Facilities
from .manual_runner import write_volleyball_debug_files, make_schedule_and_debug_files
from ..component_sets.sand_volleyball_template import get_sand_volleyball_template
from ..components.preserve_old_schedule import PreserveOldSchedule


def load_canned_volleyball_schedule():
    """Load a canned volleyball schedule from file and return the schedule object."""
    print("Loading canned volleyball schedule for 2025...")
    
    # Path to the canned schedule file
    current_dir = pathlib.Path(__file__).parent.parent
    schedule_file_path = current_dir / "scratch" / "last_volleyball_schedule 2025-06-18.txt"
    
    if not schedule_file_path.exists():
        print(f"❌ Schedule file not found: {schedule_file_path}")
        return None
    
    print(f"📁 Reading schedule from: {schedule_file_path}")
    
    # Parse the canned schedule
    schedule = Schedule.parse_canned_schedule(str(schedule_file_path))
    
    # Get the dataframes
    game_report = schedule.get_game_report()
    team_report = schedule.get_team_report()
    
    # Print summary information
    print(f"✅ Schedule loaded successfully!")
    print(f"📊 Games: {len(game_report)} total games")
    print(f"👥 Teams: {len(team_report)} teams")
    print(f"📅 Date range: {game_report['date'].min()} to {game_report['date'].max()}")
    print(f"🏐 Weekends: {game_report['weekend_idx'].nunique()} weekends")
    
    # Show some sample data
    print(f"\n📋 First 5 games:")
    print(game_report.head().to_string(index=False))
    
    print(f"\n📈 Team summary (first 5 teams):")
    print(team_report[['total_play', 'total_ref']].head().to_string())
    
    return schedule


def main():
    """Main function to generate a new schedule from revision 1 facilities."""
    print("Generating new volleyball schedule from revision 1 facilities...")
    
    current_dir = pathlib.Path(__file__).parent.parent
    
    # --- Step 1: Load the 'canned' schedule to use as a base ---
    canned_schedule = load_canned_volleyball_schedule()
    if canned_schedule is None:
        print("❌ Cannot proceed without a canned schedule to lock games.")
        return

    # --- Step 2: Load the new facility configuration ---
    facilities_file_path = current_dir / "facilities" / "configs" / "volleyball_2025_revision_1.yaml"
    if not facilities_file_path.exists():
        print(f"❌ Facilities file not found: {facilities_file_path}")
        return
    
    print(f"📁 Loading facilities from: {facilities_file_path}")
    facilities = Facilities.from_yaml(str(facilities_file_path))
    
    # --- Step 3: Prepare the component list ---
    # Get the standard set of components
    schedule_components = get_sand_volleyball_template()
    
    # Create and add the new component to preserve the first 4 weekends
    weekends_to_lock = [1, 2, 3, 4]
    preserve_component = PreserveOldSchedule(canned_schedule, weekends_to_lock)
    schedule_components.append(preserve_component)
    
    # --- Step 4: Generate the new schedule ---
    schedule, _ = make_schedule_and_debug_files(
        facilities,
        base_dir=current_dir,
        components=schedule_components
    )
    
    if schedule:
        print(f"\n🎯 Schedule object ready for further analysis!")
    else:
        print(f"❌ Failed to generate schedule.")


def main_canned():
    """Alternative main function to load and work with the canned schedule."""
    schedule = load_canned_volleyball_schedule()
    
    if schedule is not None:
        print(f"\n🎯 Schedule object ready for further analysis!")
        # TODO: Add more analysis or processing here as needed
    else:
        print(f"❌ Failed to load schedule.")


if __name__ == "__main__":
    main() 