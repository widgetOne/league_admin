from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule


class BalanceReffingConstraint(SchedulerComponent):
    """A component that balances referee assignments across teams and weekends.
    
    Ensures:
    - Each team plays exactly 1 game per weekend  
    - Each team refs 0-1 games per weekend
    - Each team refs exactly total_weeks // 2 games per season
    """
    
    def __init__(self):
        """Initialize the component."""
        super().__init__()
        self.add_constraint(self._get_balance_reffing_constraint())
        self.add_validator(self._get_balance_reffing_validator())
        self.add_debug_report(self._get_balance_reffing_debug_report())

    def _get_balance_reffing_constraint(self):
        """Create a constraint function for the OR-Tools model.
        
        Returns:
            function: A constraint function that adds referee balancing requirements to the model
        """
        def enforce_balance_reffing(schedule: Schedule):
            """Add the referee balancing constraints to the OR-Tools model.
            
            Args:
                schedule: The schedule model to add the constraint to
            """
            # Get weekend indices from matches
            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            total_weeks = len(weekend_idxs)
            games_per_day = schedule.facilities.games_per_season // total_weeks  # Should be 1 for volleyball
            
            # Weekend play targets - each team plays 0-2 games per weekend
            # This allows for double headers and byes to balance out over the season
            for w in weekend_idxs:
                for t_idx in schedule.teams:
                    weekend_playing_vars = [schedule.is_playing[m, t_idx] for m in schedule.matches if m.weekend_idx == w]
                    schedule.model.Add(sum(weekend_playing_vars) <= 2)  # Allow up to 2 games per weekend
                    schedule.model.Add(sum(weekend_playing_vars) >= 0)  # Allow byes
            
            # Weekend ref targets - each team refs 0-1 games per weekend
            for w in weekend_idxs:
                for t_idx in schedule.teams:
                    weekend_reffing_vars = [schedule.is_ref[m, t_idx] for m in schedule.matches if m.weekend_idx == w]
                    schedule.model.Add(sum(weekend_reffing_vars) <= 1)
                    schedule.model.Add(sum(weekend_reffing_vars) >= 0)
            
            # Total ref in a season - each team refs exactly total_weeks // 2
            season_ref_target = total_weeks // 2
            for t_idx in schedule.teams:
                season_reffing_vars = [schedule.is_ref[m, t_idx] for m in schedule.matches]
                schedule.model.Add(sum(season_reffing_vars) == season_ref_target)
        
        return ModelActor(enforce_balance_reffing)

    def _get_balance_reffing_validator(self):
        """Create a validator function to verify the constraint was satisfied.
        
        Returns:
            function: A validator function that checks referee balance
        """
        def validate_balance_reffing(schedule):
            """Verify that referee assignments are properly balanced.
            
            Args:
                schedule: The solved schedule to validate
                
            Raises:
                ValueError: If referee balancing constraints are violated
            """
            # Get reports
            game_report = schedule.get_game_report()
            team_report = schedule.get_team_report()
            
            # Get weekend indices and targets
            weekend_idxs = sorted(game_report['weekend_idx'].unique())
            total_weeks = len(weekend_idxs)
            games_per_day = schedule.facilities.games_per_season // total_weeks
            season_ref_target = total_weeks // 2
            
            # Check weekend play targets
            for w in weekend_idxs:
                week_games = game_report[game_report['weekend_idx'] == w]
                for t_idx in schedule.teams:
                    # Count how many games this team played this weekend
                    games_played = len(week_games[(week_games['team1'] == t_idx) | (week_games['team2'] == t_idx)])
                    if games_played > 2 or games_played < 0:  # Allow 0-2 games per weekend
                        raise ValueError(
                            f"Team {t_idx} played {games_played} games in weekend {w}, "
                            f"but should play between 0 and 2 games"
                        )
            
            # Check weekend ref targets (0-1 games per weekend)
            for w in weekend_idxs:
                week_games = game_report[game_report['weekend_idx'] == w]
                for t_idx in schedule.teams:
                    # Count how many games this team reffed this weekend
                    games_reffed = len(week_games[week_games['ref'] == t_idx])
                    if games_reffed > 1:
                        raise ValueError(
                            f"Team {t_idx} reffed {games_reffed} games in weekend {w}, "
                            f"but should ref at most 1 game per weekend"
                        )
            
            # Check season ref totals
            for t_idx in schedule.teams:
                total_refs = team_report.loc[t_idx, 'total_ref']
                if total_refs != season_ref_target:
                    raise ValueError(
                        f"Team {t_idx} reffed {total_refs} games in the season, "
                        f"but should ref exactly {season_ref_target} games"
                    )
        
        return validate_balance_reffing

    def _get_balance_reffing_debug_report(self):
        """Create a debug report function to verify referee balance.
        
        Returns:
            DebugReporter: A debug reporter that shows referee assignment balance
        """
        def generate_balance_reffing_report(schedule):
            """Generate a debug report showing referee assignment balance.
            
            Args:
                schedule: The solved schedule to report on
                
            Returns:
                str: Debug report string
            """
            game_report = schedule.get_game_report()
            team_report = schedule.get_team_report()
            
            # Get weekend indices and targets
            weekend_idxs = sorted(game_report['weekend_idx'].unique())
            total_weeks = len(weekend_idxs)
            games_per_day = schedule.facilities.games_per_season // total_weeks
            season_ref_target = total_weeks // 2
            
            lines = []
            lines.append("REFEREE BALANCE DEBUG REPORT")
            lines.append("=" * 50)
            lines.append(f"Games per day target: {games_per_day}")
            lines.append(f"Season ref target: {season_ref_target}")
            lines.append("")
            
            # Weekend play report
            lines.append("WEEKEND PLAY DISTRIBUTION")
            lines.append("-" * 30)
            lines.append("Team | " + " | ".join(f"W{w}" for w in weekend_idxs) + " | Total")
            lines.append("-" * (8 + len(weekend_idxs) * 5 + 8))
            
            all_play_correct = True
            for t_idx in schedule.teams:
                row = f"{t_idx:4d} | "
                total_games = 0
                for w in weekend_idxs:
                    week_games = game_report[game_report['weekend_idx'] == w]
                    games_played = len(week_games[(week_games['team1'] == t_idx) | (week_games['team2'] == t_idx)])
                    total_games += games_played
                    status = "✓" if games_played == games_per_day else "✗"
                    if status == "✗":
                        all_play_correct = False
                    row += f"{games_played}{status} | "
                
                total_status = "✓" if total_games == schedule.facilities.games_per_season else "✗"
                row += f"{total_games}{total_status}"
                lines.append(row)
            
            lines.append("")
            
            # Weekend ref report
            lines.append("WEEKEND REF DISTRIBUTION")
            lines.append("-" * 30)
            lines.append("Team | " + " | ".join(f"W{w}" for w in weekend_idxs) + " | Total")
            lines.append("-" * (8 + len(weekend_idxs) * 5 + 8))
            
            all_ref_correct = True
            for t_idx in schedule.teams:
                row = f"{t_idx:4d} | "
                total_refs = 0
                for w in weekend_idxs:
                    week_games = game_report[game_report['weekend_idx'] == w]
                    games_reffed = len(week_games[week_games['ref'] == t_idx])
                    total_refs += games_reffed
                    status = "✓" if games_reffed <= 1 else "✗"
                    if status == "✗":
                        all_ref_correct = False
                    row += f"{games_reffed}{status} | "
                
                total_status = "✓" if total_refs == season_ref_target else "✗"
                if total_status == "✗":
                    all_ref_correct = False
                row += f"{total_refs}{total_status}"
                lines.append(row)
            
            lines.append("")
            play_status = "✓ PASS" if all_play_correct else "✗ FAIL"
            ref_status = "✓ PASS" if all_ref_correct else "✗ FAIL"
            overall_status = "✓ PASS" if all_play_correct and all_ref_correct else "✗ FAIL"
            
            lines.append(f"Weekend Play Status: {play_status}")
            lines.append(f"Weekend Ref Status: {ref_status}")
            lines.append(f"Overall Status: {overall_status}")
            
            return "\n".join(lines)
        
        return DebugReporter(generate_balance_reffing_report, "BalanceReffingConstraint") 