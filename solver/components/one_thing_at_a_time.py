from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule


class OneThingAtATimeConstraint(SchedulerComponent):
    """A component that ensures teams can only be busy with one thing at a time.
    
    Ensures:
    - Teams cannot play and ref simultaneously (busy_count <= 1)
    - At any given time slot, a team is either playing, reffing, or free
    """
    
    def __init__(self):
        """Initialize the component."""
        super().__init__()
        self.add_constraint(self._get_one_thing_at_a_time_constraint())
        self.add_validator(self._get_one_thing_at_a_time_validator())
        self.add_debug_report(self._get_one_thing_at_a_time_debug_report())

    def _get_one_thing_at_a_time_constraint(self):
        """Create a constraint function for the OR-Tools model.
        
        Returns:
            function: A constraint function that ensures teams can only be busy with one thing at a time
        """
        def enforce_one_thing_at_a_time(schedule: Schedule):
            """Add the one thing at a time constraints to the OR-Tools model.
            
            Args:
                schedule: The schedule model to add the constraint to
            """
            # Get weekend indices and max time index from matches
            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            max_time_idx = max(m.time_idx for m in schedule.matches) + 1
            
            # Teams can only be busy with one thing at a time
            for weekend_idx in weekend_idxs:
                for time_idx in range(max_time_idx):
                    for t_idx in schedule.teams:
                        # Busy count constraint: teams can only be busy with one thing at a time
                        schedule.model.Add(schedule.busy_count[weekend_idx, time_idx, t_idx] <= 1)
        
        return ModelActor(enforce_one_thing_at_a_time)

    def _get_one_thing_at_a_time_validator(self):
        """Create a validator function to verify the constraint was satisfied.
        
        Returns:
            function: A validator function that checks one thing at a time constraints
        """
        def validate_one_thing_at_a_time(schedule):
            """Verify that teams are never doing multiple things simultaneously.
            
            Args:
                schedule: The solved schedule to validate
                
            Raises:
                ValueError: If one thing at a time constraints are violated
            """
            game_report = schedule.get_game_report()
            
            # Check that teams don't play and ref simultaneously at any time
            violations = []
            
            # Group games by weekend and time
            for weekend_idx in game_report['weekend_idx'].unique():
                for time_idx in game_report['time_idx'].unique():
                    time_slot_games = game_report[
                        (game_report['weekend_idx'] == weekend_idx) & 
                        (game_report['time_idx'] == time_idx)
                    ]
                    
                    # Check each team's activity at this time slot
                    for t_idx in schedule.teams:
                        activities = []
                        
                        # Check if team is playing (home or away)
                        playing_games = time_slot_games[
                            (time_slot_games['team1'] == t_idx) | (time_slot_games['team2'] == t_idx)
                        ]
                        if len(playing_games) > 0:
                            activities.append('playing')
                        
                        # Check if team is reffing
                        reffing_games = time_slot_games[time_slot_games['ref'] == t_idx]
                        if len(reffing_games) > 0:
                            activities.append('reffing')
                        
                        # If team is doing multiple things, that's a violation
                        if len(activities) > 1:
                            violations.append(
                                f"Team {t_idx} is doing multiple things at weekend {weekend_idx}, "
                                f"time {time_idx}: {', '.join(activities)}"
                            )
                        
                        # Also check if team is playing multiple games at same time
                        if len(playing_games) > 1:
                            violations.append(
                                f"Team {t_idx} is playing multiple games simultaneously at "
                                f"weekend {weekend_idx}, time {time_idx}: {len(playing_games)} games"
                            )
                        
                        # Also check if team is reffing multiple games at same time
                        if len(reffing_games) > 1:
                            violations.append(
                                f"Team {t_idx} is reffing multiple games simultaneously at "
                                f"weekend {weekend_idx}, time {time_idx}: {len(reffing_games)} games"
                            )
            
            if violations:
                raise ValueError(f"Teams doing multiple things simultaneously: {violations}")
        
        return validate_one_thing_at_a_time

    def _get_one_thing_at_a_time_debug_report(self):
        """Create a debug report function to verify one thing at a time constraints.
        
        Returns:
            DebugReporter: A debug reporter that shows team activity analysis
        """
        def generate_one_thing_at_a_time_report(schedule):
            """Generate a debug report showing team activity at each time slot.
            
            Args:
                schedule: The solved schedule to report on
                
            Returns:
                str: Debug report string
            """
            game_report = schedule.get_game_report()
            
            lines = []
            lines.append("ONE THING AT A TIME DEBUG REPORT")
            lines.append("=" * 50)
            
            violations = []
            
            # Summary by weekend and time
            lines.append("TEAM ACTIVITY ANALYSIS")
            lines.append("-" * 30)
            
            for weekend_idx in sorted(game_report['weekend_idx'].unique()):
                lines.append(f"\nWeekend {weekend_idx}:")
                weekend_games = game_report[game_report['weekend_idx'] == weekend_idx]
                
                for time_idx in sorted(weekend_games['time_idx'].unique()):
                    time_slot_games = weekend_games[weekend_games['time_idx'] == time_idx]
                    lines.append(f"  Time {time_idx}:")
                    
                    # Track team activities at this time slot
                    team_activities = {}
                    
                    for _, game in time_slot_games.iterrows():
                        team1, team2, ref = game['team1'], game['team2'], game['ref']
                        
                        # Track playing activities
                        for team in [team1, team2]:
                            if team not in team_activities:
                                team_activities[team] = []
                            team_activities[team].append('P')  # P for Playing
                        
                        # Track reffing activities
                        if ref not in team_activities:
                            team_activities[ref] = []
                        team_activities[ref].append('R')  # R for Reffing
                    
                    # Report team activities and check for violations
                    for team, activities in team_activities.items():
                        activity_str = ''.join(activities)
                        busy_count = len(activities)
                        
                        if busy_count > 1:
                            status = "✗"
                            violations.append(f"Weekend {weekend_idx}, Time {time_idx}: Team {team} busy {busy_count} times")
                        else:
                            status = "✓"
                        
                        lines.append(f"    Team {team:2d}: {activity_str} (busy={busy_count}) {status}")
                    
                    # Show teams that are free (not playing or reffing)
                    busy_teams = set(team_activities.keys())
                    free_teams = [t for t in schedule.teams if t not in busy_teams]
                    if free_teams:
                        # Only show first few free teams to avoid clutter
                        if len(free_teams) <= 5:
                            free_str = ', '.join(map(str, free_teams))
                        else:
                            free_str = f"{', '.join(map(str, free_teams[:3]))} ... (+{len(free_teams)-3} more)"
                        lines.append(f"    Free teams: {free_str}")
            
            lines.append("")
            
            # Violation summary
            lines.append("VIOLATIONS SUMMARY")
            lines.append("-" * 20)
            
            if violations:
                lines.append(f"Total violations: {len(violations)}")
                for violation in violations:
                    lines.append(f"  ✗ {violation}")
            else:
                lines.append("No violations found")
            
            lines.append("")
            
            # Overall status
            overall_pass = len(violations) == 0
            status = "✓ PASS" if overall_pass else "✗ FAIL"
            lines.append(f"Overall Status: {status}")
            
            return "\n".join(lines)
        
        return DebugReporter(generate_one_thing_at_a_time_report, "OneThingAtATimeConstraint") 