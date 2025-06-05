from typing import List, Dict, Set, Any, Iterable, Tuple, Optional
from ortools.sat.python import cp_model
from .facilities.facility import Facilities, Match
from .schedule_component import ModelActor

class Schedule:
    """A solver for scheduling games using constraint programming."""
    
    def __init__(self, facilities: Facilities, model: Optional[cp_model.CpModel]):
        """Initialize the solver with facility constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            model: Optional OR-Tools model. If None, creates a new CpModel.
        """
        self.facilities = facilities
        self.model = model
        
        # Initialize dictionaries for OR-Tools variables
        self.home_team: Dict[Any, Any] = {}
        self.away_team: Dict[Any, Any] = {}
        self.ref: Dict[Any, Any] = {}
        self.match_div: Dict[Any, Any] = {}
        self.match_loc: Dict[Any, Any] = {}
        self.home_div: Dict[Any, Any] = {}
        self.ref_div: Dict[Any, Any] = {}

        self.is_home: Dict[Tuple[Any, int], Any] = {}
        self.is_away: Dict[Tuple[Any, int], Any] = {}
        self.is_ref: Dict[Tuple[Any, int], Any] = {}
        self.is_playing: Dict[Tuple[Any, int], Any] = {}

        self.busy_count: Dict[Tuple[int, int, int], Any] = {}
        self.is_busy: Dict[Tuple[int, int, int], Any] = {}
        self.reffing_at_time: Dict[Tuple[int, int, int], Any] = {}
        self.playing_at_time: Dict[Tuple[int, int, int], Any] = {}
        
        self._total_teams: int = 0

        # Apply facility constraints to the model
        self._apply_facilities_to_model()





    @property
    def total_teams(self) -> int:
        return self.facilities.total_teams

    @property
    def matches(self):
        return self.facilities.matches
    
    def _apply_facilities_to_model(self):
        """Apply facility-level constraints and define core model variables based on facilities.
        Translates logic from Colab notebook.
        """
        
        calculated_total_teams = sum(self.facilities.team_counts)
        if calculated_total_teams <= 0:
            raise ValueError("Scheduling requires at least one team. Please check team_counts in facilities.")
        self.total_teams = calculated_total_teams
        self.teams = list(range(self.total_teams))

        team_div_list = []
        for div_idx, div_count in enumerate(self.facilities.team_counts):
            if div_count > 0: # Only add divisions that have teams
                for _ in range(div_count):
                    team_div_list.append(div_idx)
        
        # This should not be an issue if calculated_total_teams > 0
        # and team_counts is structured correctly (i.e., sum of positive counts > 0)
        if not team_div_list:
             raise ValueError("team_div_list is empty despite total_teams > 0. Check team_counts structure.")

        all_matches = self.facilities.matches
        if not all_matches:
            # It might be valid to have no matches defined yet if they are determined by the solver
            # or if this is an initial setup. For now, we'll allow it and loops will just not run.
            # If matches are essential for model setup beyond variable creation, add a check here.
            print("Warning: No matches found in facilities. Model variables related to matches will not be created.")
            return # Exit early if no matches, as loops below depend on them

        for m_obj in all_matches:
            m = m_obj
            name_suffix = f"{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}"

            self.home_team[m] = self.model.NewIntVar(0, self.total_teams - 1, f"home_team_{name_suffix}")
            self.away_team[m] = self.model.NewIntVar(0, self.total_teams - 1, f"away_team_{name_suffix}")
            self.ref[m] = self.model.NewIntVar(0, self.total_teams - 1, f"ref_team_{name_suffix}")
            
            # len(self.facilities.team_counts) should be > 0 if total_teams > 0
            # and team_counts is not empty. Assume team_counts is a non-empty list.
            num_divisions = len(self.facilities.team_counts)
            self.match_div[m] = self.model.NewIntVar(0, num_divisions - 1, f"division_of_{name_suffix}")
            self.match_loc[m] = self.model.NewConstant(m_obj.location)

            self.home_div[m] = self.model.NewIntVar(0, num_divisions - 1, f"home_div_{name_suffix}")
            self.ref_div[m] = self.model.NewIntVar(0, num_divisions - 1, f"ref_div_{name_suffix}")

            self.model.AddElement(self.home_team[m], team_div_list, self.home_div[m])
            self.model.AddElement(self.ref[m], team_div_list, self.ref_div[m])
            
            self.model.Add(self.home_team[m] != self.away_team[m])
            self.model.Add(self.home_team[m] != self.ref[m])
            self.model.Add(self.away_team[m] != self.ref[m])

        for m_obj in all_matches:
            m = m_obj
            name_suffix = f"{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}"
            for t_idx in range(self.total_teams):
                self.is_home[m, t_idx] = self.model.NewBoolVar(f"is_home_{name_suffix}_{t_idx}")
                self.model.Add(self.home_team[m] == t_idx).OnlyEnforceIf(self.is_home[m, t_idx])
                self.model.Add(self.home_team[m] != t_idx).OnlyEnforceIf(self.is_home[m, t_idx].Not())

                self.is_away[m, t_idx] = self.model.NewBoolVar(f"is_away_{name_suffix}_{t_idx}")
                self.model.Add(self.away_team[m] == t_idx).OnlyEnforceIf(self.is_away[m, t_idx])
                self.model.Add(self.away_team[m] != t_idx).OnlyEnforceIf(self.is_away[m, t_idx].Not())

                self.is_ref[m, t_idx] = self.model.NewBoolVar(f"is_ref_{name_suffix}_{t_idx}")
                self.model.Add(self.ref[m] == t_idx).OnlyEnforceIf(self.is_ref[m, t_idx])
                self.model.Add(self.ref[m] != t_idx).OnlyEnforceIf(self.is_ref[m, t_idx].Not())

                self.is_playing[m, t_idx] = self.model.NewBoolVar(f"is_playing_{name_suffix}_{t_idx}")
                self.model.AddBoolOr([self.is_home[m, t_idx], self.is_away[m, t_idx]]).OnlyEnforceIf(self.is_playing[m, t_idx])
                self.model.AddBoolAnd([self.is_home[m, t_idx].Not(), self.is_away[m, t_idx].Not()]).OnlyEnforceIf(self.is_playing[m, t_idx].Not())

        weekend_idxs = sorted(list(set(m.weekend_idx for m in all_matches)))
        time_indices = sorted(list(set(m.time_idx for m in all_matches)))
        num_locations = len(self.facilities.locations) if self.facilities.locations else 0
        # If num_locations could be 0, max_busy_val needs to handle it. Smallest positive if 0.
        max_busy_val = num_locations * 3 if num_locations > 0 else 3 

        for w_idx in weekend_idxs:
            for ti_idx in time_indices:
                for t_idx in range(self.total_teams):
                    key = (w_idx, ti_idx, t_idx)
                    playing_vars_at_time = [self.is_playing[m_obj, t_idx] for m_obj in all_matches if m_obj.weekend_idx == w_idx and m_obj.time_idx == ti_idx]
                    reffing_vars_at_time = [self.is_ref[m_obj, t_idx] for m_obj in all_matches if m_obj.weekend_idx == w_idx and m_obj.time_idx == ti_idx]

                    self.busy_count[key] = self.model.NewIntVar(0, max_busy_val, f"busy_count_{w_idx}_{ti_idx}_{t_idx}")
                    self.model.Add(self.busy_count[key] == sum(playing_vars_at_time) + sum(reffing_vars_at_time))
                    
                    self.reffing_at_time[key] = self.model.NewBoolVar(f"reffing_at_{w_idx}_{ti_idx}_{t_idx}")
                    if reffing_vars_at_time:
                        self.model.AddBoolOr(reffing_vars_at_time).OnlyEnforceIf(self.reffing_at_time[key])
                        self.model.AddBoolAnd([r.Not() for r in reffing_vars_at_time]).OnlyEnforceIf(self.reffing_at_time[key].Not())
                    else:
                        self.model.Add(self.reffing_at_time[key] == 0)

                    self.playing_at_time[key] = self.model.NewBoolVar(f"playing_at_{w_idx}_{ti_idx}_{t_idx}")
                    if playing_vars_at_time:
                        self.model.AddBoolOr(playing_vars_at_time).OnlyEnforceIf(self.playing_at_time[key])
                        self.model.AddBoolAnd([p.Not() for p in playing_vars_at_time]).OnlyEnforceIf(self.playing_at_time[key].Not())
                    else:
                        self.model.Add(self.playing_at_time[key] == 0)

                    self.is_busy[key] = self.model.NewBoolVar(f"is_busy_{w_idx}_{ti_idx}_{t_idx}")
                    self.model.Add(self.busy_count[key] >= 1).OnlyEnforceIf(self.is_busy[key])
                    self.model.Add(self.busy_count[key] == 0).OnlyEnforceIf(self.is_busy[key].Not())
        
    def solve(self):
        """Solve the scheduling problem."""

        status = self.model.Solve(self.model)
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print('Solution found!')
        else:
            print('No solution found. Status:', status)
            if status == cp_model.INFEASIBLE:
                print("Model is infeasible.")
            elif status == cp_model.MODEL_INVALID:
                print("Model is invalid. Check constraints and variable definitions.")
            
    def __str__(self) -> str:
        """Return a string representation of the solution."""
        return f"Schedule with {len(self._constraints)} constraints"

class ReffedSchedule(Schedule):
    """A solver for scheduling games that includes referee assignments."""
    
    def __init__(self, facilities: Facilities, model: Optional[cp_model.CpModel] = None):
        """Initialize the solver with facility and referee constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            model: Optional OR-Tools model. If None, creates a new CpModel.
        """
        super().__init__(facilities, model)
        
