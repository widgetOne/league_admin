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
    
    def create_schedule(self) -> Schedule:
        """Create and configure a Schedule instance.
        
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
        
        schedule.solve()

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
        for component in self.components:
            debug_reports.extend(component._debug_reports)
        
        if not debug_reports:
            return "No debug reports available."
        
        report_sections = []
        report_sections.append("COMPONENT DEBUG REPORTS")
        report_sections.append("=" * 60)
        report_sections.append("")
        
        for debug_report in debug_reports:
            report_sections.append(f"Component: {debug_report.component_name}")
            report_sections.append("-" * 40)
            report_sections.append(debug_report(schedule))
            report_sections.append("")
            report_sections.append("")
        
        return "\n".join(report_sections) 