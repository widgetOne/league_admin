import pathlib
import os
from .. import Facilities, Schedule
from ..component_sets.sand_volleyball_template import get_sand_volleyball_template
from .manual_runner import make_schedule_and_debug_files
from ..exports.gsheets_export import export_schedule_to_sheets, test_sheets_connection, get_team_counts_from_sheets

def main():
    """Run the volleyball scheduler for the season."""
    print("Running Volleyball Scheduler...")
    current_dir = pathlib.Path(__file__).parent.parent # Get the 'solver' directory
    facilities_yaml_path = current_dir / "facilities" / "configs" / "volleyball.yaml"
    
    # For final schedule prep, uncomment to fetch team_counts from Google Sheets:
    # team_counts = get_team_counts_from_sheets()
    # facilities = Facilities.from_yaml(str(facilities_yaml_path), team_counts=team_counts)

    facilities = Facilities.from_yaml(str(facilities_yaml_path))
    print(f"Team counts from YAML: {facilities.team_counts}")

    # Validate that YAML team_counts match Google Sheets before exporting
    print("Validating team counts against Google Sheets...")
    sheet_team_counts = get_team_counts_from_sheets()
    if list(facilities.team_counts) != list(sheet_team_counts):
        print()
        print("❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌")
        print("❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌")
        print()
        print(
            f"  TEAM COUNT MISMATCH! YAML has {facilities.team_counts} but "
            f"Google Sheet has {sheet_team_counts}. Update one to match the other."
        )
        print()
        print("❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌")
        print("❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌")
        print()
        raise ValueError("Team count mismatch — see above.")
    print(f"✅ Team counts validated: YAML and Sheet both have {facilities.team_counts}")
    print("Facilities loaded.")

    from ..cache_manager import get_best_cached_schedule, save_schedule_to_cache
    from ..exports.gsheets_export import export_cached_schedule_to_sheets
    from datetime import datetime
    
    print("\nChecking local cache for an existing schedule...")
    csv_path, debug_path = get_best_cached_schedule(facilities)
    
    if csv_path:
        print(f"✅ Found cached schedule: {csv_path.name}")
        try:
            print("\nTesting Google Sheets connection...")
            if test_sheets_connection():
                print("\nExporting cached schedule to Google Sheets...")
                export_cached_schedule_to_sheets(csv_path, debug_path)
                
                print("\n📋 Generating individual team schedules...")
                from .make_teamwise_schedules import make_teamwise_schedules
                make_teamwise_schedules()
                print("✅ Individual team schedules generated!")
            else:
                print("⚠️  Skipping Google Sheets export due to connection issues.")
        except Exception as e:
            print(f"⚠️  Google Sheets export failed: {e}")
            
    else:
        print("⚠️ No valid cached schedule found. Generating a new one now...")
        
        # Get the sand volleyball template components
        schedule_components = get_sand_volleyball_template()
        
        run_start_time = datetime.now()
        # Create schedule and write debug files using the new top-level function
        schedule, creator = make_schedule_and_debug_files(
            facilities,
            base_dir=current_dir,
            components=schedule_components
        )
        
        if schedule.has_solution:
            current_score = schedule.solver.ObjectiveValue()
            print(f"Schedule generated successfully. Objective Score: {current_score:,.2f}")
            
            # Cache it
            try:
                save_schedule_to_cache(schedule, run_start_time, current_score, creator)
            except Exception as e:
                print(f"⚠️ Failed to cache schedule locally: {e}")
                
            # Export to Google Sheets
            try:
                print("\nTesting Google Sheets connection...")
                if test_sheets_connection():
                    print("\nExporting schedule to Google Sheets...")
                    export_schedule_to_sheets(schedule, creator)
                    print("Export completed successfully!")
                    
                    print("\n📋 Generating individual team schedules...")
                    from .make_teamwise_schedules import make_teamwise_schedules
                    make_teamwise_schedules()
                    print("✅ Individual team schedules generated!")
                else:
                    print("⚠️  Skipping Google Sheets export due to connection issues.")
            except Exception as e:
                print(f"⚠️  Google Sheets export failed: {e}")
                print("   Local files were still created successfully.")
        else:
            print("❌ Failed to find a feasible schedule.")


if __name__ == "__main__":
    main() 
