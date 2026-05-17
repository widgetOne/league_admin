import datetime
from typing import List, Optional, Iterable
from ortools.sat.python import cp_model
from .facilities.facility import Facilities
from .schedule import Schedule
from .schedule_component import SchedulerComponent

class ScheduleCreator:
    """A factory class for creating and configuring Schedule instances."""
    
    def __init__(self, 
                 facilities: Facilities, 
                 model: Optional[cp_model.CpModel] = None,
                 components: Optional[Iterable[SchedulerComponent]] = None):
        """Initialize the ScheduleCreator.
        
        Args:
            facilities: The Facilities object containing all facility constraints
            model: Optional OR-Tools model. If None, creates a new CpModel.
            components: Optional iterable of SchedulerComponents to apply
        """
        self.facilities = facilities
        if model is not None:
            self.model = model
        else:
            self.model = cp_model.CpModel()
        self.components = list(components) if components is not None else []
    
    def add_component(self, component: SchedulerComponent):
        """Add a single component to the schedule.
        
        Args:
            component: SchedulerComponent to add
        """
        self.components.append(component)
    
    def add_components(self, components: Iterable[SchedulerComponent]):
        """Add multiple components to the schedule.
        
        Args:
            components: Iterable of SchedulerComponents to add
        """
        self.components.extend(components)
    
    def create_schedule(self, solve_time_seconds: float = 240.0) -> Schedule:
        """Create and configure a Schedule instance.
        
        Args:
            solve_time_seconds: Maximum time in seconds for the solver to run.
            
        Returns:
            Schedule: A fully configured Schedule instance ready for solving
        """
        # Create the base schedule
        schedule = Schedule(self.facilities, self.model)
        
        # Collect all component classes for logging
        all_component_classes = []
        for component in self.components:
            all_component_classes.extend(component.get_component_classes())
        
        # Apply all components
        constraint_classes = []
        optimizer_classes = []
        
        for component in self.components:
            # Add constraints from the component
            for constraint in component._constraints:
                constraint(schedule)
                constraint_classes.extend(component.get_component_classes())
            
            # Add optimizers from the component
            for optimizer in component._optimizers:
                optimizer(schedule)
                optimizer_classes.extend(component.get_component_classes())
        
        # Log which components were applied before solving
        if all_component_classes:
            unique_classes = sorted(set(all_component_classes))
            print(f"Applied components: {', '.join(unique_classes)}")
            
            if constraint_classes:
                unique_constraint_classes = sorted(set(constraint_classes))
                print(f"  - Constraints from: {', '.join(unique_constraint_classes)}")
                
            if optimizer_classes:
                unique_optimizer_classes = sorted(set(optimizer_classes))
                print(f"  - Optimizers from: {', '.join(unique_optimizer_classes)}")
        
        # Minimize combined optimization terms if any exist
        if hasattr(schedule, 'things_to_minimize'):
            schedule.model.Minimize(sum(schedule.things_to_minimize))
        
        schedule.solve(solve_time_seconds=solve_time_seconds)
        
        # Only run validators and post-processors if a solution was found
        if schedule._last_solve_status not in (
            cp_model.OPTIMAL, cp_model.FEASIBLE
        ):
            status_name = schedule.solver.StatusName(schedule._last_solve_status)
            print(f"\n⚠️  Solver returned {status_name} — skipping validators and post-processors.")
            return schedule

        # Validate that that schedule meets all constraints
        validator_classes = []
        for component in self.components:
            for validator in component._validators:
                validator(schedule)
                validator_classes.extend(component.get_component_classes())
        
        # Apply any post-processing
        post_processor_classes = []
        for component in self.components:
            for post_processor in component._post_processors:
                post_processor(schedule)
                post_processor_classes.extend(component.get_component_classes())
        
        # Log validation and post-processing if they occurred
        if validator_classes:
            unique_validator_classes = sorted(set(validator_classes))
            print(f"  - Validators from: {', '.join(unique_validator_classes)}")
            
        if post_processor_classes:
            unique_post_processor_classes = sorted(set(post_processor_classes))
            print(f"  - Post-processors from: {', '.join(unique_post_processor_classes)}")
        
        return schedule

    def generate_debug_reports(self, schedule: Schedule) -> str:
        """Generate all debug reports from components using the solved schedule.
        
        Args:
            schedule: The solved schedule to generate reports for
            
        Returns:
            str: Combined debug reports from all components
        """
        # Collect debug reports from all components
        debug_reports = []
        debug_summaries = []
        for component in self.components:
            debug_reports.extend(component._debug_reports)
            debug_summaries.extend(component._debug_summaries)
        
        if not debug_reports and not debug_summaries:
            return "No debug reports available."
        
        report_sections = []
        
        # Build Executive Summary Block
        summary_sections = []
        if debug_summaries:
            summary_sections.append("EXECUTIVE SUMMARY")
            score = schedule.solver.ObjectiveValue() if schedule.has_solution else "N/A"
            summary_sections.append(f"Schedule with score of {score:,.0f} generated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            summary_sections.append("=" * 60)
            for debug_summary in debug_summaries:
                summary_text = debug_summary(schedule)
                if summary_text:
                    summary_sections.append(f"[{debug_summary.component_name}]")
                    summary_sections.append(summary_text)
                    summary_sections.append("")
            summary_sections.append("=" * 60)
            summary_sections.append("")
            
            # Prepend summary block
            report_sections.extend(summary_sections)
            
        report_sections.append("COMPONENT DEBUG REPORTS")
        report_sections.append("=" * 60)
        report_sections.append("")
        
        for debug_report in debug_reports:
            report_sections.append(f"Component: {debug_report.component_name}")
            report_sections.append("-" * 40)
            report_sections.append(debug_report(schedule))
            report_sections.append("")
            report_sections.append("")
            
        # Append summary block again at the end
        if debug_summaries:
            report_sections.append("")
            report_sections.extend(summary_sections)
        
        return "\n".join(report_sections) 