from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule
import pandas as pd


class TimeVarietyOptimization(SchedulerComponent):
    """A component that optimizes for time variety using entropy-inspired approach.
    
    This component adds an optimization objective (not constraints) to spread teams
    across different time slots throughout the season. Uses squared deviation from
    uniform distribution as a proxy for entropy maximization.
    """
    
    def __init__(self):
        """Initialize the component."""
        super().__init__()
        self.add_optimizer(self._get_time_variety_optimizer())
        self.add_debug_report(self._get_time_variety_debug_report())

    def _get_time_variety_optimizer(self):
        """Create an optimizer function for time variety.
        
        Returns:
            ModelActor: An optimizer that maximizes time variety across teams
        """
        def optimize_time_variety(schedule: Schedule):
            """Add time variety optimization to the OR-Tools model.
            
            The heuristic: For each team-time combination, contribute
            (games_per_season - games_at_this_time) to the objective.
            This rewards teams that spread their games across time slots.
            
            Args:
                schedule: The schedule model to add the optimization to
            """
            # Get unique weekend and time combinations
            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            time_idxs = sorted(list(set(m.time_idx for m in schedule.matches)))
            
            # Calculate total games per team (assuming 1 game per team per weekend)
            games_per_season = len(weekend_idxs)
            
            # Create variables to count how many times each team plays at each time slot
            team_time_counts = {}
            for t_idx in schedule.teams:
                for time_idx in time_idxs:
                    var_name = f'team_{t_idx}_time_{time_idx}_count'
                    team_time_counts[t_idx, time_idx] = schedule.model.NewIntVar(
                        0, games_per_season, var_name
                    )
            
            # Link the counting variables to actual game assignments
            # Sum all playing_at_time variables for each team-time combination
            for t_idx in schedule.teams:
                for time_idx in time_idxs:
                    # Collect all playing_at_time variables for this team and time across all weekends
                    playing_vars = []
                    for weekend_idx in weekend_idxs:
                        # Check if this combination exists in the schedule
                        key = (weekend_idx, time_idx, t_idx)
                        if key in schedule.playing_at_time:
                            playing_vars.append(schedule.playing_at_time[key])
                    
                    # Link count to sum of playing variables
                    if playing_vars:
                        schedule.model.Add(team_time_counts[t_idx, time_idx] == sum(playing_vars))
                    else:
                        # No games possible at this time for this team
                        schedule.model.Add(team_time_counts[t_idx, time_idx] == 0)
            
            # Create time variety contribution variables
            # For each team-time combination: 
            # - contribute 0 if team plays 0 games at this time
            # - contribute (games_per_season - games_at_this_time) if team plays > 0 games
            time_variety_contributions = {}
            for t_idx in schedule.teams:
                for time_idx in time_idxs:
                    var_name = f'variety_contrib_team_{t_idx}_time_{time_idx}'
                    time_variety_contributions[t_idx, time_idx] = schedule.model.NewIntVar(
                        0, games_per_season, var_name
                    )
                    
                    # Create boolean variable: is this team playing any games at this time?
                    plays_at_time_var_name = f'plays_at_time_team_{t_idx}_time_{time_idx}'
                    plays_at_time = schedule.model.NewBoolVar(plays_at_time_var_name)
                    
                    # Link boolean to whether count > 0
                    # plays_at_time == 1 iff team_time_counts > 0
                    schedule.model.Add(team_time_counts[t_idx, time_idx] >= 1).OnlyEnforceIf(plays_at_time)
                    schedule.model.Add(team_time_counts[t_idx, time_idx] == 0).OnlyEnforceIf(plays_at_time.Not())
                    
                    # Set the contribution based on whether team plays at this time
                    # If plays_at_time == 0: contribution = 0
                    # If plays_at_time == 1: contribution = games_per_season - team_time_counts
                    schedule.model.Add(time_variety_contributions[t_idx, time_idx] == 0).OnlyEnforceIf(plays_at_time.Not())
                    schedule.model.Add(
                        time_variety_contributions[t_idx, time_idx] == 
                        games_per_season - team_time_counts[t_idx, time_idx]
                    ).OnlyEnforceIf(plays_at_time)
            
            # Calculate total time variety objective value
            total_time_variety = sum(time_variety_contributions[t_idx, time_idx] 
                                   for t_idx in schedule.teams 
                                   for time_idx in time_idxs)
            
            # Maximize time variety (minimize negative time variety)
            schedule.model.Maximize(total_time_variety)
        
        return ModelActor(optimize_time_variety)

    def _get_time_variety_debug_report(self):
        """Create a debug report function for time variety analysis.
        
        Returns:
            DebugReporter: A debug reporter that shows time slot distribution
        """
        def generate_time_variety_report(schedule):
            """Generate a debug report showing team time slot distribution.
            
            Args:
                schedule: The solved schedule to report on
                
            Returns:
                str: Debug report string
            """
            game_report = schedule.get_game_report()
            
            lines = []
            lines.append("TIME VARIETY OPTIMIZATION DEBUG REPORT")
            lines.append("=" * 50)
            
            # Create time slot distribution table
            # Get unique time slots and teams
            time_idxs = sorted(game_report['time_idx'].unique())
            teams = sorted(schedule.teams)
            
            # Count games per team per time slot
            team_time_matrix = []
            
            for team in teams:
                team_row = [team]  # Start with team ID
                team_games = game_report[
                    (game_report['team1'] == team) | (game_report['team2'] == team)
                ]
                
                for time_idx in time_idxs:
                    count = len(team_games[team_games['time_idx'] == time_idx])
                    team_row.append(count)
                
                team_time_matrix.append(team_row)
            
            # Create DataFrame for pretty printing
            columns = ['Team'] + [f'Time_{idx}' for idx in time_idxs]
            df = pd.DataFrame(team_time_matrix, columns=columns)
            
            lines.append("TEAM vs TIME SLOT DISTRIBUTION")
            lines.append("-" * 40)
            lines.append(str(df.to_string(index=False)))
            
            # Calculate statistics
            lines.append("")
            lines.append("DISTRIBUTION STATISTICS")
            lines.append("-" * 25)
            
            # Calculate ideal distribution
            total_games_per_team = len(game_report) // len(teams) * 2  # Each game involves 2 teams
            ideal_per_slot = total_games_per_team / len(time_idxs)
            lines.append(f"Ideal games per team per time slot: {ideal_per_slot:.2f}")
            
            # Calculate actual distribution stats
            for time_idx in time_idxs:
                col_name = f'Time_{time_idx}'
                if col_name in df.columns:
                    values = df[col_name].values
                    avg = values.mean()
                    std = values.std()
                    min_val = values.min()
                    max_val = values.max()
                    lines.append(f"Time slot {time_idx}: avg={avg:.2f}, std={std:.2f}, min={min_val}, max={max_val}")
            
            # Overall variance measure
            time_cols = [col for col in df.columns if col.startswith('Time_')]
            if time_cols:
                all_values = df[time_cols].values.flatten()
                overall_std = all_values.std()
                lines.append(f"Overall standard deviation: {overall_std:.2f}")
                lines.append(f"Variance score (lower is better): {overall_std:.2f}")
            
            lines.append("")
            
            # Check for teams that are "stuck" at one time
            lines.append("POTENTIAL ISSUES")
            lines.append("-" * 18)
            
            issues_found = False
            for _, row in df.iterrows():
                team = row['Team']
                time_counts = [row[col] for col in time_cols]
                max_count = max(time_counts)
                total_count = sum(time_counts)
                
                if total_count > 0:
                    max_percentage = max_count / total_count
                    if max_percentage > 0.6:  # If more than 60% of games at one time
                        max_time_idx = time_idxs[time_counts.index(max_count)]
                        lines.append(f"⚠️  Team {team}: {max_percentage:.1%} of games at time slot {max_time_idx}")
                        issues_found = True
            
            if not issues_found:
                lines.append("✅ No teams heavily concentrated in single time slots")
            
            return "\n".join(lines)
        
        return DebugReporter(generate_time_variety_report, "TimeVarietyOptimization") 