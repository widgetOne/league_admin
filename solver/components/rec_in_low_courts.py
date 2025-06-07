from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule
import pandas as pd


class RecInLowCourtsProcessor(SchedulerComponent):
    """A component that post-processes schedules to ensure divisions are ordered by court.
    
    Ensures:
    - Within each time frame, games are ordered by division (low division on low court numbers)
    - Uses bubble sort to reorder games while preserving all constraint satisfaction
    - All parts of a game (home, away, ref) are moved together
    """
    
    def __init__(self):
        """Initialize the component."""
        super().__init__()
        self.add_post_processor(self._get_rec_in_low_courts_post_processor())
        self.add_debug_report(self._get_rec_in_low_courts_debug_report())

    def _get_rec_in_low_courts_post_processor(self):
        """Create a post-processor function to reorder games by division.
        
        Returns:
            ModelActor: A post-processor that sorts games by division within time frames
        """
        def process_rec_in_low_courts(schedule: Schedule):
            """Reorder games within each time frame by division using bubble sort.
            
            Args:
                schedule: The solved schedule to post-process
            """
            # Create a mapping from original matches to swapped team assignments
            if not hasattr(schedule, '_team_reassignments'):
                schedule._team_reassignments = {}
            
            # Group matches by weekend and time
            matches_by_time = {}
            for match in schedule.matches:
                key = (match.weekend_idx, match.time_idx)
                if key not in matches_by_time:
                    matches_by_time[key] = []
                matches_by_time[key].append(match)
            
            # Process each time frame
            for (weekend_idx, time_idx), time_matches in matches_by_time.items():
                if len(time_matches) <= 1:
                    continue  # No need to sort single game
                
                # Sort matches by location (court) to get current order
                time_matches.sort(key=lambda m: m.location)
                
                # Get current team assignments and their divisions
                game_assignments = []
                for match in time_matches:
                    home_team = schedule.solver.Value(schedule.home_team[match])
                    away_team = schedule.solver.Value(schedule.away_team[match])
                    ref_team = schedule.solver.Value(schedule.ref[match])
                    division = schedule.team_div[home_team]
                    
                    game_assignments.append((division, home_team, away_team, ref_team, match))
                
                # Bubble sort by division
                n = len(game_assignments)
                for i in range(n):
                    for j in range(0, n - i - 1):
                        if game_assignments[j][0] > game_assignments[j + 1][0]:
                            # Swap games
                            game_assignments[j], game_assignments[j + 1] = \
                                game_assignments[j + 1], game_assignments[j]
                
                # Create reassignments: map each match to its new team assignment
                for idx, (division, home_team, away_team, ref_team, original_match) in enumerate(game_assignments):
                    target_match = time_matches[idx]  # Match at the desired court position
                    
                    # Store the reassignment
                    schedule._team_reassignments[target_match] = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'ref': ref_team
                    }
            
            # Clear the cached game report so it gets regenerated with new assignments
            schedule._game_report = None
        
        return ModelActor(process_rec_in_low_courts)

    def _get_rec_in_low_courts_debug_report(self):
        """Create a debug report function to show division layout by court.
        
        Returns:
            DebugReporter: A debug reporter that shows division assignments by court
        """
        def generate_rec_in_low_courts_report(schedule):
            """Generate a debug report showing division layout by court and time.
            
            Args:
                schedule: The solved schedule to report on
                
            Returns:
                str: Debug report string
            """
            game_report = schedule.get_game_report()
            
            lines = []
            lines.append("REC IN LOW COURTS DEBUG REPORT")
            lines.append("=" * 50)
            lines.append("Division layout by court (home team division shown)")
            lines.append("")
            
            # Group by weekend
            for weekend_idx in sorted(game_report['weekend_idx'].unique()):
                lines.append(f"week_idx: {weekend_idx}")
                weekend_games = game_report[game_report['weekend_idx'] == weekend_idx]
                
                # Group by date
                for date in sorted(weekend_games['date'].unique()):
                    lines.append(f"date: {date}")
                    date_games = weekend_games[weekend_games['date'] == date]
                    
                    # Group by time
                    for time in sorted(date_games['time'].unique()):
                        time_games = date_games[date_games['time'] == time]
                        
                        # Sort by court (location)
                        time_games = time_games.sort_values('location')
                        
                        # Get divisions for each court
                        divisions = []
                        for _, game in time_games.iterrows():
                            home_team = game['team1']
                            division = schedule.team_div[home_team]
                            divisions.append(str(division))
                        
                        # Format time string
                        time_str = time.strftime('%H:%M') if hasattr(time, 'strftime') else str(time)
                        divisions_str = ' '.join(divisions)
                        lines.append(f"{time_str} {divisions_str}")
                
                lines.append("")  # Blank line between weeks
            
            # Check if divisions are properly ordered
            lines.append("ORDERING ANALYSIS")
            lines.append("-" * 20)
            
            violations = []
            for weekend_idx in sorted(game_report['weekend_idx'].unique()):
                weekend_games = game_report[game_report['weekend_idx'] == weekend_idx]
                
                for time_idx in sorted(weekend_games['time_idx'].unique()):
                    time_games = weekend_games[weekend_games['time_idx'] == time_idx]
                    time_games = time_games.sort_values('location')
                    
                    # Check if divisions are in ascending order
                    prev_division = -1
                    for _, game in time_games.iterrows():
                        home_team = game['team1']
                        division = schedule.team_div[home_team]
                        
                        if division < prev_division:
                            violations.append(
                                f"Weekend {weekend_idx}, Time {time_idx}: "
                                f"Division {division} after division {prev_division}"
                            )
                        prev_division = division
            
            if violations:
                lines.append(f"Ordering violations: {len(violations)}")
                for violation in violations:
                    lines.append(f"  ✗ {violation}")
            else:
                lines.append("All time frames properly ordered by division")
            
            lines.append("")
            
            # Overall status
            overall_pass = len(violations) == 0
            status = "✓ PASS" if overall_pass else "✗ FAIL"
            lines.append(f"Overall Status: {status}")
            
            return "\n".join(lines)
        
        return DebugReporter(generate_rec_in_low_courts_report, "RecInLowCourtsProcessor") 