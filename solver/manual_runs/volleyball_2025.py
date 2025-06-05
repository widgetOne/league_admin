import pathlib
import os
from .. import Facilities, Schedule # Import Facilities and Schedule from solver package
# from ..components import TotalPlayConstraint # Removed this problematic import
from ..component_sets.sand_volleyball_template import get_sand_volleyball_template
from .manual_runner import make_schedule # This seems unused now

def main():
    """Load facilities and run the volleyball scheduler."""
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
    
    # Make the schedule
    schedule = make_schedule(facilities, schedule_components)
    # Print the result
    print("Schedule created successfully!")
    print(schedule)
    
    # Get the human-readable schedule and write to file
    debug_schedule = schedule.get_volleyball_debug_schedule()
    
    # Ensure the scratch directory exists
    scratch_dir = current_dir / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    
    # Write to file
    output_file = scratch_dir / "last_volleyball_schedule.txt"
    with open(output_file, 'w') as f:
        f.write("VOLLEYBALL SCHEDULE DEBUG OUTPUT\n")
        f.write("="*50 + "\n")
        f.write(debug_schedule)
    
    print(f"\nSchedule written to: {output_file}")


if __name__ == "__main__":
    main() 