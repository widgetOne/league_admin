from typing import Optional, Set, Any, Iterable, Tuple
import pathlib
import datetime
from ortools.sat.python import cp_model
from ..facilities import Facilities
from ..schedule import Schedule
from ..schedule_creator import ScheduleCreator
from ..schedule_component import SchedulerComponent

from ..debug_report import write_volleyball_debug_files

def make_schedule(facilities: Facilities, components: Iterable[SchedulerComponent], solve_time_seconds: float = 240.0) -> Tuple[Schedule, ScheduleCreator]:
    """Make a scheduling optimization with the given facilities and constraints.
    
    Args:
        facilities: The Facilities object containing all facility constraints
        components: Iterable of SchedulerComponents to apply to the schedule
        solve_time_seconds: Maximum time in seconds for the solver to run.
        
    Returns:
        Tuple[Schedule, ScheduleCreator]: The solved schedule and the creator (for debug reports)
    """
    # Create schedule creator
    creator = ScheduleCreator(facilities, components=components)
    
    # Create and configure the schedule
    schedule = creator.create_schedule(solve_time_seconds=solve_time_seconds)
    
    return schedule, creator


def make_schedule_and_debug_files(
    facilities: Facilities,
    base_dir: pathlib.Path,
    components: Optional[Iterable[SchedulerComponent]] = None
) -> Tuple[Schedule, Optional[ScheduleCreator]]:
    """
    Generates a schedule, writes debug files, and returns the schedule and creator.

    This function handles two modes:
    1. If components are provided, it uses ScheduleCreator for a full build.
    2. If no components are provided, it does a direct, simple schedule generation.
    
    Args:
        facilities: The Facilities object with all constraints.
        base_dir: The base directory for writing debug files.
        components: Optional list of components for a complex build.
        
    Returns:
        A tuple containing the solved Schedule and the ScheduleCreator (if used).
    """
    creator = None
    if components:
        # Mode 1: Use ScheduleCreator with components
        print("Running schedule generation with components...")
        schedule, creator = make_schedule(facilities, components)
        
        if schedule.has_solution:
            write_volleyball_debug_files(schedule, base_dir, creator=creator)
        else:
            status_name = schedule.solver.StatusName(schedule._last_solve_status)
            print(f"\n❌ No solution found (status: {status_name}). Debug files not written.")
    else:
        # Mode 2: Direct schedule generation
        print("Running direct schedule generation (no components)...")
        model = cp_model.CpModel()
        schedule = Schedule(facilities, model)
        schedule.solve()
        
        if schedule.has_solution:
            write_volleyball_debug_files(schedule, base_dir, creator=None)
        else:
            status_name = schedule.solver.StatusName(schedule._last_solve_status)
            print(f"\n❌ No solution found (status: {status_name}). Debug files not written.")

    if schedule.has_solution:
        print("\n✅ Top-level schedule generation complete!")
    return schedule, creator 