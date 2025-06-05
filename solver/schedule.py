from typing import List, Dict, Set, Any, Iterable, Tuple, Optional
import datetime
import pandas as pd
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
        self.solver = cp_model.CpSolver()
        
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
        self._game_report: Optional[pd.DataFrame] = None

        # Apply facility constraints to the model
        self._apply_facilities_to_model()

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
    
    def get_game_report(self):
        """Get a DataFrame report of the solved schedule using singleton pattern.
        
        Returns:
            pd.DataFrame: Schedule report with columns for weekend_idx, date, location, 
                         time, team1 (home), team2 (away), ref, time_idx
                         
        Raises:
            RuntimeError: If called before solving or if no solution was found
        """
        # Return cached report if it exists
        if self._game_report is not None:
            return self._game_report
            
        # Check if we have a valid solution
        if not hasattr(self, '_last_solve_status'):
            raise RuntimeError("Must call solve() before generating game report")
            
        if self._last_solve_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError(f"Cannot generate report - solver status: {self.solver.StatusName(self._last_solve_status)}")
        
        # Generate the report
        schedule_rows = []
        
        for match in self.matches:
            home_idx = self.solver.Value(self.home_team[match])
            away_idx = self.solver.Value(self.away_team[match])
            ref_idx = self.solver.Value(self.ref[match])
            
            schedule_rows.append({
                "weekend_idx": match.weekend_idx,
                "date": match.date,
                "location": match.location,
                "time": match.time,
                "team1": home_idx,  # home team
                "team2": away_idx,  # away team
                "ref": ref_idx,     # ref team
                "time_idx": match.time_idx,
            })
        
        # Create DataFrame and sort
        self._game_report = pd.DataFrame(schedule_rows)
        self._game_report.sort_values(["weekend_idx", "date", "location", "time"], inplace=True)
        self._game_report.reset_index(drop=True, inplace=True)
        
        return self._game_report
    
    def get_team_report(self):
        """Generate a team-level report from the game schedule.
        
        Returns:
            pd.DataFrame: Team report indexed by team_idx with columns:
                         - total_play: total games played
                         - total_ref: total games refereed  
                         - vs_0, vs_1, ..., vs_N: games played against each team
        """
        # Get the game report first
        game_report = self.get_game_report()
        
        # Initialize team report DataFrame
        team_indices = list(range(self.total_teams))
        team_report = pd.DataFrame(index=team_indices)
        
        # Count total play (team1 + team2 appearances)
        play_counts = pd.Series(0, index=team_indices, name='total_play')
        for _, row in game_report.iterrows():
            play_counts[row['team1']] += 1
            play_counts[row['team2']] += 1
        team_report['total_play'] = play_counts
        
        # Count total ref
        ref_counts = game_report['ref'].value_counts().reindex(team_indices, fill_value=0)
        team_report['total_ref'] = ref_counts
        
        # Count vs play (games against each other team)
        for opponent_idx in team_indices:
            vs_count = pd.Series(0, index=team_indices, name=f'vs_{opponent_idx}')
            
            for _, row in game_report.iterrows():
                team1, team2 = row['team1'], row['team2']
                
                # Count matchups where team1 plays against opponent_idx
                if team2 == opponent_idx:
                    vs_count[team1] += 1
                    
                # Count matchups where team2 plays against opponent_idx  
                if team1 == opponent_idx:
                    vs_count[team2] += 1
                    
            team_report[f'vs_{opponent_idx}'] = vs_count
        
        return team_report
    
    def solve(self):
        """Solve the scheduling problem."""
        start = datetime.datetime.now()
        print(f"Starting solution process at {start}")
        
        status = self.solver.Solve(self.model)
        
        end = datetime.datetime.now()
        delta = end - start
        print(f"Solver status: {self.solver.StatusName(status)}")
        print(f"Finished at {end}, duration: {delta}")
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print('Solution found!')
        else:
            print('No solution found. Status:', status)
            if status == cp_model.INFEASIBLE:
                print("Model is infeasible.")
            elif status == cp_model.MODEL_INVALID:
                print("Model is invalid. Check constraints and variable definitions.")

        # Store the solve status for later reference
        self._last_solve_status = status

    def __str__(self) -> str:
        """Return a string representation of the solution."""
        return f"Schedule with {len(self.matches)} matches for {self.total_teams} teams"

class ReffedSchedule(Schedule):
    """A solver for scheduling games that includes referee assignments."""
    
    def __init__(self, facilities: Facilities, model: Optional[cp_model.CpModel] = None):
        """Initialize the solver with facility and referee constraints.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            model: Optional OR-Tools model. If None, creates a new CpModel.
        """
        super().__init__(facilities, model)
        
