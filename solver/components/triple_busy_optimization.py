from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule


class TripleBusyOptimization(SchedulerComponent):
    """A component that optimizes to minimize weekends with 3 or more busy times.
    
    This component provides:
    1. An optimization to minimize weekends where teams are busy 3 or more times
    2. A debug report showing busy time distribution
    """
    def __init__(self, weight=100.0):
        """Initialize the component.
        
        Args:
            weight: The relative weight of this optimization compared to others
        """
        super().__init__()
        self.weight = weight
        self.add_optimizer(self._get_triple_busy_optimizer())
        self.add_debug_report(self._get_triple_busy_debug_report())
    
    def _get_triple_busy_optimizer(self) -> ModelActor:
        """Get the optimizer that minimizes weekends with 3 or more busy times."""
        def optimize_triple_busy(schedule: Schedule):
            # Create variables for each team-weekend that is busy 3 or more times
            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            triple_busy_vars = {}
            for w_idx in weekend_idxs:
                for t_idx in range(schedule.total_teams):
                    key = (w_idx, t_idx)
                    # Create a boolean variable that is true if busy_count_per_weekend >= 3
                    triple_busy_vars[key] = schedule.model.NewBoolVar(f"triple_busy_{w_idx}_{t_idx}")
                    # If busy_count_per_weekend >= 3, then triple_busy_vars[key] must be true
                    schedule.model.Add(schedule.busy_count_per_weekend[key] >= 3).OnlyEnforceIf(triple_busy_vars[key])
                    schedule.model.Add(schedule.busy_count_per_weekend[key] < 3).OnlyEnforceIf(triple_busy_vars[key].Not())
            
            # Initialize things_to_minimize if it doesn't exist
            if not hasattr(schedule, 'things_to_minimize'):
                schedule.things_to_minimize = []
                    
            # Add each triple busy variable with its weight individually
            schedule.things_to_minimize.extend([var * self.weight for var in triple_busy_vars.values()])
        
        return ModelActor(optimize_triple_busy)
    
    def _get_triple_busy_debug_report(self) -> DebugReporter:
        """Get a debug report showing busy time distribution."""
        def report_triple_busy(schedule: Schedule) -> str:
            """Generate a debug report for the triple busy optimization."""
            lines = []
            if not hasattr(schedule, 'things_to_minimize') or not schedule.things_to_minimize:
                return "TripleBusyOptimization: No minimization goals found."

            # Check if a solution exists
            if not schedule.solver.ObjectiveValue() is not None:
                return "TripleBusyOptimization: No solution found."

            lines.append("TripleBusyOptimization Component Report:")
            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            
            # Count weekends with 3 or more busy times for each team
            triple_busy_counts = {}
            for t_idx in range(schedule.total_teams):
                triple_busy_counts[t_idx] = 0
                for w_idx in weekend_idxs:
                    key = (w_idx, t_idx)
                    if schedule.solver.Value(schedule.busy_count_per_weekend[key]) >= 3:
                        triple_busy_counts[t_idx] += 1
            
            # Generate report lines
            lines.append("Weekends with 3 or more busy times per team:")
            lines.append(f"Total weekends with 3+ busy times: {sum(triple_busy_counts.values())}")
            
            for t_idx, count in triple_busy_counts.items():
                if count > 0:
                    lines.append(f"  Team {t_idx}: {count} weekends")
            
            return "\n".join(lines)
        
        return DebugReporter(report_triple_busy, "Triple Busy Optimization")

    def add_constraints(self, schedule: Schedule) -> None:
        """Adds minimization goals to the schedule."""
        weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
        
        # Ensure things_to_minimize is initialized
        if not hasattr(schedule, 'things_to_minimize'):
            schedule.things_to_minimize = []
        
        triple_busy_vars = {}
        for w_idx in weekend_idxs:
            for t_idx in range(schedule.total_teams):
                key = (w_idx, t_idx)
                triple_busy_vars[key] = schedule.model.NewBoolVar(f'triple_busy_{w_idx}_{t_idx}')

                # Create a boolean variable that is true if busy_count_per_weekend >= 3
                # This requires schedule.busy_count_per_weekend to be defined
                # If busy_count_per_weekend >= 3, then triple_busy_vars[key] must be true
                schedule.model.Add(schedule.busy_count_per_weekend[key] >= 3).OnlyEnforceIf(triple_busy_vars[key])
                schedule.model.Add(schedule.busy_count_per_weekend[key] < 3).OnlyEnforceIf(triple_busy_vars[key].Not())

        # Add weights for triple-busy variables
        schedule.things_to_minimize.extend(
            (var, 1) for var in triple_busy_vars.values()
        )

        report_lines = ["TripleBusyOptimization Component Report:"]
        violations = []
        
        # Calculate how many weekends each team is busy 3 or more times
        triple_busy_counts = {}
        for t_idx in range(schedule.total_teams):
            triple_busy_counts[t_idx] = 0
            
            for w_idx in weekend_idxs:
                key = (w_idx, t_idx)
                if schedule.solver.Value(schedule.busy_count_per_weekend[key]) >= 3:
                    triple_busy_counts[t_idx] += 1
        
        # Generate report lines
        lines.append("Weekends with 3 or more busy times per team:")
        lines.append(f"Total weekends with 3+ busy times: {sum(triple_busy_counts.values())}")
        
        for t_idx, count in triple_busy_counts.items():
            if count > 0:
                lines.append(f"  Team {t_idx}: {count} weekends")

        if any(c > 0 for c in triple_busy_counts.values()):
            report_lines.append("\\nViolations Found:") 