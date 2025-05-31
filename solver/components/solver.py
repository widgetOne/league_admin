from ..schedule_component import SchedulerComponent
from ortools.sat.python import cp_model
from typing import List, Dict, Set, Any
from ..facilities.facility import Facilities, GameSlot

class SchedulerSolver:
    """A solver for scheduling games using constraint programming."""
    
    def __init__(self, facilities: Facilities, model=None):
        """Initialize the solver with facility constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
        """
        self.facilities = facilities
        self.model = model if model is not None else cp_model.CpModel()
        self.constraints = []
        
    def add_constraint(self, constraint: Any):
        """Add a constraint to the solver.
        
        Args:
            constraint: The constraint to add
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
    
    def __init__(self, facilities: Facilities, model=None):
        """Initialize the solver with facility and referee constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            ref_teams: List of teams that can provide referees
        """
        super().__init__(facilities, model)
        self.ref_teams = ref_teams
        
    def __str__(self) -> str:
        """Return a string representation of the solution."""
        return f"ReffedSchedulerSolver with {len(self.constraints)} constraints and {len(self.ref_teams)} ref teams"
