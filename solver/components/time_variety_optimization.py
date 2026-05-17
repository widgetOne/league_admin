from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule
import pandas as pd


class TimeVarietyOptimization(SchedulerComponent):
    """A component that optimizes for time variety using entropy-inspired approach.
    
    This component adds an optimization objective (not constraints) to spread teams
    across different time slots throughout the season. Uses squared deviation from
    uniform distribution as a proxy for entropy maximization.
    """
    
    def __init__(self, weight=1.0):
        """Initialize the component.
        
        Args:
            weight: The relative weight of this optimization compared to others
        """
        super().__init__()
        self.weight = weight
        self.add_optimizer(self._get_time_variety_optimizer())
        self.add_debug_report(self._get_time_variety_debug_report())
        self.add_debug_summary(self._get_time_variety_debug_summary())

    def _get_time_variety_debug_summary(self):
        def generate_time_variety_summary(schedule):
            game_report = schedule.get_game_report()
            time_idxs = sorted(game_report['time_idx'].unique())
            teams = sorted(schedule.teams)
            
            distinct_slots = []
            for team in teams:
                team_games = game_report[(game_report['team1'] == team) | (game_report['team2'] == team)]
                unique_slots = team_games['time_idx'].nunique()
                distinct_slots.append(unique_slots)
            
            if distinct_slots:
                min_slots = min(distinct_slots)
                max_slots = max(distinct_slots)
                avg_slots = sum(distinct_slots) / len(distinct_slots)
                variance = sum((s - avg_slots) ** 2 for s in distinct_slots) / len(distinct_slots)
                
                # Calculate the objective penalty (which is scaled by 100 in the model)
                total_dev = 0
                total_teams = len(teams)
                for time_idx in time_idxs:
                    games_at_this_time = sum(1 for m in schedule.matches if m.time_idx == time_idx)
                    target = (games_at_this_time * 2) / total_teams
                    for team in teams:
                        team_games = game_report[(game_report['team1'] == team) | (game_report['team2'] == team)]
                        actual = len(team_games[team_games['time_idx'] == time_idx])
                        total_dev += abs(actual - target)
                
                penalty = total_dev * self.weight * 100
                
                return (
                    f"Distinct time slots per team: min={min_slots}, max={max_slots}, "
                    f"avg={avg_slots:.1f}, var={variance:.2f} | penalty: {penalty:.0f}"
                )
            return "No games scheduled"
            
        return DebugReporter(generate_time_variety_summary, "TimeVarietyOptimization")

    def _get_time_variety_optimizer(self):
        """Create an optimizer function for time variety.
        
        Returns:
            ModelActor: An optimizer that maximizes time variety across teams
        """
        def optimize_time_variety(schedule: Schedule):
            """Add time variety optimization to the OR-Tools model.
            
            The heuristic: For each time slot, calculate target plays per team as
            (games_at_that_time * 2) / total_teams. Then minimize the absolute
            deviation of each team's actual plays from the target for each time slot.
            
            Args:
                schedule: The schedule model to add the optimization to
            """
            # Get unique weekend and time combinations
            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            time_idxs = sorted(list(set(m.time_idx for m in schedule.matches)))
            
            # Calculate target plays per team for each time slot dynamically from facilities
            # For each time slot: target = (games_at_that_time * 2) / total_teams
            time_slot_targets = {}
            total_teams = len(schedule.teams)
            
            for time_idx in time_idxs:
                # Count games at this time slot across all weekends
                games_at_this_time = sum(1 for m in schedule.matches if m.time_idx == time_idx)
                # Each game involves 2 teams, so total team-slots = games * 2
                target_plays = (games_at_this_time * 2) / total_teams
                time_slot_targets[time_idx] = target_plays
                print(f"Time slot {time_idx}: {games_at_this_time} games, target {target_plays:.2f} plays per team")
            
            # Create variables to count how many times each team plays at each time slot
            team_time_counts = {}
            max_possible_games = len(weekend_idxs)  # Maximum games any team could play at one time slot
            for t_idx in schedule.teams:
                for time_idx in time_idxs:
                    var_name = f'team_{t_idx}_time_{time_idx}_count'
                    team_time_counts[t_idx, time_idx] = schedule.model.NewIntVar(
                        0, max_possible_games, var_name
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
            
            # Create absolute deviation variables for each team-time combination
            # For each team-time: |actual_plays - target_plays|
            absolute_deviations = {}
            for t_idx in schedule.teams:
                for time_idx in time_idxs:
                    target = time_slot_targets[time_idx]
                    
                    # Since OR-Tools works with integers, multiply target by 100 for precision
                    target_times_100 = int(target * 100)
                    max_deviation_times_100 = max_possible_games * 100
                    
                    # Create variable for the absolute deviation (scaled by 100)
                    abs_dev_var_name = f'abs_dev_team_{t_idx}_time_{time_idx}'
                    absolute_deviations[t_idx, time_idx] = schedule.model.NewIntVar(
                        0, max_deviation_times_100, abs_dev_var_name
                    )
                    
                    # Create variable for the signed deviation (actual - target) * 100
                    signed_dev_var_name = f'signed_dev_team_{t_idx}_time_{time_idx}'
                    signed_deviation = schedule.model.NewIntVar(
                        -max_deviation_times_100, max_deviation_times_100, signed_dev_var_name
                    )
                    
                    # Link signed deviation: signed_dev = (actual_count * 100) - target_times_100
                    actual_times_100 = team_time_counts[t_idx, time_idx] * 100
                    schedule.model.Add(signed_deviation == actual_times_100 - target_times_100)
                    
                    # Link absolute deviation: abs_dev = |signed_dev|
                    schedule.model.Add(absolute_deviations[t_idx, time_idx] >= signed_deviation)
                    schedule.model.Add(absolute_deviations[t_idx, time_idx] >= -signed_deviation)
            
            # Calculate total absolute deviation across all teams and time slots
            total_absolute_deviation = sum(absolute_deviations[t_idx, time_idx] 
                                         for t_idx in schedule.teams 
                                         for time_idx in time_idxs)
            
            # Store the optimization terms in the shared list
            if not hasattr(schedule, 'things_to_minimize'):
                schedule.things_to_minimize = []
            
            # Add the time variety terms with their weight
            schedule.things_to_minimize.extend([d * self.weight for d in absolute_deviations.values()])
        
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
            
            # ── Per-division analysis ─────────────────────────────────
            lines.append("")
            lines.append("DIVISION ANALYSIS")
            lines.append("-" * 40)
            
            # Group teams by division
            divisions = {}
            for team in teams:
                div_idx = schedule.team_div[team]
                if div_idx not in divisions:
                    divisions[div_idx] = []
                divisions[div_idx].append(team)
            
            # Get time labels from schedule for readable output
            time_labels = {}
            for m in schedule.matches:
                if m.time_idx not in time_labels:
                    time_labels[m.time_idx] = m.time
            
            for div_idx in sorted(divisions.keys()):
                div_teams = divisions[div_idx]
                lines.append(f"\n  Division {div_idx} ({len(div_teams)} teams)")
                lines.append(f"  {'─' * 36}")
                
                # Average distinct time slots per team in this division
                div_distinct = []
                # Weighted average time index per team
                div_avg_times = []
                
                for team in div_teams:
                    team_games = game_report[
                        (game_report['team1'] == team) | (game_report['team2'] == team)
                    ]
                    div_distinct.append(team_games['time_idx'].nunique())
                    
                    if len(team_games) > 0:
                        avg_time = team_games['time_idx'].mean()
                        div_avg_times.append(avg_time)
                
                avg_distinct = sum(div_distinct) / len(div_distinct) if div_distinct else 0
                lines.append(f"  Avg distinct time slots: {avg_distinct:.1f}")
                
                if div_avg_times:
                    div_mean_time = sum(div_avg_times) / len(div_avg_times)
                    time_label = time_labels.get(round(div_mean_time), f"idx {div_mean_time:.1f}")
                    lines.append(f"  Avg time of play: slot {div_mean_time:.2f} (~{time_label})")
                    
                    # Show time slot breakdown for this division
                    div_games = game_report[
                        (game_report['team1'].isin(div_teams)) | (game_report['team2'].isin(div_teams))
                    ]
                    slot_counts = div_games['time_idx'].value_counts().sort_index()
                    total_div_appearances = slot_counts.sum()
                    slot_parts = []
                    for tidx in time_idxs:
                        count = slot_counts.get(tidx, 0)
                        pct = count / total_div_appearances * 100 if total_div_appearances > 0 else 0
                        slot_parts.append(f"slot {tidx}: {count} ({pct:.0f}%)")
                    lines.append(f"  Distribution: {', '.join(slot_parts)}")
            
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