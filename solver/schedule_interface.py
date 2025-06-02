from abc import ABC, abstractmethod
from typing import Any, List, Dict, Tuple
from ortools.sat.python import cp_model
# Attempt to import Facilities for type hint, but use string literal if it causes issues
# from .facilities.facility import Facilities # This could create a cycle if Facilities needs ScheduleInterface

# Forward reference for Facilities if direct import is problematic
Facilities = 'Facilities'

class ScheduleInterface(ABC):
    """
    Interface defining the properties and model variables a scheduling instance must provide
    for components (ModelActors) to interact with.
    """

    @property
    @abstractmethod
    def facilities(self) -> Facilities: # Using forward reference
        pass

    @property
    @abstractmethod
    def model(self) -> cp_model.CpModel:
        pass

    @property
    @abstractmethod
    def total_teams(self) -> int:
        pass

    # Dictionaries for OR-Tools variables created in _apply_facilities_to_model
    # Using Any for the value type of these dictionaries as they hold OR-Tools variable types.
    # Keys are typically Match objects or tuples.

    @property
    @abstractmethod
    def home_team(self) -> Dict[Any, Any]:
        pass

    @property
    @abstractmethod
    def away_team(self) -> Dict[Any, Any]:
        pass

    @property
    @abstractmethod
    def ref(self) -> Dict[Any, Any]:
        pass

    @property
    @abstractmethod
    def match_div(self) -> Dict[Any, Any]:
        pass

    @property
    @abstractmethod
    def match_loc(self) -> Dict[Any, Any]:
        pass

    @property
    @abstractmethod
    def home_div(self) -> Dict[Any, Any]:
        pass

    @property
    @abstractmethod
    def ref_div(self) -> Dict[Any, Any]:
        pass

    @property
    @abstractmethod
    def is_home(self) -> Dict[Tuple[Any, int], Any]: # Key: (Match, team_idx)
        pass

    @property
    @abstractmethod
    def is_away(self) -> Dict[Tuple[Any, int], Any]: # Key: (Match, team_idx)
        pass

    @property
    @abstractmethod
    def is_ref(self) -> Dict[Tuple[Any, int], Any]: # Key: (Match, team_idx)
        pass

    @property
    @abstractmethod
    def is_playing(self) -> Dict[Tuple[Any, int], Any]: # Key: (Match, team_idx)
        pass

    @property
    @abstractmethod
    def busy_count(self) -> Dict[Tuple[int, int, int], Any]: # Key: (weekend_idx, time_idx, team_idx)
        pass

    @property
    @abstractmethod
    def is_busy(self) -> Dict[Tuple[int, int, int], Any]: # Key: (weekend_idx, time_idx, team_idx)
        pass

    @property
    @abstractmethod
    def reffing_at_time(self) -> Dict[Tuple[int, int, int], Any]: # Key: (weekend_idx, time_idx, team_idx)
        pass

    @property
    @abstractmethod
    def playing_at_time(self) -> Dict[Tuple[int, int, int], Any]: # Key: (weekend_idx, time_idx, team_idx)
        pass

    # Add other essential properties/methods that components might need to access from the Schedule object
    # For example, if components need access to all matches directly:
    # @property
    # @abstractmethod
    # def matches(self) -> List[Any]: # List of Match objects
    #     pass

    @abstractmethod
    def _apply_facilities_to_model(self):
        pass 