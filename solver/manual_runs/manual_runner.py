from typing import Optional, Set, Any, Iterable
from ..facilities import Facilities
from ..schedule import Schedule
from ..schedule_component import SchedulerComponent

def make_schedule(facilities: Facilities, components: Iterable[SchedulerComponent]) -> Schedule:
    """Make a scheduling optimization with the given facilities and constraints.
    
    Args:
        facilities: The Facilities object containing all facility constraints
        components: Iterable of SchedulerComponents to apply to the schedule
        
    Returns:
        Schedule: The solved schedule
    """
    # Create schedule
    schedule = Schedule(facilities)
    
    # Add all constraints
    schedule.add_constraints(components)
    
    # Solve the model
    schedule.solve()
    
    return schedule 