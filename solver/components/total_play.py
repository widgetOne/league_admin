from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule
from ..exhibition import exhibition_games_by_division, has_exhibition_games


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
        self.add_debug_summary(self._get_total_play_debug_summary())

    def _get_total_play_debug_summary(self):
        def generate_total_play_summary(schedule):
            total_games = schedule.facilities.games_per_season
            team_report = schedule.get_team_report()
            official_plays = team_report['official_play'].value_counts().to_dict()
            exhibition_plays = team_report['exhibition_play'].value_counts().to_dict() if 'exhibition_play' in team_report else {}
            
            summary_parts = []
            for games, count in sorted(official_plays.items()):
                if games == total_games:
                    summary_parts.append(f"All {count} teams play exactly {games} official games")
                else:
                    summary_parts.append(f"{count} teams play {games} official games")
                    
            exhibition_count = sum(team_report.get('exhibition_play', [])) // 2 if 'exhibition_play' in team_report else 0
            if exhibition_count > 0:
                summary_parts.append(f"plus {exhibition_count} exhibition games scheduled")
                
            return "Total Play: " + ", ".join(summary_parts)
            
        return DebugReporter(generate_total_play_summary, "TotalPlayConstraint")

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
            
            # 1. Official games must exactly match the target for each team.
            #    When no exhibitions exist, is_official_play is already aliased
            #    to is_playing in schedule.py, so this just constrains total plays.
            for team in schedule.teams:
                official_games_played = sum(schedule.is_official_play[m, team] for m in schedule.matches)
                schedule.model.Add(official_games_played == total_games)
                
            # 2. Exhibition constraints — only needed when the parity math requires them.
            #    Skip entirely for even team counts to avoid creating thousands of extra variables.
            if not has_exhibition_games(schedule.facilities.team_counts, total_games):
                return
            
            expected_by_div = exhibition_games_by_division(schedule.facilities.team_counts, total_games)
            
            for div_idx, expected_exhibition in enumerate(expected_by_div):
                if schedule.facilities.team_counts[div_idx] <= 0:
                    continue
                    
                div_exhibitions = []
                for team in schedule.teams:
                    if schedule.team_div[team] == div_idx:
                        for m in schedule.matches:
                            exhibition_var = schedule.model.NewIntVar(0, 1, f"exhibition_{m}_{team}")
                            schedule.model.Add(exhibition_var == schedule.is_playing[m, team] - schedule.is_official_play[m, team])
                            div_exhibitions.append(exhibition_var)
                            
                schedule.model.Add(sum(div_exhibitions) == expected_exhibition)
                    
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
                games_played = team_report.loc[team_idx, 'official_play']
                if games_played != total_games:
                    raise ValueError(
                        f"Team {team_idx} has played {games_played} official games, "
                        f"but should play exactly {total_games} official games. "
                        f"(Total physical games: {team_report.loc[team_idx, 'total_play']})"
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

