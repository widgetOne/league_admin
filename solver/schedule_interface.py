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

    @abstractmethod
    def _apply_facilities_to_model(self):
        pass 