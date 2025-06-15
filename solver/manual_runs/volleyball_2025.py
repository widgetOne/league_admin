import pathlib
import os
from .. import Facilities, Schedule
from ..component_sets.sand_volleyball_template import get_sand_volleyball_template
from .manual_runner import make_schedule, write_volleyball_debug_files
from ..exports.gsheets_export import export_schedule_to_sheets, test_sheets_connection

def main():
    """Run the volleyball scheduler for 2025."""
    print("Running Volleyball Scheduler for 2025...")
    current_dir = pathlib.Path(__file__).parent.parent # Get the 'solver' directory
    facilities_yaml_path = current_dir / "facilities" / "configs" / "volleyball_2025.yaml"
    
    # It seems Facilities.from_yaml might not be available or correctly implemented on the base class.
    # If Facilities is an abstract base class for from_yaml, we need a concrete implementation.
    # For now, assuming it works as per the file content of facility.py
    facilities = Facilities.from_yaml(str(facilities_yaml_path))

    print("Facilities loaded.")
    # print(facilities) # Uncomment to see facility details

     # Get the sand volleyball template components
    schedule_components = get_sand_volleyball_template()
    
    # Create and solve the schedule
    schedule, creator = make_schedule(facilities, schedule_components)
    
    # Print the result
    print("Schedule created successfully!")
    print(schedule)
    
    # Write debug files
    write_volleyball_debug_files(schedule, creator, current_dir)
    
    # Export to Google Sheets
    try:
        print("\nTesting Google Sheets connection...")
        if test_sheets_connection():
            print("\nExporting schedule to Google Sheets...")
            export_schedule_to_sheets(schedule, schedule_components)
            print("Export completed successfully!")
        else:
            print("⚠️  Skipping Google Sheets export due to connection issues.")
    except Exception as e:
        print(f"⚠️  Google Sheets export failed: {e}")
        print("   Local files were still created successfully.")


if __name__ == "__main__":
    main() 