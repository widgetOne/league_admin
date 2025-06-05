#!/usr/bin/env python3

import sys
import pathlib
sys.path.append('.')

from solver import Facilities
from solver.manual_runs.manual_runner import make_schedule
from solver.component_sets.sand_volleyball_template import get_sand_volleyball_template

def test_reports():
    print("Running Volleyball Scheduler for 2025...")
    
    # Load facilities from YAML like the main script does
    current_dir = pathlib.Path(__file__).parent / "solver"
    facilities_yaml_path = current_dir / "facilities" / "configs" / "volleyball_2025.yaml"
    facilities = Facilities.from_yaml(str(facilities_yaml_path))
    
    print("Facilities loaded.")
    
    # Get components
    schedule_components = get_sand_volleyball_template()
    
    # Create schedule
    schedule = make_schedule(facilities, schedule_components)
    
    print("\n=== Testing get_game_report ===")
    try:
        game_report = schedule.get_game_report()
        print(f"Game report shape: {game_report.shape}")
        print("First 5 games:")
        print(game_report.head())
    except Exception as e:
        print(f"Error getting game report: {e}")
    
    print("\n=== Testing get_team_report ===")
    try:
        team_report = schedule.get_team_report()
        print(f"Team report shape: {team_report.shape}")
        print("Team report:")
        print(team_report)
    except Exception as e:
        print(f"Error getting team report: {e}")

if __name__ == "__main__":
    test_reports() 