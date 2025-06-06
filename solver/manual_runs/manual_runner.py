from typing import Optional, Set, Any, Iterable, Tuple
import pathlib
from ..facilities import Facilities
from ..schedule import Schedule
from ..schedule_creator import ScheduleCreator
from ..schedule_component import SchedulerComponent

def make_schedule(facilities: Facilities, components: Iterable[SchedulerComponent]) -> Tuple[Schedule, ScheduleCreator]:
    """Make a scheduling optimization with the given facilities and constraints.
    
    Args:
        facilities: The Facilities object containing all facility constraints
        components: Iterable of SchedulerComponents to apply to the schedule
        
    Returns:
        Tuple[Schedule, ScheduleCreator]: The solved schedule and the creator (for debug reports)
    """
    # Create schedule creator
    creator = ScheduleCreator(facilities, components=components)
    
    # Create and configure the schedule
    schedule = creator.create_schedule()
    
    return schedule, creator

def write_volleyball_debug_files(schedule: Schedule, creator: ScheduleCreator, base_dir: pathlib.Path):
    """Write volleyball schedule and debug reports to files.
    
    Args:
        schedule: The solved schedule
        creator: The schedule creator (contains debug reports)
        base_dir: The base directory to write files to (should contain 'scratch' subdirectory)
    """
    # Get the human-readable schedule
    debug_schedule = schedule.get_volleyball_debug_schedule()
    
    # Ensure the scratch directory exists
    scratch_dir = base_dir / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    
    # Write schedule to file
    output_file = scratch_dir / "last_volleyball_schedule.txt"
    with open(output_file, 'w') as f:
        f.write("VOLLEYBALL SCHEDULE DEBUG OUTPUT\n")
        f.write("="*50 + "\n")
        f.write(debug_schedule)
    
    # Generate and write debug reports
    debug_reports = creator.generate_debug_reports(schedule)
    debug_report_file = scratch_dir / "last_volleyball_debug_reports.txt"
    with open(debug_report_file, 'w') as f:
        f.write(debug_reports)
    
    print(f"\nSchedule written to: {output_file}")
    print(f"Debug reports written to: {debug_report_file}") 