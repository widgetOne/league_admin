from ..schedule_component import SchedulerComponent

class TotalPlayConstraint(SchedulerComponent):
    """A component that ensures each team plays exactly the specified number of games.
    
    This component provides both:
    1. A constraint for the OR-Tools model to enforce during solving
    2. A validator to verify the constraint was satisfied after solving
    """
    def __init__(self, total_games_per_team):
        """Initialize the component with the target number of games per team.
        
        Args:
            total_games_per_team (int): The number of games each team should play
        """
        super().__init__()
        self.add_constraint(self._get_total_play_constraint(total_games_per_team))
        self.add_validator(self._get_total_play_validator(total_games_per_team))

    def _get_total_play_constraint(self, total_games):
        """Create a constraint function for the OR-Tools model.
        
        This function will be used by the solver to enforce the total games requirement
        during the solving process.
        
        Args:
            total_games (int): The number of games each team should play
            
        Returns:
            function: A constraint function that adds the total games requirement to the model
        """
        def enforce_total_play(schedule):
            """Add the total games constraint to the OR-Tools model.
            
            Args:
                schedule: The schedule model to add the constraint to
            """
            model = schedule._model
            for team in schedule.teams:
                games_played = sum(schedule.is_playing[m, team] for m in schedule.matches)
                model.Add(games_played == total_games)
        return enforce_total_play

    def _get_total_play_validator(self, total_games):
        """Create a validator function to verify the constraint was satisfied.
        
        This function will be run after solving to verify that each team
        actually played the required number of games.
        
        Args:
            total_games (int): The number of games each team should play
            
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
            for team in schedule.teams:
                games_played = schedule.get_games_played(team)
                if games_played != total_games:
                    raise ValueError(
                        f"Team {team} has played {games_played} games, "
                        f"but should play exactly {total_games} games"
                    )
        return validate_total_play

