from typing import List, Dict, Set, Any, Iterable
from ortools.sat.python import cp_model
from .facilities.facility import Facilities, Match
from .schedule_component import SchedulerComponent

class SchedulerSolver(SchedulerComponent):
    """A solver for scheduling games using constraint programming."""
    
    def __init__(self, facilities: Facilities, components: Iterable[SchedulerComponent] = [], model=None):
        """Initialize the solver with facility constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            components: Optional iterable of SchedulerComponents to apply
            model: Optional OR-Tools model. If None, creates a new CpModel.
        """
        super().__init__()
        self.facilities = facilities
        self.model = model if model is not None else cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # Initialize dictionaries for OR-Tools variables
        self.home_team = {}
        self.away_team = {}
        self.ref = {}
        self.match_div = {}
        self.match_loc = {}
        self.home_div = {}
        self.ref_div = {}

        self.is_home = {}
        self.is_away = {}
        self.is_ref = {}
        self.is_playing = {}

        self.busy_count = {}
        self.is_busy = {}
        self.reffing_at_time = {}
        self.playing_at_time = {}
        
        # Apply facility constraints to the model
        self._apply_facilities_to_model()
        
        for component in components:
            self += component
    
    @property
    def matches(self):
        return self.facilities.matches
    
    def _apply_facilities_to_model(self):
        """Apply facility-level constraints and define core model variables based on facilities.
        Translates logic from Colab notebook.
        """
        
        total_teams = sum(self.facilities.team_counts)
        self.total_teams = total_teams # Store for potential use in components

        team_div_list = []
        for div_idx, div_count in enumerate(self.facilities.team_counts):
            for _ in range(div_count):
                team_div_list.append(div_idx)
        
        # Ensure team_div_list is not empty if total_teams > 0
        # OR-Tools AddElement requires the array to be non-empty.
        # If total_teams is 0, this list might be empty, but loops below won't run.
        # If team_counts is like [0,0], total_teams is 0.
        # If team_counts is [2,0], total_teams is 2, list is [0,0]
        # If team_counts is [0], total_teams is 0.
        # If there are teams, team_div_list must be populated.
        # If total_teams > 0 and not team_div_list:
        #    raise ValueError("team_div_list cannot be empty if there are teams.")
        # It seems team_div_list will always be populated correctly if total_teams > 0

        all_matches = self.facilities.matches
        
        for m_obj in all_matches:
            # Use a hashable key for the dictionaries, e.g., the Match object itself if it's hashable,
            # or a tuple of its identifying attributes. Since Match is a dataclass (implicitly hashable
            # if fields are hashable, and it is), we can use m_obj directly.
            m = m_obj # Using the object as key, assuming it's hashable

            self.home_team[m] = self.model.NewIntVar(0, total_teams - 1, f"home_team_{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}")
            self.away_team[m] = self.model.NewIntVar(0, total_teams - 1, f"away_team_{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}")
            self.ref[m] = self.model.NewIntVar(0, total_teams - 1, f"ref_team_{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}")
            self.match_div[m] = self.model.NewIntVar(0, len(self.facilities.team_counts) -1 if self.facilities.team_counts else 0, f"division_of_{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}") # div index
            self.match_loc[m] = self.model.NewConstant(m_obj.location) # location is an int index

            self.home_div[m] = self.model.NewIntVar(0, len(self.facilities.team_counts) - 1 if self.facilities.team_counts else 0, f"home_div_{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}")
            self.ref_div[m] = self.model.NewIntVar(0, len(self.facilities.team_counts) - 1 if self.facilities.team_counts else 0, f"ref_div_{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}")

            if total_teams > 0 and team_div_list: # AddElement requires a non-empty array
                self.model.AddElement(self.home_team[m], team_div_list, self.home_div[m])
                self.model.AddElement(self.ref[m], team_div_list, self.ref_div[m])
            elif total_teams > 0 and not team_div_list:
                 # This case should ideally not happen if team_counts is well-defined
                pass


            self.model.Add(self.home_team[m] != self.away_team[m])
            self.model.Add(self.home_team[m] != self.ref[m])
            self.model.Add(self.away_team[m] != self.ref[m])

        # Define layered booleans
        for m_obj in all_matches:
            m = m_obj
            for t_idx in range(total_teams):
                self.is_home[m, t_idx] = self.model.NewBoolVar(f"is_home_{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}_{t_idx}")
                self.model.Add(self.home_team[m] == t_idx).OnlyEnforceIf(self.is_home[m, t_idx])
                self.model.Add(self.home_team[m] != t_idx).OnlyEnforceIf(self.is_home[m, t_idx].Not())

                self.is_away[m, t_idx] = self.model.NewBoolVar(f"is_away_{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}_{t_idx}")
                self.model.Add(self.away_team[m] == t_idx).OnlyEnforceIf(self.is_away[m, t_idx])
                self.model.Add(self.away_team[m] != t_idx).OnlyEnforceIf(self.is_away[m, t_idx].Not())

                self.is_ref[m, t_idx] = self.model.NewBoolVar(f"is_ref_{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}_{t_idx}")
                self.model.Add(self.ref[m] == t_idx).OnlyEnforceIf(self.is_ref[m, t_idx])
                self.model.Add(self.ref[m] != t_idx).OnlyEnforceIf(self.is_ref[m, t_idx].Not())

                self.is_playing[m, t_idx] = self.model.NewBoolVar(f"is_playing_{m_obj.weekend_idx}_{m_obj.date}_{m_obj.location}_{m_obj.time_idx}_{t_idx}")
                self.model.AddBoolOr([self.is_home[m, t_idx], self.is_away[m, t_idx]]).OnlyEnforceIf(self.is_playing[m, t_idx])
                self.model.AddBoolAnd([self.is_home[m, t_idx].Not(), self.is_away[m, t_idx].Not()]).OnlyEnforceIf(self.is_playing[m, t_idx].Not())

        # Busyness variables
        weekend_idxs = sorted(list(set(m.weekend_idx for m in all_matches)))
        # max_time_idx from Colab likely means the number of distinct time slots available.
        # self.facilities.times should store unique time objects. Its length can be max_time_idx.
        # The Colab code uses `m[4]` which is `time_idx` of the Match object.
        time_indices = sorted(list(set(m.time_idx for m in all_matches)))


        # Assuming locations are 0-indexed integers as per Match.location
        num_locations = len(self.facilities.locations) if self.facilities.locations else 0


        for w_idx in weekend_idxs:
            for ti_idx in time_indices: # ti_idx is the actual time_idx from Match object
                for t_idx in range(total_teams):
                    key = (w_idx, ti_idx, t_idx) # Use tuple for multi-dimensional key

                    playing_vars_at_time = [self.is_playing[m_obj, t_idx] for m_obj in all_matches if m_obj.weekend_idx == w_idx and m_obj.time_idx == ti_idx]
                    reffing_vars_at_time = [self.is_ref[m_obj, t_idx] for m_obj in all_matches if m_obj.weekend_idx == w_idx and m_obj.time_idx == ti_idx]

                    self.busy_count[key] = self.model.NewIntVar(0, num_locations * 3 if num_locations else 3, f"busy_count_{w_idx}_{ti_idx}_{t_idx}") # Max busy is playing or reffing on all courts (simplified)
                    # Sum constraint: Ensure lists are not empty if summing, or handle sum([]) = 0
                    self.model.Add(self.busy_count[key] == sum(playing_vars_at_time) + sum(reffing_vars_at_time))
                    
                    self.reffing_at_time[key] = self.model.NewBoolVar(f"reffing_at_{w_idx}_{ti_idx}_{t_idx}")
                    if reffing_vars_at_time:
                        self.model.AddBoolOr(reffing_vars_at_time).OnlyEnforceIf(self.reffing_at_time[key])
                        self.model.AddBoolAnd([r.Not() for r in reffing_vars_at_time]).OnlyEnforceIf(self.reffing_at_time[key].Not())
                    else: # No matches to ref at this time for this team, so can't be reffing
                        self.model.Add(self.reffing_at_time[key] == 0)


                    self.playing_at_time[key] = self.model.NewBoolVar(f"playing_at_{w_idx}_{ti_idx}_{t_idx}")
                    if playing_vars_at_time:
                        self.model.AddBoolOr(playing_vars_at_time).OnlyEnforceIf(self.playing_at_time[key])
                        self.model.AddBoolAnd([p.Not() for p in playing_vars_at_time]).OnlyEnforceIf(self.playing_at_time[key].Not())
                    else: # No matches to play at this time for this team
                        self.model.Add(self.playing_at_time[key] == 0)

                    self.is_busy[key] = self.model.NewBoolVar(f"is_busy_{w_idx}_{ti_idx}_{t_idx}")
                    self.model.Add(self.busy_count[key] >= 1).OnlyEnforceIf(self.is_busy[key])
                    self.model.Add(self.busy_count[key] == 0).OnlyEnforceIf(self.is_busy[key].Not())
        
        # Example of how games_per_season could be used if it's a single value:
        # self.model.NewConstant(self.facilities.games_per_season) # If it needs to be a model constant for some reason
        # Or if it's a variable to be tracked/constrained:
        # self.games_per_season_var = self.model.NewIntVar(self.facilities.games_per_season, self.facilities.games_per_season, "games_per_season_const")


    def solve(self):
        """Solve the scheduling problem."""
        for constraint_applier in self._constraints: # Assuming these are functions or callable objects
            constraint_applier(self) # Pass self (which has model and vars)
        for optimizer_applier in self._optimizers:
            optimizer_applier(self)
        status = self.solver.Solve(self.model)
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print('Solution found!')
            # Potentially extract and store solution here
        else:
            print('No solution found.')
            
    def __str__(self) -> str:
        """Return a string representation of the solution."""
        return f"SchedulerSolver with {len(self._constraints)} constraints"

class ReffedSchedulerSolver(SchedulerSolver):
    """A solver for scheduling games that includes referee assignments."""
    
    def __init__(self, facilities: Facilities, components: Iterable[SchedulerComponent] = [], model=None):
        """Initialize the solver with facility and referee constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            components: Optional iterable of SchedulerComponents to apply
            model: Optional OR-Tools model. If None, creates a new CpModel.
        """
        super().__init__(facilities, components, model)
        # self.ref_teams = [] # This was in original, but ref variables are now created above.
                           # If this was meant for something else, it needs clarification.
        
    def __str__(self) -> str:
        """Return a string representation of the solution."""
        return f"ReffedSchedulerSolver with {len(self._constraints)} constraints"
