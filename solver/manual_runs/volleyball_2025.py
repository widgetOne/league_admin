from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from facilities.facility import Facilities
from manual_runs.manual_runner import make_schedule

def main():
    # Get the directory of this file
    current_dir = Path(__file__).parent.parent
    
    # Load the volleyball facilities
    facilities = Facilities.from_yaml(str(current_dir / "facilities" / "configs" / "volleyball_2025.yaml"))
    
    # Create empty set of constraints for now
    constraints = set()
    
    # Make the schedule
    solver = make_schedule(facilities, constraints)
    
    # Print the result
    print("Schedule created successfully!")
    print(solver)

if __name__ == "__main__":
    main() 