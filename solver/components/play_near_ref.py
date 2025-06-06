from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule


class PlayNearRefConstraint(SchedulerComponent):
    """A component that ensures teams can only ref when they're playing around that time.
    
    Ensures:
    - Teams can only be busy with one thing at a time (busy_count <= 1)
    - Teams can only ref if they're playing before or after that time slot
    """
    
    def __init__(self):
        """Initialize the component."""
        super().__init__()
        self.add_constraint(self._get_play_near_ref_constraint())
        self.add_validator(self._get_play_near_ref_validator())
        self.add_debug_report(self._get_play_near_ref_debug_report())

    def _get_play_near_ref_constraint(self):
        """Create a constraint function for the OR-Tools model.
        
        Returns:
            function: A constraint function that adds play near ref requirements to the model
        """
        def enforce_play_near_ref(schedule: Schedule):
            """Add the play near ref constraints to the OR-Tools model.
            
            Args:
                schedule: The schedule model to add the constraint to
            """
            # Get weekend indices and max time index from matches
            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            max_time_idx = max(m.time_idx for m in schedule.matches) + 1
            
            # Teams can only be busy with one thing at a time, and can only ref if playing around that time
            for weekend_idx in weekend_idxs:
                for time_idx in range(max_time_idx):
                    for t_idx in schedule.teams:
                        # Busy count constraint: teams can only be busy with one thing at a time
                        schedule.model.Add(schedule.busy_count[weekend_idx, time_idx, t_idx] <= 1)
                        
                        # Implication: if reffing at time, must be playing around that time
                        schedule.model.AddImplication(
                            schedule.reffing_at_time[weekend_idx, time_idx, t_idx], 
                            schedule.playing_around_time[weekend_idx, time_idx, t_idx]
                        )
        
        return ModelActor(enforce_play_near_ref)

    def _get_play_near_ref_validator(self):
        """Create a validator function to verify the constraint was satisfied.
        
        Returns:
            function: A validator function that checks play near ref constraints
        """
        def validate_play_near_ref(schedule):
            """Verify that teams only ref when playing around that time.
            
            Args:
                schedule: The solved schedule to validate
                
            Raises:
                ValueError: If play near ref constraints are violated
            """
            game_report = schedule.get_game_report()
            
            # Check that teams don't ref and play simultaneously
            violations = []
            for _, game in game_report.iterrows():
                ref_team = game['ref']
                playing_teams = [game['team1'], game['team2']]
                
                if ref_team in playing_teams:
                    violations.append(f"Team {ref_team} is both playing and reffing in game: {game.to_dict()}")
            
            if violations:
                raise ValueError(f"Teams reffing and playing simultaneously: {violations}")
            
            # Check that reffing teams are playing around that time
            # Group games by weekend and time
            for weekend_idx in game_report['weekend_idx'].unique():
                for time_idx in game_report['time_idx'].unique():
                    weekend_time_games = game_report[
                        (game_report['weekend_idx'] == weekend_idx) & 
                        (game_report['time_idx'] == time_idx)
                    ]
                    
                    for _, game in weekend_time_games.iterrows():
                        ref_team = game['ref']
                        
                        # Check if ref team is playing around this time (before or after)
                        weekend_games = game_report[game_report['weekend_idx'] == weekend_idx]
                        ref_team_games = weekend_games[
                            (weekend_games['team1'] == ref_team) | (weekend_games['team2'] == ref_team)
                        ]
                        
                        # Check if ref team plays at adjacent time slots
                        ref_time_slots = set(ref_team_games['time_idx'])
                        adjacent_times = {time_idx - 1, time_idx + 1}
                        
                        if not (ref_time_slots & adjacent_times):
                            # Also check if they play at the same time (shouldn't happen due to busy constraint)
                            if time_idx not in ref_time_slots:
                                violations.append(
                                    f"Team {ref_team} is reffing at weekend {weekend_idx}, time {time_idx} "
                                    f"but not playing around that time. Plays at times: {sorted(ref_time_slots)}"
                                )
            
            if violations:
                raise ValueError(f"Teams reffing without playing around that time: {violations}")
        
        return validate_play_near_ref

    def _get_play_near_ref_debug_report(self):
        """Create a debug report function to verify play near ref constraints.
        
        Returns:
            DebugReporter: A debug reporter that shows play near ref analysis
        """
        def generate_play_near_ref_report(schedule):
            """Generate a debug report showing play near ref constraint compliance.
            
            Args:
                schedule: The solved schedule to report on
                
            Returns:
                str: Debug report string
            """
            game_report = schedule.get_game_report()
            
            lines = []
            lines.append("PLAY NEAR REF DEBUG REPORT")
            lines.append("=" * 50)
            
            # Check for simultaneous play/ref violations
            simultaneous_violations = []
            for _, game in game_report.iterrows():
                ref_team = game['ref']
                playing_teams = [game['team1'], game['team2']]
                if ref_team in playing_teams:
                    simultaneous_violations.append(game)
            
            lines.append(f"Simultaneous play/ref violations: {len(simultaneous_violations)}")
            if simultaneous_violations:
                lines.append("VIOLATIONS:")
                for game in simultaneous_violations:
                    lines.append(f"  Team {game['ref']} refs and plays in game at {game['date']} {game['time']}")
                lines.append("")
            
            # Check play around time compliance
            around_time_violations = []
            for weekend_idx in sorted(game_report['weekend_idx'].unique()):
                for time_idx in sorted(game_report['time_idx'].unique()):
                    weekend_time_games = game_report[
                        (game_report['weekend_idx'] == weekend_idx) & 
                        (game_report['time_idx'] == time_idx)
                    ]
                    
                    for _, game in weekend_time_games.iterrows():
                        ref_team = game['ref']
                        
                        # Get ref team's games this weekend
                        weekend_games = game_report[game_report['weekend_idx'] == weekend_idx]
                        ref_team_games = weekend_games[
                            (weekend_games['team1'] == ref_team) | (weekend_games['team2'] == ref_team)
                        ]
                        
                        ref_time_slots = set(ref_team_games['time_idx'])
                        adjacent_times = {time_idx - 1, time_idx + 1}
                        
                        if not (ref_time_slots & adjacent_times) and time_idx not in ref_time_slots:
                            around_time_violations.append({
                                'weekend': weekend_idx,
                                'time': time_idx,
                                'ref_team': ref_team,
                                'ref_plays_at': sorted(ref_time_slots)
                            })
            
            lines.append(f"Play around time violations: {len(around_time_violations)}")
            if around_time_violations:
                lines.append("VIOLATIONS:")
                for violation in around_time_violations:
                    lines.append(f"  Weekend {violation['weekend']}, Time {violation['time']}: "
                               f"Team {violation['ref_team']} refs but plays at {violation['ref_plays_at']}")
                lines.append("")
            
            # Summary by weekend and time
            lines.append("REF TEAM PLAY SCHEDULE ANALYSIS")
            lines.append("-" * 40)
            
            for weekend_idx in sorted(game_report['weekend_idx'].unique()):
                lines.append(f"Weekend {weekend_idx}:")
                weekend_games = game_report[game_report['weekend_idx'] == weekend_idx]
                
                for time_idx in sorted(weekend_games['time_idx'].unique()):
                    time_games = weekend_games[weekend_games['time_idx'] == time_idx]
                    lines.append(f"  Time {time_idx}:")
                    
                    for _, game in time_games.iterrows():
                        ref_team = game['ref']
                        
                        # Get ref team's play times this weekend
                        ref_plays = weekend_games[
                            (weekend_games['team1'] == ref_team) | (weekend_games['team2'] == ref_team)
                        ]['time_idx'].tolist()
                        
                        status = "✓" if (time_idx - 1 in ref_plays or time_idx + 1 in ref_plays) else "✗"
                        lines.append(f"    Game {game['date']} {game['time']}: Ref={ref_team} {status} (plays at {sorted(ref_plays)})")
                
                lines.append("")
            
            # Overall status
            overall_pass = len(simultaneous_violations) == 0 and len(around_time_violations) == 0
            status = "✓ PASS" if overall_pass else "✗ FAIL"
            lines.append(f"Overall Status: {status}")
            
            return "\n".join(lines)
        
        return DebugReporter(generate_play_near_ref_report, "PlayNearRefConstraint") 