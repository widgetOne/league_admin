from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule


class ByeWeekOptimization(SchedulerComponent):
    """A component that optimizes bye weeks.
    
    This component provides:
    1. An optimization to minimize bye weeks
    2. A debug report showing bye week distribution
    """
    def __init__(self, weight=10.0):
        """Initialize the component.
        
        Args:
            weight: The relative weight of this optimization compared to others
        """
        super().__init__()
        self.weight = weight
        self.add_optimizer(self._get_bye_weeks_optimizer())
        self.add_debug_report(self._get_bye_weeks_debug_report())
        self.add_debug_summary(self._get_bye_weeks_debug_summary())

    def _get_bye_weeks_debug_summary(self):
        def generate_bye_weeks_summary(schedule):
            game_report = schedule.get_game_report()
            weekend_idxs = sorted(game_report['weekend_idx'].unique())
            bye_counts = {}
            for t_idx in schedule.teams:
                byes = 0
                for w in weekend_idxs:
                    week_games = game_report[game_report['weekend_idx'] == w]
                    games_played = len(week_games[(week_games['team1'] == t_idx) | (week_games['team2'] == t_idx)])
                    if games_played == 0:
                        byes += 1
                bye_counts[byes] = bye_counts.get(byes, 0) + 1
            
            summary_parts = []
            for byes in sorted(bye_counts.keys()):
                summary_parts.append(f"{bye_counts[byes]} teams with {byes} byes")
            
            return "Bye distribution: " + ", ".join(summary_parts)
            
        return DebugReporter(generate_bye_weeks_summary, "ByeWeekOptimization")

    def _get_bye_weeks_optimizer(self):
        """Create an optimizer function to minimize bye weeks.
        
        Returns:
            ModelActor: An optimizer that minimizes bye weeks
        """
        def optimize_bye_weeks(schedule: Schedule):
            """Add bye weeks optimization to the OR-Tools model.
            
            Penalty escalates 10× per additional bye for the same team:
              1 bye  →  1 × weight
              2 byes → 11 × weight  (1 + 10)
              3 byes → 111 × weight (1 + 10 + 100)
            This makes it extremely expensive for any team to accumulate
            multiple byes.
            
            Args:
                schedule: The schedule model to add the optimization to
            """
            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            total_weeks = len(weekend_idxs)
            
            # Create per-weekend bye indicators
            bye_week_vars = {}
            for w_idx in weekend_idxs:
                for t_idx in schedule.teams:
                    key = (w_idx, t_idx)
                    bye_week_vars[key] = schedule.model.NewBoolVar(f"bye_week_{w_idx}_{t_idx}")
                    schedule.model.Add(schedule.games_per_weekend[key] == 0).OnlyEnforceIf(bye_week_vars[key])
                    schedule.model.Add(schedule.games_per_weekend[key] > 0).OnlyEnforceIf(bye_week_vars[key].Not())
            
            if not hasattr(schedule, 'things_to_minimize'):
                schedule.things_to_minimize = []
            
            # Escalating penalty: cumulative target is N * 10^(N-1) x weight.
            # - N=1 (1 bye): target = 1
            # - N=2 (2 byes): target = 20
            # - N=3 (3 byes): target = 300
            # - N=4 (4 byes): target = 4000
            def get_cumulative_target(n):
                if n <= 0:
                    return 0
                return n * (10 ** (n - 1))
            
            for t_idx in schedule.teams:
                team_bye_vars = [bye_week_vars[(w_idx, t_idx)] for w_idx in weekend_idxs]
                total_byes = schedule.model.NewIntVar(0, total_weeks, f"total_byes_{t_idx}")
                schedule.model.Add(total_byes == sum(team_bye_vars))
                
                # Create threshold bools and add escalating penalties
                for k in range(1, total_weeks + 1):
                    has_k_byes = schedule.model.NewBoolVar(f"has_ge_{k}_byes_{t_idx}")
                    schedule.model.Add(total_byes >= k).OnlyEnforceIf(has_k_byes)
                    schedule.model.Add(total_byes < k).OnlyEnforceIf(has_k_byes.Not())
                    
                    incremental_multiplier = get_cumulative_target(k) - get_cumulative_target(k - 1)
                    
                    schedule.things_to_minimize.append(has_k_byes * int(self.weight * incremental_multiplier))
        
        return ModelActor(optimize_bye_weeks)

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