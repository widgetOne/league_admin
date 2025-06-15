from ..schedule_component import SchedulerComponent, DebugReporter
from ..schedule import Schedule


class MinimizeByeWeeks(SchedulerComponent):
    """A component that will eventually minimize bye weeks, but for now just reports on them.
    
    This component currently only provides:
    1. A debug report showing bye week distribution
    """
    def __init__(self):
        """Initialize the component."""
        super().__init__()
        self.add_debug_report(self._get_bye_weeks_debug_report())

    def _get_bye_weeks_debug_report(self):
        """Create a debug report function to show bye week distribution.
        
        Returns:
            DebugReporter: A debug reporter that shows bye week distribution
        """
        def generate_bye_weeks_report(schedule):
            """Generate a debug report showing bye week distribution.
            
            Args:
                schedule: The solved schedule to report on
                
            Returns:
                str: Debug report string
            """
            game_report = schedule.get_game_report()
            
            lines = []
            lines.append("BYE WEEKS DEBUG REPORT")
            lines.append("=" * 50)
            
            # Get weekend indices
            weekend_idxs = sorted(game_report['weekend_idx'].unique())
            
            # Count games per team per weekend
            bye_weeks = {}  # team_idx -> list of weekends with byes
            double_headers = {}  # team_idx -> list of weekends with double headers
            
            for t_idx in schedule.teams:
                bye_weeks[t_idx] = []
                double_headers[t_idx] = []
                
                for w in weekend_idxs:
                    week_games = game_report[game_report['weekend_idx'] == w]
                    games_played = len(week_games[(week_games['team1'] == t_idx) | (week_games['team2'] == t_idx)])
                    
                    if games_played == 0:
                        bye_weeks[t_idx].append(w)
                    elif games_played == 2:
                        double_headers[t_idx].append(w)
            
            # Summary statistics
            total_byes = sum(len(byes) for byes in bye_weeks.values())
            total_double_headers = sum(len(dh) for dh in double_headers.values())
            teams_with_byes = sum(1 for byes in bye_weeks.values() if byes)
            teams_with_double_headers = sum(1 for dh in double_headers.values() if dh)
            
            lines.append("\nSUMMARY STATISTICS")
            lines.append("-" * 30)
            lines.append(f"Total bye weeks: {total_byes}")
            lines.append(f"Total double header weeks: {total_double_headers}")
            lines.append(f"Teams with bye weeks: {teams_with_byes}")
            lines.append(f"Teams with double headers: {teams_with_double_headers}")
            
            # Detailed team report
            lines.append("\nTEAM BYE WEEKS AND DOUBLE HEADERS")
            lines.append("-" * 50)
            lines.append("Team | Bye Weeks | Double Header Weeks")
            lines.append("-" * 50)
            
            for t_idx in sorted(schedule.teams):
                bye_str = ", ".join(str(w) for w in bye_weeks[t_idx]) or "None"
                dh_str = ", ".join(str(w) for w in double_headers[t_idx]) or "None"
                lines.append(f"{t_idx:4d} | {bye_str:10s} | {dh_str}")
            
            return "\n".join(lines)
        
        return DebugReporter(generate_bye_weeks_report, "MinimizeByeWeeks") 