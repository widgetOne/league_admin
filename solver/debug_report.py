from typing import Optional, List, Any
import pathlib
import datetime
from .schedule import Schedule

def generate_debug_reports(schedule: Schedule, components: List[Any]) -> str:
    """Generate all debug reports from components using the solved schedule.
    
    Args:
        schedule: The solved schedule to generate reports for
        components: List of SchedulerComponent instances applied to the schedule
        
    Returns:
        str: Combined debug reports from all components, grouped by Optimizations and Constraints
    """
    # Collect and separate by optimization vs constraint components
    optimization_summaries = []
    optimization_reports = []
    constraint_summaries = []
    constraint_reports = []
    
    for component in components:
        is_optimization = len(component._optimizers) > 0
        if is_optimization:
            optimization_summaries.extend(component._debug_summaries)
            optimization_reports.extend(component._debug_reports)
        else:
            constraint_summaries.extend(component._debug_summaries)
            constraint_reports.extend(component._debug_reports)
    
    if not optimization_reports and not constraint_reports and not optimization_summaries and not constraint_summaries:
        return "No debug reports available."
    
    report_sections = []
    
    # Build Executive Summary Block
    summary_sections = []
    if optimization_summaries or constraint_summaries:
        summary_sections.append("EXECUTIVE SUMMARY")
        score = schedule.solver.ObjectiveValue() if schedule.has_solution else "N/A"
        summary_sections.append(f"Schedule with score of {score:,.0f} generated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_sections.append("=" * 60)
        
        if optimization_summaries:
            summary_sections.append("OPTIMIZATIONS:")
            summary_sections.append("-" * 20)
            for debug_summary in optimization_summaries:
                summary_text = debug_summary(schedule)
                if summary_text:
                    summary_sections.append(f"[{debug_summary.component_name}]")
                    summary_sections.append(summary_text)
                    summary_sections.append("")
            summary_sections.append("-" * 60)
        
        if constraint_summaries:
            summary_sections.append("CONSTRAINTS & PROCESSORS:")
            summary_sections.append("-" * 20)
            for debug_summary in constraint_summaries:
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
    
    if optimization_reports:
        report_sections.append("OPTIMIZATION REPORTS")
        report_sections.append("=" * 40)
        report_sections.append("")
        for debug_report in optimization_reports:
            report_sections.append(f"Component: {debug_report.component_name}")
            report_sections.append("-" * 40)
            report_sections.append(debug_report(schedule))
            report_sections.append("")
            report_sections.append("")
            
    if constraint_reports:
        report_sections.append("CONSTRAINT & PROCESSOR REPORTS")
        report_sections.append("=" * 40)
        report_sections.append("")
        for debug_report in constraint_reports:
            report_sections.append(f"Component: {debug_report.component_name}")
            report_sections.append("-" * 40)
            report_sections.append(debug_report(schedule))
            report_sections.append("")
            report_sections.append("")
        
    # Append summary block again at the end
    if optimization_summaries or constraint_summaries:
        report_sections.append("")
        report_sections.extend(summary_sections)
    
    return "\n".join(report_sections)


def write_volleyball_debug_files(schedule: Schedule, base_dir: pathlib.Path, creator: Optional[Any] = None):
    """Write volleyball schedule and debug reports to files.
    
    This function handles two cases:
    1. If a ScheduleCreator (or similar object containing .components) is provided,
       it generates detailed debug reports from components.
    2. If no creator is provided, it generates a simple report with basic stats.
    
    Args:
        schedule: The solved schedule
        base_dir: The base directory to write files to (should contain 'scratch' subdirectory)
        creator: Optional schedule creator/object containing components for detailed debug reports
    """
    # Get the human-readable schedule
    debug_schedule = schedule.get_volleyball_debug_schedule()
    
    # Ensure the scratch directory exists
    scratch_dir = base_dir / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    
    # Write schedule to file with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    schedule_filename = f"last_volleyball_schedule {timestamp}.txt"
    report_filename = f"last_volleyball_debug_reports {timestamp}.txt"
    
    output_file = scratch_dir / schedule_filename
    with open(output_file, 'w') as f:
        f.write("VOLLEYBALL SCHEDULE DEBUG OUTPUT\n")
        f.write("="*50 + "\n")
        f.write(debug_schedule)
    
    # Generate and write debug reports
    debug_report_file = scratch_dir / report_filename
    report_content = ""
    if creator and hasattr(creator, 'components'):
        # Case 1: Detailed report using the refactored function
        report_content = generate_debug_reports(schedule, creator.components)
    else:
        # Case 2: Simple report with basic stats
        report_lines = []
        report_lines.append("SIMPLE SCHEDULE DEBUG REPORT")
        report_lines.append("="*50)
        report_lines.append(f"Generated at: {datetime.datetime.now()}")
        report_lines.append("Schedule type: Direct Schedule (no components)\n")
        
        game_report = schedule.get_game_report()
        team_report = schedule.get_team_report()
        
        report_lines.append("BASIC STATISTICS:")
        report_lines.append(f"- Total games: {len(game_report)}")
        report_lines.append(f"- Total teams: {len(team_report)}")
        if not game_report.empty:
            report_lines.append(f"- Date range: {game_report['date'].min()} to {game_report['date'].max()}")
            report_lines.append(f"- Weekends: {game_report['weekend_idx'].nunique()}\n")
        
        report_lines.append("TEAM STATISTICS:")
        report_lines.append(f"- Games per team (min/max/avg): {team_report['total_play'].min()}/{team_report['total_play'].max()}/{team_report['total_play'].mean():.1f}")
        report_lines.append(f"- Ref assignments per team (min/max/avg): {team_report['total_ref'].min()}/{team_report['total_ref'].max()}/{team_report['total_ref'].mean():.1f}\n")
        
        report_lines.append("GAMES PER WEEKEND:")
        if not game_report.empty:
            for weekend in sorted(game_report['weekend_idx'].unique()):
                weekend_games = game_report[game_report['weekend_idx'] == weekend]
                report_lines.append(f"- Weekend {weekend}: {len(weekend_games)} games")
        report_content = "\n".join(report_lines)

    with open(debug_report_file, 'w') as f:
        f.write(report_content)

    print(f"\nSchedule written to: {output_file}")
    print(f"Debug reports written to: {debug_report_file}")
