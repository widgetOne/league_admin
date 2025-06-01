from abc import ABC, abstractmethod

class ModelActor(ABC):
    """Base class for all model actors.
    
    These are function which act on the schedule model based on
    concrete realities from the facilities object.
    """
    def __init__(self, actor_function: Callable[[cp_model.CpModel, Facilities], None]):
        self._actor_function = actor_function
    
    def __call__(self, model: cp_model.CpModel, facilities: Facilities):
        """Apply the actor to the model.
        
        This will add logic to the model based on the numbers and realities
        imposed by the facilities for this schedule.

        Args:
            model: The model to apply the actor to
            facilities: The facilities object to use for the actor
        """
        self._actor_function(model, facilities)


class SchedulerComponent(object):
    """Base class for all scheduling components.
    
    This class provides the foundation for different scheduling components
    that can be combined to create a complete scheduling solution.
    """
    def __init__(self):
        self._constraints = []
        self._optimizers = []
        self._post_processors = []
        self._validators = []

    def add_constraint(self, constraint: ModelActor):
        """Add a constraint to the component."""
        self._constraints.append(constraint)

    def add_optimizer(self, optimizer: ModelActor):
        """Add an optimizer to the component."""
        self._optimizers.append(optimizer)

    def add_post_processor(self, post_processor: ModelActor):
        """Add a post-processor to the component."""
        self._post_processors.append(post_processor)

    def add_validator(self, validator: ModelActor):
        """Add a validator to the component."""
        self._validators.append(validator)

    def __add__(self, other):
        """Combine two SchedulerComponents into a new one.
        
        Args:
            other: Another SchedulerComponent to combine with
            
        Returns:
            A new SchedulerComponent containing the combined elements
        """
        if not isinstance(other, SchedulerComponent):
            raise TypeError("Can only combine SchedulerComponent with another SchedulerComponent")
        
        combined = SchedulerComponent()
        combined._constraints = self._constraints + other._constraints
        combined._optimizers = self._optimizers + other._optimizers
        combined._post_processors = self._post_processors + other._post_processors
        combined._validators = self._validators + other._validators
        return combined

    def __iadd__(self, other):
        """In-place addition of another SchedulerComponent.
        
        Args:
            other: Another SchedulerComponent to combine with
            
        Returns:
            self with the other component's elements added
        """
        if not isinstance(other, SchedulerComponent):
            raise TypeError("Can only combine SchedulerComponent with another SchedulerComponent")
        
        self._constraints.extend(other._constraints)
        self._optimizers.extend(other._optimizers)
        self._post_processors.extend(other._post_processors)
        self._validators.extend(other._validators)
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

