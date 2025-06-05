from ..schedule_component import SchedulerComponent, ModelActor
from ..schedule import Schedule
import math


class VsPlayBalanceConstraint(SchedulerComponent):
    """A component that balances games between team pairs based on divisions.
    
    Teams in different divisions should not play each other.
    Teams in the same division should play each other between:
    - Min: floor(games_per_season / teams_in_division) 
    - Max: ceil(games_per_season / teams_in_division)
    """
    
    def __init__(self):
        """Initialize the component."""
        super().__init__()
        self.add_constraint(self._get_vs_play_balance_constraint())
        self.add_validator(self._get_vs_play_balance_validator())

    def _get_vs_play_balance_constraint(self):
        """Create a constraint function for the OR-Tools model.
        
        Returns:
            function: A constraint function that adds vs play balance requirements to the model
        """
        def enforce_vs_play_balance(schedule: Schedule):
            """Add the vs play balance constraints to the OR-Tools model.
            
            Args:
                schedule: The schedule model to add the constraint to
            """
            games_per_season = schedule.facilities.games_per_season

            # For each team pair, determine min/max games
            for t1 in schedule.teams:
                for t2 in schedule.teams:
                    if t1 >= t2:  # Only process each pair once
                        continue
                    
                    t1_div = schedule.team_div[t1]
                    t2_div = schedule.team_div[t2]
                    
                    if t1_div != t2_div:
                        # Different divisions - should not play each other
                        min_games = 0
                        max_games = 0
                    else:
                        # Same division - calculate min/max based on division size
                        teams_in_division = schedule.facilities.team_counts[t1_div]
                        min_games = games_per_season // teams_in_division
                        max_games = math.ceil(games_per_season / teams_in_division)
                    
                    # Create boolean flags for when these teams play each other
                    vs_match_flags = []
                    
                    for m in schedule.matches:
                        # Create variables for both possible matchups (t1 vs t2, t2 vs t1)
                        both_1 = schedule.model.NewBoolVar(f"vs_{t1}_home_{t2}_away_in_{m}")
                        schedule.model.AddBoolAnd([
                            schedule.is_home[m, t1], 
                            schedule.is_away[m, t2]
                        ]).OnlyEnforceIf(both_1)
                        schedule.model.AddBoolOr([
                            schedule.is_home[m, t1].Not(), 
                            schedule.is_away[m, t2].Not()
                        ]).OnlyEnforceIf(both_1.Not())

                        both_2 = schedule.model.NewBoolVar(f"vs_{t2}_home_{t1}_away_in_{m}")
                        schedule.model.AddBoolAnd([
                            schedule.is_home[m, t2], 
                            schedule.is_away[m, t1]
                        ]).OnlyEnforceIf(both_2)
                        schedule.model.AddBoolOr([
                            schedule.is_home[m, t2].Not(), 
                            schedule.is_away[m, t1].Not()
                        ]).OnlyEnforceIf(both_2.Not())

                        either = schedule.model.NewBoolVar(f"vs_match_{t1}_{t2}_{m}")
                        schedule.model.AddBoolOr([both_1, both_2]).OnlyEnforceIf(either)
                        schedule.model.AddBoolAnd([both_1.Not(), both_2.Not()]).OnlyEnforceIf(either.Not())

                        vs_match_flags.append(either)
                    
                    # Add min/max constraints
                    total_vs_games = sum(vs_match_flags)
                    schedule.model.Add(total_vs_games >= min_games)
                    schedule.model.Add(total_vs_games <= max_games)
        
        return ModelActor(enforce_vs_play_balance)

    def _get_vs_play_balance_validator(self):
        """Create a validator function to verify the constraint was satisfied.
        
        Returns:
            function: A validator function that checks vs play balance
        """
        def validate_vs_play_balance(schedule):
            """Verify that team pairs played the correct number of games against each other.
            
            Args:
                schedule: The solved schedule to validate
                
            Raises:
                ValueError: If any team pair's vs games are outside the expected range
            """
            games_per_season = schedule.facilities.games_per_season

            
            # Get the team report which contains vs play data
            team_report = schedule.get_team_report()
            
            for t1 in schedule.teams:
                for t2 in schedule.teams:
                    if t1 >= t2:  # Only check each pair once
                        continue
                    
                    t1_div = schedule.team_div[t1]
                    t2_div = schedule.team_div[t2]
                    
                    if t1_div != t2_div:
                        # Different divisions - should not play each other
                        min_games = 0
                        max_games = 0
                    else:
                        # Same division - calculate min/max based on division size
                        teams_in_division = schedule.facilities.team_counts[t1_div]
                        min_games = games_per_season // teams_in_division
                        max_games = math.ceil(games_per_season / teams_in_division)
                    
                    # Check the actual games played using the vs column from team report
                    actual_games = team_report.loc[t1, f'vs_{t2}']
                    
                    if actual_games < min_games or actual_games > max_games:
                        raise ValueError(
                            f"Teams {t1} and {t2} played {actual_games} games against each other, "
                            f"but should play between {min_games} and {max_games} games"
                        )
        
        return validate_vs_play_balance 