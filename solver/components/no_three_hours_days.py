from ..schedule_component import SchedulerComponent, ModelActor, DebugReporter
from ..schedule import Schedule


class NoThreeHoursDays(SchedulerComponent):
    """A component that constrains teams to not be busy for 3+ hours in a day.
    
    This component provides:
    1. A constraint that prevents teams from being busy at time X and times X-2, X+2, X+3
    2. A debug report showing busy time distribution
    """
    def __init__(self):
        """Initialize the component."""
        super().__init__()
        self.add_constraint(self._get_no_three_hours_constraint())
        self.add_validator(self._get_no_three_hours_validator())
        self.add_debug_report(self._get_no_three_hours_debug_report())
    
    def _get_no_three_hours_constraint(self) -> ModelActor:
        """Get the constraint that prevents 3+ hour busy periods."""
        def add_no_three_hours_constraint(schedule: Schedule):
            # Get all weekend and time indices
            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            time_indices = sorted(list(set(m.time_idx for m in schedule.matches)))
            
            # For each team and weekend
            for w_idx in weekend_idxs:
                for t_idx in range(schedule.total_teams):
                    # For each pair of time slots
                    for time_idx in time_indices:
                        for other_time_idx in time_indices:
                            # If time slots are not consecutive (gap > 1), they can't both be busy
                            if abs(time_idx - other_time_idx) > 1:
                                busy_key = (w_idx, time_idx, t_idx)
                                other_key = (w_idx, other_time_idx, t_idx)
                                
                                if busy_key in schedule.busy_at_time and other_key in schedule.busy_at_time:
                                    # If busy at time_idx, then not busy at other_time_idx
                                    schedule.model.AddImplication(
                                        schedule.busy_at_time[busy_key],
                                        schedule.busy_at_time[other_key].Not()
                                    )
        
        return ModelActor(add_no_three_hours_constraint)
    
    def _get_no_three_hours_validator(self) -> ModelActor:
        """Get the validator that checks no team is at field for 3+ hours."""
        def validate_no_three_hours(schedule: Schedule):
            """Validate that no team is at the field for 3 or more hours."""
            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            time_indices = sorted(list(set(m.time_idx for m in schedule.matches)))
            
            violations = []
            
            for w_idx in weekend_idxs:
                for t_idx in range(schedule.total_teams):
                    # Find all times this team is busy
                    busy_times = []
                    for time_idx in time_indices:
                        key = (w_idx, time_idx, t_idx)
                        if key in schedule.busy_at_time and schedule.solver.Value(schedule.busy_at_time[key]):
                            busy_times.append(time_idx)
                    
                    if len(busy_times) >= 2:
                        # Calculate total time at field (earliest to latest)
                        earliest_time = min(busy_times)
                        latest_time = max(busy_times)
                        total_hours = latest_time - earliest_time + 1
                        
                        if total_hours >= 3:
                            violations.append(f"Team {t_idx}, Weekend {w_idx}: at field for {total_hours} hours (times {earliest_time}-{latest_time})")
            
            if violations:
                violation_msg = "NO THREE HOURS DAYS VIOLATIONS:\n" + "\n".join(f"  {v}" for v in violations)
                raise ValueError(violation_msg)
        
        return ModelActor(validate_no_three_hours)
    
    def _get_no_three_hours_debug_report(self) -> DebugReporter:
        """Get a debug report showing total time at field per team per weekend."""
        def report_no_three_hours(schedule: Schedule) -> str:
            """Generate a debug report table for total time at field."""
            lines = []
            lines.append("TOTAL TIME AT FIELD DEBUG REPORT")
            lines.append("========================================")
            
            # Check if a solution exists
            if not hasattr(schedule, '_last_solve_status'):
                return "NoThreeHoursDays: No solution found."

            weekend_idxs = sorted(list(set(m.weekend_idx for m in schedule.matches)))
            time_indices = sorted(list(set(m.time_idx for m in schedule.matches)))
            
            # Create table header
            header = "Team |"
            for w_idx in weekend_idxs:
                header += f" W{w_idx} |"
            lines.append(header)
            lines.append("-" * len(header))
            
            # Create table rows
            violations_found = False
            for t_idx in range(schedule.total_teams):
                row = f"{t_idx:4d} |"
                
                for w_idx in weekend_idxs:
                    # Find all times this team is busy this weekend
                    busy_times = []
                    for time_idx in time_indices:
                        key = (w_idx, time_idx, t_idx)
                        if key in schedule.busy_at_time and schedule.solver.Value(schedule.busy_at_time[key]):
                            busy_times.append(time_idx)
                    
                    if len(busy_times) == 0:
                        total_hours = 0
                    elif len(busy_times) == 1:
                        total_hours = 1
                    else:
                        # Calculate total time at field (earliest to latest)
                        earliest_time = min(busy_times)
                        latest_time = max(busy_times)
                        total_hours = latest_time - earliest_time + 1
                    
                    # Mark violations with ✗
                    if total_hours >= 3:
                        row += f"  {total_hours}✗ |"
                        violations_found = True
                    else:
                        row += f"   {total_hours} |"
                
                lines.append(row)
            
            # Add summary
            lines.append("")
            if violations_found:
                lines.append("✗ VIOLATIONS FOUND: Teams marked with ✗ are at field for 3+ hours")
            else:
                lines.append("✓ PASS: No teams at field for 3+ hours")
            
            return "\n".join(lines)
        
        return DebugReporter(report_no_three_hours, "No Three Hours Days") 