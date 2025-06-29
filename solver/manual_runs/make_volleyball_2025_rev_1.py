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
    
    # Path to the facilities configuration
    current_dir = pathlib.Path(__file__).parent.parent
    facilities_file_path = current_dir / "facilities" / "configs" / "volleyball_2025_revision_1.yaml"
    
    if not facilities_file_path.exists():
        print(f"❌ Facilities file not found: {facilities_file_path}")
        return
    
    print(f"📁 Loading facilities from: {facilities_file_path}")
    
    # Load facilities
    facilities = Facilities.from_yaml(str(facilities_file_path))
    
    # Get the sand volleyball template components
    schedule_components = get_sand_volleyball_template()
    
    # Create schedule and write debug files using the new top-level function
    schedule, _ = make_schedule_and_debug_files(
        facilities,
        base_dir=current_dir,
        components=schedule_components
    )
    
    if schedule is not None:
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