from ..schedule_component import SchedulerComponent

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

    def _get_total_play_constraint(self):
        """Create a constraint function for the OR-Tools model.
        
        This function will be used by the solver to enforce the total games requirement
        during the solving process.
        
        Returns:
            function: A constraint function that adds the total games requirement to the model
        """
        def enforce_total_play(schedule):
            """Add the total games constraint to the OR-Tools model.
            
            Args:
                schedule: The schedule model to add the constraint to
            """
            model = schedule._model
            total_games = model.GetVarByName('games_per_season')
            for team in schedule.teams:
                games_played = sum(schedule.is_playing[m, team] for m in schedule.matches)
                model.Add(games_played == total_games)
        return enforce_total_play

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
            total_games = schedule._model.GetVarByName('games_per_season')
            for team in schedule.teams:
                games_played = schedule.get_games_played(team)
                if games_played != total_games:
                    raise ValueError(
                        f"Team {team} has played {games_played} games, "
                        f"but should play exactly {total_games} games"
                    )
        return validate_total_play

