from typing import Optional, Set, Any
from ..facilities import Facilities
from ..components import SchedulerSolver

def make_schedule(
    facilities: Facilities,
    constraints: Set[Any],
) -> SchedulerSolver:
    """Make a scheduling optimization with the given facilities and constraints.
    
    Args:
        facilities: The Facilities object containing all facility constraints
        constraints: Set of constraint objects to apply to the schedule
        
    Returns:
        SchedulerSolver: The solved scheduler
    """
    # Create solver
    solver = SchedulerSolver(facilities)
    
    # Add all constraints
    for constraint in constraints:
        solver.add_constraint(constraint)
    
    # Solve the model
    solver.solve()
    
    return solver 