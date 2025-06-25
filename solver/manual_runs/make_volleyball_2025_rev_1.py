#!/usr/bin/env python3
"""
Volleyball 2025 Rev 1 - Load and work with a canned schedule.

This script loads a previously generated schedule from a text file
and creates a schedule object with the key dataframes for further analysis.
"""

import pathlib
from ..schedule import Schedule


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
    """Main function to load and work with the canned schedule."""
    schedule = load_canned_volleyball_schedule()
    
    if schedule is not None:
        print(f"\n🎯 Schedule object ready for further analysis!")
        # TODO: Add more analysis or processing here as needed
    else:
        print(f"❌ Failed to load schedule.")


if __name__ == "__main__":
    main() 