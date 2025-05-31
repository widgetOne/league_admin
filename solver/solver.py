from typing import List, Dict, Set, Any, Iterable
from ortools.sat.python import cp_model
from .facilities.facility import Facilities, GameSlot
from .schedule_component.component import ScheduleComponent

class SchedulerSolver:
    """A solver for scheduling games using constraint programming."""
    
    def __init__(self, facilities: Facilities, constraints: Iterable[ScheduleComponent] = None, model=None):
        """Initialize the solver with facility constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            constraints: Optional iterable of ScheduleComponents to apply
            model: Optional OR-Tools model. If None, creates a new CpModel.
        """
        self.facilities = facilities
        self.model = model if model is not None else cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.constraints = []
        
        if constraints:
            self.add_constraints(constraints)
        
    def add_constraints(self, constraints: Iterable[ScheduleComponent]):
        """Add multiple constraints to the solver.
        
        Args:
            constraints: Iterable of ScheduleComponents to add
        """
        for constraint in constraints:
            self.add_constraint(constraint)
        
    def add_constraint(self, constraint: ScheduleComponent):
        """Add a constraint to the solver.
        
        Args:
            constraint: The ScheduleComponent to add
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
    
    def __init__(self, facilities: Facilities, constraints: Iterable[ScheduleComponent] = None, model=None):
        """Initialize the solver with facility and referee constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            constraints: Optional iterable of ScheduleComponents to apply
            model: Optional OR-Tools model. If None, creates a new CpModel.
        """
        super().__init__(facilities, constraints, model)
        self.ref_teams = []
        
    def __str__(self) -> str:
        """Return a string representation of the solution."""
        return f"ReffedSchedulerSolver with {len(self.constraints)} constraints and {len(self.ref_teams)} ref teams"
