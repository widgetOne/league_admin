from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule


class TotalPlayConstraint(SchedulerComponent):
    """A component that ensures each team plays exactly the specified number of games.
    
    This component provides both:
    1. A constraint for the OR-Tools model to enforce during solving
    2. A validator to verify the constraint was satisfied after solving
    """
    def __init__(self):
        """Initialize the component.
        
        The total games per team is retrieved from the model's 'games_per_season' variable.
        """
        super().__init__()
        self.add_constraint(self._get_total_play_constraint())
        self.add_validator(self._get_total_play_validator())
        self.add_debug_report(self._get_total_play_debug_report())

    def _get_total_play_constraint(self):
        """Create a constraint function for the OR-Tools model.
        
        This function will be used by the solver to enforce the total games requirement
        during the solving process.
        
        Returns:
            function: A constraint function that adds the total games requirement to the model
        """
        def enforce_total_play(schedule: Schedule):
            """Add the total games constraint to the OR-Tools model.
            
            Args:
                schedule: The schedule model to add the constraint to
            """
            total_games = schedule.facilities.games_per_season
            for team in schedule.teams:
                games_played = sum(schedule.is_playing[m, team] for m in schedule.matches)
                schedule.model.Add(games_played == total_games)
        return ModelActor(enforce_total_play)

    def _get_total_play_validator(self):
        """Create a validator function to verify the constraint was satisfied.
        
        This function will be run after solving to verify that each team
        actually played the required number of games.
        
        Returns:
            function: A validator function that checks each team's total games
        """
        def validate_total_play(schedule):
            """Verify that each team played exactly the target number of games.
            
            Args:
                schedule: The solved schedule to validate
                
            Raises:
                ValueError: If any team's total games doesn't match the target
            """
            total_games = schedule.facilities.games_per_season
            team_report = schedule.get_team_report()
            
            for team_idx in schedule.teams:
                games_played = team_report.loc[team_idx, 'total_play']
                if games_played != total_games:
                    raise ValueError(
                        f"Team {team_idx} has played {games_played} games, "
                        f"but should play exactly {total_games} games"
                    )
        return validate_total_play

    def _get_total_play_debug_report(self):
        """Create a debug report function to verify total play distribution.
        
        Returns:
            DebugReporter: A debug reporter that shows total play per team
        """
        def generate_total_play_report(schedule):
            """Generate a debug report showing total play per team.
            
            Args:
                schedule: The solved schedule to report on
                
            Returns:
                str: Debug report string
            """
            target_games = schedule.facilities.games_per_season
            team_report = schedule.get_team_report()
            
            lines = []
            lines.append("TOTAL PLAY DEBUG REPORT")
            lines.append("=" * 40)
            lines.append(f"Target games per team: {target_games}")
            lines.append("")
            lines.append("Team | Total Games | Status")
            lines.append("-" * 30)
            
            for team_idx in schedule.teams:
                total_games = team_report.loc[team_idx, 'total_play']
                status = "✓" if total_games == target_games else "✗"
                lines.append(f"{team_idx:4d} | {total_games:11d} | {status}")
            
            # Summary
            all_correct = all(team_report.loc[team_idx, 'total_play'] == target_games 
                             for team_idx in schedule.teams)
            lines.append("")
            lines.append(f"Overall Status: {'✓ PASS' if all_correct else '✗ FAIL'}")
            
            return "\n".join(lines)
        
        return DebugReporter(generate_total_play_report, "TotalPlayConstraint")

