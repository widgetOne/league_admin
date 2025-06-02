from typing import Optional, Set, Any, Iterable
from ..facilities import Facilities
from ..solver import SchedulerSolver
from ..schedule_component import SchedulerComponent

def make_schedule(facilities: Facilities, components: Iterable[SchedulerComponent]) -> SchedulerSolver:
    """Make a scheduling optimization with the given facilities and constraints.
    
    Args:
        facilities: The Facilities object containing all facility constraints
        constraints: Set of constraint objects to apply to the schedule
        
    Returns:
        SchedulerSolver: The solved scheduler
    """
    # Create solver
    solver = SchedulerSolver(facilities)
    
    # Add all schdule components to solver's model
    for component in components:
        solver += component
    
    # Solve the model
    solver.solve()
    
    return solver 