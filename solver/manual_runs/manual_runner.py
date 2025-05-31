from typing import Optional, Set, Any
from ..facilities.facility import Facilities
from ..schedule_component import ScheduleModel

def make_schedule(
    facilities: Facilities,
    constraints: Set[Any],
) -> ScheduleModel:
    """Make a scheduling optimization with the given facilities and constraints.
    
    Args:
        facilities: The Facilities object containing all facility constraints
        constraints: Set of constraint objects to apply to the schedule
        model: Optional existing model to use instead of creating a new one
        
    Returns:
        ScheduleModel: The solved schedule model
    """
    # Create or use existing model
    model = ScheduleModel(facilities)
    
    # Add all constraints
    for constraint in constraints:
        model.add_constraint(constraint)
    
    # Solve the model
    model.solve()
    
    return model 