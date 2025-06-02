from pathlib import Path
from ..facilities import Facilities
from ..solver import SchedulerSolver
from ..component_sets.sand_volleyball_template import get_sand_volleyball_template
from .manual_runner import make_schedule

def main():
    # Get the directory of this file
    current_dir = Path(__file__).parent.parent
    
    # Load the volleyball facilities
    facilities = Facilities.from_yaml(str(current_dir / "facilities" / "configs" / "volleyball_2025.yaml"))
    
    # Get the sand volleyball template components
    schedule_components = get_sand_volleyball_template()
    
    # Make the schedule
    solver = make_schedule(facilities, schedule_components)
    
    # Print the result
    print("Schedule created successfully!")
    print(solver)

if __name__ == "__main__":
    main() 