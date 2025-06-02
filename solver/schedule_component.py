from abc import ABC, abstractmethod
from typing import List, Callable
from ortools.sat.python import cp_model
from .facilities.facility import Facilities

class ModelActor(ABC):
    """Base class for any object that can act on the model.
    
    These are function which act on the schedule model based on
    concrete realities from the facilities object.
    """
    def __init__(self, actor_function: Callable[[cp_model.CpModel, Facilities], None]):
        """Initialize with a function that acts on the model.
        
        Args:
            actor_function: Function that takes a model and facilities, then acts on the model
        """
        self._actor_function = actor_function

    def __call__(self, model: cp_model.CpModel, facilities: Facilities):
        """Call the actor function with the given model and facilities."""
        self._actor_function(model, facilities)

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

    def __add__(self, other: 'SchedulerComponent') -> 'SchedulerComponent':
        """Combine two components.
        
        Args:
            other: Another component to combine with
        
        Returns:
            A new component containing all manipulators from both components
        """
        result = SchedulerComponent()
        result._constraints = self._constraints + other._constraints
        result._optimizers = self._optimizers + other._optimizers
        result._validators = self._validators + other._validators
        result._post_processors = self._post_processors + other._post_processors
        return result

    def __iadd__(self, other: 'SchedulerComponent') -> 'SchedulerComponent':
        """Add another component to this one in place.
        
        Args:
            other: Another component to add
        
        Returns:
            self, with the other component's manipulators added
        """
        self._constraints.extend(other._constraints)
        self._optimizers.extend(other._optimizers)
        self._validators.extend(other._validators)
        self._post_processors.extend(other._post_processors)
        return self

class EqualSeasonPlay(SchedulerComponent):
    """Component that ensures equal number of games played per team."""
    def __init__(self, total_season_play):
        super().__init__()
        self._constraints.append(self.generate_equal_season_play_constraints(total_season_play))

    def generate_equal_season_play_constraints(self, total_season_play):
        def apply_equal_play_constraint(schedule):
            for team in schedule.teams:
                if schedule.get_games_played(team) != total_season_play:
                    raise ValueError(f"Team {team} has played {schedule.get_games_played(team)} games, expected {total_season_play}")
        return apply_equal_play_constraint

