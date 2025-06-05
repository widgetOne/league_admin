import pathlib
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

if __name__ == "__main__":
    main() 