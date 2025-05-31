from typing import List, Dict, Set, Any, Iterable
from ortools.sat.python import cp_model
from .facilities.facility import Facilities, GameSlot
from .schedule_component import SchedulerComponent

class SchedulerSolver:
    """A solver for scheduling games using constraint programming."""
    
    def __init__(self, facilities: Facilities, constraints: Iterable[SchedulerComponent] = None, model=None):
        """Initialize the solver with facility constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            constraints: Optional iterable of SchedulerComponents to apply
            model: Optional OR-Tools model. If None, creates a new CpModel.
        """
        self.facilities = facilities
        self.model = model if model is not None else cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.constraints = []
        
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
        
    def add_constraints(self, constraints: Iterable[SchedulerComponent]):
        """Add multiple constraints to the solver.
        
        Args:
            constraints: Iterable of SchedulerComponents to add
        """
        for constraint in constraints:
            self.add_constraint(constraint)
        
    def add_constraint(self, constraint: SchedulerComponent):
        """Add a constraint to the solver.
        
        Args:
            constraint: The SchedulerComponent to add
        """
        self.constraints.append(constraint)
        constraint.apply(self.model, self.facilities)
        
    def solve(self):
        """Solve the scheduling problem."""
        status = self.solver.Solve(self.model)
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print('Solution found!')
        else:
            print('No solution found.')
            
    def __str__(self) -> str:
        """Return a string representation of the solution."""
        return f"SchedulerSolver with {len(self.constraints)} constraints"

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
        return f"ReffedSchedulerSolver with {len(self.constraints)} constraints and {len(self.ref_teams)} ref teams"
