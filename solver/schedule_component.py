from abc import ABC, abstractmethod
from typing import List, Callable, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import
if TYPE_CHECKING:
    from .schedule import Schedule

class ModelActor(ABC):
    """Base class for any object that can act on the model.
    
    These are function which act on the schedule model based on
    concrete realities from the facilities object.
    """
    def __init__(self, actor_function: Callable[['Schedule'], None]):
        """Initialize with a function that acts on the model.
        
        Args:
            actor_function: Function that takes a Schedule object
        """
        self._actor_function = actor_function

    def __call__(self, schedule_obj: 'Schedule'):
        """Call the actor function with the given schedule object."""
        self._actor_function(schedule_obj)

class DebugReporter:
    """Class for debug report functions that return strings instead of acting on the model."""
    
    def __init__(self, report_function: Callable[['Schedule'], str], component_name: str):
        """Initialize with a function that generates a debug report.
        
        Args:
            report_function: Function that takes a Schedule object and returns a debug string
            component_name: Name of the component this report belongs to
        """
        self._report_function = report_function
        self._component_name = component_name

    def __call__(self, schedule_obj: 'Schedule') -> str:
        """Call the report function with the given schedule object."""
        return self._report_function(schedule_obj)
    
    @property
    def component_name(self) -> str:
        """Get the name of the component this report belongs to."""
        return self._component_name

class SchedulerComponent:
    """Base class for all scheduler components.
    
    A component can add constraints, optimizers, validators, or post-processors
    to the scheduling model.
    """
    def __init__(self):
        """Initialize empty lists for each type of manipulator."""
        self._constraints: List[ModelActor] = []
        self._optimizers: List[ModelActor] = []
        self._validators: List[ModelActor] = []
        self._post_processors: List[ModelActor] = []
        self._debug_reports: List[DebugReporter] = []
        self._component_classes: List[str] = [self.__class__.__name__]

    def add_constraint(self, constraint: ModelActor):
        """Add a constraint to the component.
        
        Args:
            constraint: The constraint to add
        """
        self._constraints.append(constraint)

    def add_optimizer(self, optimizer: ModelActor):
        """Add an optimizer to the component.
        
        Args:
            optimizer: The optimizer to add
        """
        self._optimizers.append(optimizer)

    def add_validator(self, validator: ModelActor):
        """Add a validator to the component.
        
        Args:
            validator: The validator to add
        """
        self._validators.append(validator)

    def add_post_processor(self, post_processor: ModelActor):
        """Add a post-processor to the component.
        
        Args:
            post_processor: The post-processor to add
        """
        self._post_processors.append(post_processor)

    def add_debug_report(self, debug_report: DebugReporter):
        """Add a debug report to the component.
        
        Args:
            debug_report: The debug report function to add
        """
        self._debug_reports.append(debug_report)

    def get_component_classes(self) -> List[str]:
        """Get the list of component class names that make up this component.
        
        Returns:
            List of class names
        """
        return self._component_classes.copy()

    def __add__(self, other: 'SchedulerComponent') -> 'SchedulerComponent':
        """Combine two components.
        
        Args:
            other: Another component to combine with
        
        Returns:
            A new component containing all manipulators from both components
        """
        if not isinstance(other, SchedulerComponent):
            return NotImplemented
        result = SchedulerComponent()
        result._constraints = self._constraints + other._constraints
        result._optimizers = self._optimizers + other._optimizers
        result._validators = self._validators + other._validators
        result._post_processors = self._post_processors + other._post_processors
        result._debug_reports = self._debug_reports + other._debug_reports
        result._component_classes = self._component_classes + other._component_classes
        return result

    def __iadd__(self, other: 'SchedulerComponent') -> 'SchedulerComponent':
        """Add another component to this one in place.
        
        Args:
            other: Another component to add
        
        Returns:
            self, with the other component's manipulators added
        """
        if not isinstance(other, SchedulerComponent):
            return NotImplemented
        self._constraints.extend(other._constraints)
        self._optimizers.extend(other._optimizers)
        self._validators.extend(other._validators)
        self._post_processors.extend(other._post_processors)
        self._debug_reports.extend(other._debug_reports)
        self._component_classes.extend(other._component_classes)
        return self

class EqualSeasonPlay(SchedulerComponent):
    """Component that ensures equal number of games played per team."""
    def __init__(self, total_season_play_target: int):
        super().__init__()
        self.add_constraint(ModelActor(self.generate_equal_season_play_constraints(total_season_play_target)))

    def generate_equal_season_play_constraints(self, total_season_play_target: int) -> Callable[['Schedule'], None]:
        def apply_equal_play_constraint(schedule: 'Schedule'):
            print(f"Validator concept: Ensuring teams play {total_season_play_target} games.")
            # Example constraint implementation would go here
            pass
        return apply_equal_play_constraint

