from typing import List, Optional, Iterable
from ortools.sat.python import cp_model
from .facilities.facility import Facilities
from .schedule import Schedule
from .schedule_component import SchedulerComponent

class ScheduleCreator:
    """A factory class for creating and configuring Schedule instances."""
    
    def __init__(self, 
                 facilities: Facilities, 
                 model: Optional[cp_model.CpModel] = None,
                 components: Optional[Iterable[SchedulerComponent]] = None):
        """Initialize the ScheduleCreator.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            model: Optional OR-Tools model. If None, creates a new CpModel.
            components: Optional iterable of SchedulerComponents to apply
        """
        self.facilities = facilities
        if model is not None:
            self.model = model
        else:
            self.model = cp_model.CpModel()
        self.components = list(components) if components is not None else []
    
    def add_component(self, component: SchedulerComponent):
        """Add a single component to the schedule.
        
        Args:
            component: SchedulerComponent to add
        """
        self.components.append(component)
    
    def add_components(self, components: Iterable[SchedulerComponent]):
        """Add multiple components to the schedule.
        
        Args:
            components: Iterable of SchedulerComponents to add
        """
        self.components.extend(components)
    
    def create_schedule(self) -> Schedule:
        """Create and configure a Schedule instance.
        
        Returns:
            Schedule: A fully configured Schedule instance ready for solving
        """
        # Create the base schedule
        schedule = Schedule(self.facilities, self.model)
        
        # Apply all components
        for component in self.components:
            # Add constraints from the component
            for constraint in component._constraints:
                constraint(schedule)
            
            # Add optimizers from the component
            for optimizer in component._optimizers:
                optimizer(schedule)
        
        self.model.solve()

        # Validate that that schedule meets all constraints
        for validator in component._validators:
            validator(schedule)
        
        # Apply any post-processing
        for post_processor in component._post_processors:
            post_processor(schedule)
        
        return schedule 