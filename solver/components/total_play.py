from ..schedule_component import SchedulerComponent

class TotalPlayConstraint(SchedulerComponent):
    """A constraint that ensures each team plays exactly the specified number of games.
    
    This component adds a constraint that verifies each team's total number of games
    matches the specified target number.
    """
    def __init__(self, total_games_per_team):
        """Initialize the constraint with the target number of games per team.
        
        Args:
            total_games_per_team (int): The number of games each team should play
        """
        super().__init__()
        self.add_constraint(self._get_total_play_constraint(total_games_per_team))

    def _get_total_play_constraint(self, total_games):
        """Create a constraint function that enforces the total games per team.
        
        Args:
            total_games (int): The number of games each team should play
            
        Returns:
            function: A constraint function that checks each team's total games
        """
        def enforce_total_play(schedule):
            """Enforce that each team plays exactly the target number of games.
            
            Args:
                schedule: The schedule to check and enforce the constraint on
                
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
        return enforce_total_play 