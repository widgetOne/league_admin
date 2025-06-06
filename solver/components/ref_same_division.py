from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule


class RefSameDivisionConstraint(SchedulerComponent):
    """A component that ensures referees are from the same division as the home team.
    
    Ensures:
    - The referee's division matches the home team's division for each match
    """
    
    def __init__(self):
        """Initialize the component."""
        super().__init__()
        self.add_constraint(self._get_ref_same_division_constraint())
        self.add_validator(self._get_ref_same_division_validator())
        self.add_debug_report(self._get_ref_same_division_debug_report())

    def _get_ref_same_division_constraint(self):
        """Create a constraint function for the OR-Tools model.
        
        Returns:
            function: A constraint function that ensures refs are from same division as home team
        """
        def enforce_ref_same_division(schedule: Schedule):
            """Add the ref same division constraints to the OR-Tools model.
            
            Args:
                schedule: The schedule model to add the constraint to
            """
            # For each match, referee division must equal home team division
            for m in schedule.matches:
                schedule.model.Add(schedule.home_div[m] == schedule.ref_div[m])
        
        return ModelActor(enforce_ref_same_division)

    def _get_ref_same_division_validator(self):
        """Create a validator function to verify the constraint was satisfied.
        
        Returns:
            function: A validator function that checks ref same division constraint
        """
        def validate_ref_same_division(schedule):
            """Verify that referees are from the same division as home teams.
            
            Args:
                schedule: The solved schedule to validate
                
            Raises:
                ValueError: If ref same division constraints are violated
            """
            game_report = schedule.get_game_report()
            violations = []
            
            for _, game in game_report.iterrows():
                home_team = game['team1']  # team1 is home team
                ref_team = game['ref']
                
                # Get divisions from facilities
                home_division = schedule.team_div[home_team]
                ref_division = schedule.team_div[ref_team]
                
                if home_division != ref_division:
                    violations.append(
                        f"Game {game['date']} {game['time']}: Home team {home_team} (div {home_division}) "
                        f"reffed by team {ref_team} (div {ref_division})"
                    )
            
            if violations:
                raise ValueError(f"Referee not from same division as home team: {violations}")
        
        return validate_ref_same_division

    def _get_ref_same_division_debug_report(self):
        """Create a debug report function to verify ref same division constraint.
        
        Returns:
            DebugReporter: A debug reporter that shows ref same division analysis
        """
        def generate_ref_same_division_report(schedule):
            """Generate a debug report showing ref same division constraint compliance.
            
            Args:
                schedule: The solved schedule to report on
                
            Returns:
                str: Debug report string
            """
            game_report = schedule.get_game_report()
            
            lines = []
            lines.append("REF SAME DIVISION DEBUG REPORT")
            lines.append("=" * 50)
            
            # Group teams by division for analysis
            divisions = {}
            for team in schedule.teams:
                div_idx = schedule.team_div[team]
                if div_idx not in divisions:
                    divisions[div_idx] = []
                divisions[div_idx].append(team)
            
            lines.append("DIVISION ANALYSIS")
            lines.append("-" * 20)
            
            total_violations = 0
            for div, div_teams in sorted(divisions.items()):
                lines.append(f"Division {div} (Teams: {sorted(div_teams)})")
                
                # Find games where home team is from this division
                home_games = game_report[game_report['team1'].isin(div_teams)]
                
                correct_refs = 0
                division_violations = []
                
                for _, game in home_games.iterrows():
                    ref_team = game['ref']
                    ref_division = schedule.team_div[ref_team]
                    
                    if ref_division == div:
                        correct_refs += 1
                    else:
                        division_violations.append({
                            'game': f"{game['date']} {game['time']}",
                            'home': game['team1'],
                            'ref': ref_team,
                            'ref_div': ref_division
                        })
                        total_violations += 1
                
                lines.append(f"  Games with home team from div {div}: {len(home_games)}")
                lines.append(f"  Correct same-division refs: {correct_refs}")
                lines.append(f"  Violations: {len(division_violations)}")
                
                if division_violations:
                    lines.append("  VIOLATIONS:")
                    for v in division_violations:
                        lines.append(f"    Game {v['game']}: Home={v['home']} Ref={v['ref']} (div {v['ref_div']})")
                
                lines.append("")
            
            # Summary table
            lines.append("REFEREE ASSIGNMENT SUMMARY")
            lines.append("-" * 30)
            lines.append("Home Div | Ref Div | Count")
            lines.append("-" * 30)
            
            # Create a cross-tabulation
            for home_div, home_teams in sorted(divisions.items()):
                home_games = game_report[game_report['team1'].isin(home_teams)]
                
                for ref_div, ref_teams in sorted(divisions.items()):
                    count = len(home_games[home_games['ref'].isin(ref_teams)])
                    status = "✓" if home_div == ref_div else ("✗" if count > 0 else " ")
                    lines.append(f"   {home_div:2d}    |   {ref_div:2d}    | {count:3d} {status}")
            
            lines.append("")
            
            # Overall status
            overall_pass = total_violations == 0
            status = "✓ PASS" if overall_pass else "✗ FAIL"
            lines.append(f"Total violations: {total_violations}")
            lines.append(f"Overall Status: {status}")
            
            return "\n".join(lines)
        
        return DebugReporter(generate_ref_same_division_report, "RefSameDivisionConstraint") 