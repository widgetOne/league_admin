from typing import List, Dict, Set, Any, Iterable
from ortools.sat.python import cp_model
from .facilities.facility import Facilities, GameSlot
from .schedule_component import SchedulerComponent

class SchedulerSolver(SchedulerComponent):
    """A solver for scheduling games using constraint programming."""
    
    def __init__(self, facilities: Facilities, constraints: Iterable[SchedulerComponent] = None, model=None):
        """Initialize the solver with facility constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            constraints: Optional iterable of SchedulerComponents to apply
            model: Optional OR-Tools model. If None, creates a new CpModel.
        """
        super().__init__()
        self.facilities = facilities
        self.model = model if model is not None else cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # Apply facility constraints to the model
        self._apply_facilities_to_model()
        
        if constraints:
            self.add_constraints(constraints)
    
    def _apply_facilities_to_model(self):
        """Apply facility-level constraints to the model.
        
        This includes:
        - Setting up games_per_season as a constant in the model
        """
        # Add games_per_season as a constant to the model
        self.model.NewIntVar(
            self.facilities.games_per_season,  # Lower bound
            self.facilities.games_per_season,  # Upper bound
            'games_per_season'  # Variable name
        )


        
    def solve(self):
        """Solve the scheduling problem."""
        for constraint in self._constraints:
            constraint(self.model, self.facilities)
        for optimizer in self._optimizers:
            optimizer(self.model, self.facilities)
        status = self.solver.Solve(self.model)
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print('Solution found!')
        else:
            print('No solution found.')
            
    def __str__(self) -> str:
        """Return a string representation of the solution."""
        return f"SchedulerSolver with {len(self._constraints)} constraints"

class ReffedSchedulerSolver(SchedulerSolver):
    """A solver for scheduling games that includes referee assignments."""
    
    def __init__(self, facilities: Facilities, constraints: Iterable[SchedulerComponent] = None, model=None):
        """Initialize the solver with facility and referee constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            constraints: Optional iterable of SchedulerComponents to apply
            model: Optional OR-Tools model. If None, creates a new CpModel.
        """
        super().__init__(facilities, constraints, model)
        self.ref_teams = []
        
    def __str__(self) -> str:
        """Return a string representation of the solution."""
        return f"ReffedSchedulerSolver with {len(self._constraints)} constraints and {len(self.ref_teams)} ref teams"
