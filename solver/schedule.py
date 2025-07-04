from typing import List, Dict, Set, Any, Iterable, Tuple, Optional
import datetime
import time
import pandas as pd
from ortools.sat.python import cp_model
from .facilities.facility import Facilities, Match
from .schedule_component import ModelActor


class SolutionStatusCallback(cp_model.CpSolverSolutionCallback):
    """A callback to print solver status at regular intervals."""

    def __init__(self, schedule: 'Schedule', interval: float = 10.0):
        """
        Initializes the callback.

        Args:
            schedule: The schedule object being solved.
            interval: The interval in seconds at which to print status updates.
        """
        super().__init__()
        self._schedule = schedule
        self._interval = interval
        self._start_time = time.time()
        self._last_print_time = time.time()
        self._solution_count = 0

    def on_solution_callback(self):
        """Called by the solver when a new solution is found."""
        current_time = time.time()
        self._solution_count += 1
        first_schedule_found = self._solution_count == 1
        if current_time - self._last_print_time >= self._interval or first_schedule_found:
            elapsed_time = current_time - self._start_time
            objective_value = self.ObjectiveValue()

            if self._solution_count == 1:
                print(f"[{elapsed_time:6.2f}s] First valid schedule found! Objective: {objective_value:,.2f}")
            else:
                print(f"[{elapsed_time:6.2f}s] Improved schedule found ({self._solution_count}). Objective: {objective_value:,.2f}")

            self._last_print_time = current_time


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
        self.is_busy: Dict[Tuple[Any, int], Any] = {}

        self.busy_count_at_time: Dict[Tuple[int, int, int], Any] = {}
        self.busy_at_time: Dict[Tuple[int, int, int], Any] = {}
        self.reffing_at_time: Dict[Tuple[int, int, int], Any] = {}
        self.playing_at_time: Dict[Tuple[int, int, int], Any] = {}
        self.playing_around_time: Dict[Tuple[int, int, int], Any] = {}
        self.games_per_weekend: Dict[Tuple[int, int], Any] = {}  # (weekend_idx, team_idx) -> games
        self.busy_count_per_weekend: Dict[Tuple[int, int], Any] = {} # (weekend_idx, team_idx) -> games
        
        self._total_teams: int = 0
        self._game_report: Optional[pd.DataFrame] = None
        self._debug_report: Optional[str] = None

        # Apply facility constraints to the model
        self._apply_facilities_to_model()

    def set_debug_report(self, report: str):
        """Store the debug report string on the schedule object."""
        self._debug_report = report

    def get_debug_report(self) -> Optional[str]:
        """Retrieve the stored debug report."""
        return self._debug_report

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
        self.team_div = []
        for div_idx, div_count in enumerate(self.facilities.team_counts):
            if div_count > 0: # Only add divisions that have teams
                for _ in range(div_count):
                    self.team_div.append(div_idx)
        
        # This should not be an issue if calculated_total_teams > 0
        # and team_counts is structured correctly (i.e., sum of positive counts > 0)
        if not self.team_div:
             raise ValueError("team_div is empty despite total_teams > 0. Check team_counts structure.")

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

            self.model.AddElement(self.home_team[m], self.team_div, self.home_div[m])
            self.model.AddElement(self.ref[m], self.team_div, self.ref_div[m])
            
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

                self.is_busy[m, t_idx] = self.model.NewBoolVar(f"is_busy_{name_suffix}_{t_idx}")
                self.model.AddBoolOr([self.is_playing[m, t_idx], self.is_ref[m, t_idx]]).OnlyEnforceIf(self.is_busy[m, t_idx])
                self.model.AddBoolAnd([self.is_playing[m, t_idx].Not(), self.is_ref[m, t_idx].Not()]).OnlyEnforceIf(self.is_busy[m, t_idx].Not())

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

                    self.busy_count_at_time[key] = self.model.NewIntVar(0, max_busy_val, f"busy_count_at_time_{w_idx}_{ti_idx}_{t_idx}")
                    self.model.Add(self.busy_count_at_time[key] == sum(playing_vars_at_time) + sum(reffing_vars_at_time))
                    
                    self.reffing_at_time[key] = self.model.NewBoolVar(f"reffing_at_{w_idx}_{ti_idx}_{t_idx}")
                    self.model.AddBoolOr(reffing_vars_at_time).OnlyEnforceIf(self.reffing_at_time[key])
                    self.model.AddBoolAnd([r.Not() for r in reffing_vars_at_time]).OnlyEnforceIf(self.reffing_at_time[key].Not())

                    self.playing_at_time[key] = self.model.NewBoolVar(f"playing_at_{w_idx}_{ti_idx}_{t_idx}")
                    self.model.AddBoolOr(playing_vars_at_time).OnlyEnforceIf(self.playing_at_time[key])
                    self.model.AddBoolAnd([p.Not() for p in playing_vars_at_time]).OnlyEnforceIf(self.playing_at_time[key].Not())

                    self.busy_at_time[key] = self.model.NewBoolVar(f"busy_at_time_{w_idx}_{ti_idx}_{t_idx}")
                    self.model.Add(self.busy_count_at_time[key] >= 1).OnlyEnforceIf(self.busy_at_time[key])
                    self.model.Add(self.busy_count_at_time[key] == 0).OnlyEnforceIf(self.busy_at_time[key].Not())

        # Add playing_around_time variables for adjacent time reffing constraints
        # This must be done in a separate loop after playing_at_time is created
        for w_idx in weekend_idxs:
            for ti_idx in time_indices:
                other_times = [other_time for other_time in time_indices if abs(other_time - ti_idx) == 1]
                for t_idx in range(self.total_teams):
                    key = (w_idx, ti_idx, t_idx)
                    self.playing_around_time[key] = self.model.NewBoolVar(f"is_playing_in_adjacent_time_{w_idx}_{ti_idx}_{t_idx}")
                    
                    if other_times:
                        other_time_keys = [(w_idx, other_time, t_idx) for other_time in other_times]
                        other_playing_vars = [self.playing_at_time[other_key] for other_key in other_time_keys]
                        
                        self.model.AddBoolOr(other_playing_vars).OnlyEnforceIf(self.playing_around_time[key])
                        self.model.AddBoolAnd([p.Not() for p in other_playing_vars]).OnlyEnforceIf(self.playing_around_time[key].Not())
                    else:
                        # No adjacent times, so always false
                        self.model.Add(self.playing_around_time[key] == 0)

        
        # Add games_per_weekend variables
        weekend_idxs = sorted(list(set(m.weekend_idx for m in all_matches)))
        self.games_per_weekend = {}
        self.busy_count_per_weekend = {}
        for w_idx in weekend_idxs:
            for t_idx in range(self.total_teams):
                key = (w_idx, t_idx)
                # Count all games this team plays this weekend
                weekend_playing_vars = [self.is_playing[m_obj, t_idx] for m_obj in all_matches if m_obj.weekend_idx == w_idx]
                self.games_per_weekend[key] = self.model.NewIntVar(0, len(weekend_playing_vars), f"games_per_weekend_{w_idx}_{t_idx}")
                self.model.Add(self.games_per_weekend[key] == sum(weekend_playing_vars))
                
                # Count all busy times this team has this weekend
                weekend_busy_vars = [self.is_busy[m_obj, t_idx] for m_obj in all_matches if m_obj.weekend_idx == w_idx]
                self.busy_count_per_weekend[key] = self.model.NewIntVar(0, len(weekend_busy_vars), f"busy_count_per_weekend_{w_idx}_{t_idx}")
                self.model.Add(self.busy_count_per_weekend[key] == sum(weekend_busy_vars))

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
            # Check if this match has been reassigned by post-processors
            if hasattr(self, '_team_reassignments') and match in self._team_reassignments:
                reassignment = self._team_reassignments[match]
                home_idx = reassignment['home_team']
                away_idx = reassignment['away_team']
                ref_idx = reassignment['ref']
            else:
                # Use original solver values
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
        """Solve the scheduling problem with optimized solver parameters."""
        start = datetime.datetime.now()
        print(f"Starting solution process at {start}")

        # Set solver parameters optimized for performance
        self.solver.parameters.max_time_in_seconds = 240.0
        self.solver.parameters.num_search_workers = 8  # Use multicore
        self.solver.parameters.linearization_level = 0  # Disable linearization for speed
        self.solver.parameters.cp_model_presolve = True  # Enable presolve optimizations
        #self.solver.parameters.enumerate_all_solutions = True
        
        solution_callback = SolutionStatusCallback(self, interval=10.0)
        status = self.solver.Solve(self.model, solution_callback)
        
        end = datetime.datetime.now()
        delta = end - start
        print(f"Solver status: {self.solver.StatusName(status)}")
        print(f"Finished at {end}, duration: {delta}")

        if status == cp_model.OPTIMAL:
            print('Optimal solution found!')
        elif status == cp_model.FEASIBLE:
            print('Feasible solution found (time limit reached)!')
        else:
            print('No solution found. Status:', status)
            if status == cp_model.INFEASIBLE:
                print("Model is infeasible.")
            elif status == cp_model.MODEL_INVALID:
                print("Model is invalid. Check constraints and variable definitions.")


        # Store the solve status for later reference
        self._last_solve_status = status

    def get_volleyball_debug_schedule(self):
        """Get a human-readable volleyball schedule string for debugging.
        
        Returns:
            str: Formatted schedule string
        
        Format:
        week_idx: 1
        date: 2025-06-22
        time 12:00
        01 v 14 r 03 - 11 v 22 r 12 - 02 v ...
        time 13:00
        03 v 04 r 05 - ...
        """
        # Get the game report
        game_report = self.get_game_report()
        
        lines = []
        
        # Group by weekend_idx and date first
        for weekend_idx in sorted(game_report['weekend_idx'].unique()):
            week_games = game_report[game_report['weekend_idx'] == weekend_idx]
            
            lines.append(f"\nweek_idx: {weekend_idx}")
            
            for date in sorted(week_games['date'].unique()):
                date_games = week_games[week_games['date'] == date]
                lines.append(f"date: {date}")
                
                # Group by time and format games
                for time in sorted(date_games['time'].unique()):
                    time_games = date_games[date_games['time'] == time]
                    
                    # Format each game as "team1 v team2 r ref"
                    game_strings = []
                    for _, game in time_games.iterrows():
                        team1 = f"{game['team1']:02d}"  # Zero-pad to 2 digits
                        team2 = f"{game['team2']:02d}"
                        ref = f"{game['ref']:02d}"
                        game_strings.append(f"{team1} v {team2} r {ref}")
                    
                    # Join games at same time with " - "
                    games_line = " - ".join(game_strings)
                    lines.append(f"time {time}")
                    lines.append(games_line)
        
        return "\n".join(lines)

    @staticmethod
    def parse_canned_schedule(file_path: str):
        """Parse a canned schedule file and return a Schedule-like object with dataframes.
        
        Args:
            file_path: Path to the schedule file in the format:
                      week_idx: 1
                      date: 6/22/2025
                      time 12:00:00
                      26 v 29 r 23
                      time 13:00:00
                      08 v 01 r 03 - 18 v 13 r 16 - ...
        
        Returns:
            object: An object with game_report and team_report DataFrames
        """
        import re
        from datetime import datetime
        
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse the content
        schedule_rows = []
        current_week_idx = None
        current_date = None
        current_time = None
        
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('=') or line == 'VOLLEYBALL SCHEDULE DEBUG OUTPUT':
                continue
                
            # Parse week_idx
            if line.startswith('week_idx:'):
                current_week_idx = int(line.split(':')[1].strip())
                continue
                
            # Parse date
            if line.startswith('date:'):
                date_str = line.split(':', 1)[1].strip()
                current_date = date_str
                continue
                
            # Parse time
            if line.startswith('time '):
                time_str = line.split(' ', 1)[1].strip()
                # Convert time format (e.g., "12:00:00" -> "12:00:00")
                current_time = time_str
                continue
                
            # Parse games (format: "26 v 29 r 23" or "08 v 01 r 03 - 18 v 13 r 16 - ...")
            if ' v ' in line and ' r ' in line:
                # Split by " - " to get individual games
                games = line.split(' - ')
                
                for i, game in enumerate(games):
                    game = game.strip()
                    # Parse game format: "team1 v team2 r ref"
                    match = re.match(r'(\d+)\s+v\s+(\d+)\s+r\s+(\d+)', game)
                    if match:
                        team1 = int(match.group(1))
                        team2 = int(match.group(2))
                        ref = int(match.group(3))
                        
                        # Create time_idx based on time
                        time_mapping = {
                            "12:00:00": 0,
                            "13:00:00": 1, 
                            "14:00:00": 2,
                            "15:00:00": 3,
                            "16:00:00": 4
                        }
                        time_idx = time_mapping.get(current_time, 0)
                        
                        schedule_rows.append({
                            "weekend_idx": current_week_idx,
                            "date": current_date,
                            "location": "Highland Park",  # Default location
                            "time": current_time,
                            "team1": team1,  # home team
                            "team2": team2,  # away team
                            "ref": ref,      # ref team
                            "time_idx": time_idx,
                        })
        
        # Create game report DataFrame
        game_report = pd.DataFrame(schedule_rows)
        game_report.sort_values(["weekend_idx", "date", "time"], inplace=True)
        game_report.reset_index(drop=True, inplace=True)
        
        # Generate team report
        if not schedule_rows:
            team_report = pd.DataFrame()
        else:
            # Find max team index to determine total teams
            all_teams = set()
            for row in schedule_rows:
                all_teams.add(row['team1'])
                all_teams.add(row['team2'])
                all_teams.add(row['ref'])
            
            team_indices = sorted(list(all_teams))
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
        
        # Create a simple object to hold the dataframes
        class ParsedSchedule:
            def __init__(self, game_report, team_report):
                self.game_report = game_report
                self.team_report = team_report
                
            def get_game_report(self):
                return self.game_report
                
            def get_team_report(self):
                return self.team_report
        
        return ParsedSchedule(game_report, team_report)

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
        
