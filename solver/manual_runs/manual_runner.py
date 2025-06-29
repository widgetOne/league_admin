from typing import Optional, Set, Any, Iterable, Tuple
import pathlib
import datetime
from ortools.sat.python import cp_model
from ..facilities import Facilities
from ..schedule import Schedule
from ..schedule_creator import ScheduleCreator
from ..schedule_component import SchedulerComponent

def make_schedule(facilities: Facilities, components: Iterable[SchedulerComponent]) -> Tuple[Schedule, ScheduleCreator]:
    """Make a scheduling optimization with the given facilities and constraints.
    
    Args:
        facilities: The Facilities object containing all facility constraints
        components: Iterable of SchedulerComponents to apply to the schedule
        
    Returns:
        Tuple[Schedule, ScheduleCreator]: The solved schedule and the creator (for debug reports)
    """
    # Create schedule creator
    creator = ScheduleCreator(facilities, components=components)
    
    # Create and configure the schedule
    schedule = creator.create_schedule()
    
    return schedule, creator


def make_schedule_and_debug_files(
    facilities: Facilities,
    base_dir: pathlib.Path,
    components: Optional[Iterable[SchedulerComponent]] = None
) -> Tuple[Schedule, Optional[ScheduleCreator]]:
    """
    Generates a schedule, writes debug files, and returns the schedule and creator.

    This function handles two modes:
    1. If components are provided, it uses ScheduleCreator for a full build.
    2. If no components are provided, it does a direct, simple schedule generation.
    
    Args:
        facilities: The Facilities object with all constraints.
        base_dir: The base directory for writing debug files.
        components: Optional list of components for a complex build.
        
    Returns:
        A tuple containing the solved Schedule and the ScheduleCreator (if used).
    """
    creator = None
    if components:
        # Mode 1: Use ScheduleCreator with components
        print("Running schedule generation with components...")
        schedule, creator = make_schedule(facilities, components)
        write_volleyball_debug_files(schedule, base_dir, creator=creator)
    else:
        # Mode 2: Direct schedule generation
        print("Running direct schedule generation (no components)...")
        model = cp_model.CpModel()
        schedule = Schedule(facilities, model)
        schedule.solve()
        write_volleyball_debug_files(schedule, base_dir, creator=None)

    print("\n✅ Top-level schedule generation complete!")
    return schedule, creator


def write_volleyball_debug_files(schedule: Schedule, base_dir: pathlib.Path, creator: Optional[ScheduleCreator] = None):
    """Write volleyball schedule and debug reports to files.
    
    This function handles two cases:
    1. If a ScheduleCreator is provided, it generates detailed debug reports from components.
    2. If no ScheduleCreator is provided, it generates a simple report with basic stats.
    
    Args:
        schedule: The solved schedule
        base_dir: The base directory to write files to (should contain 'scratch' subdirectory)
        creator: Optional schedule creator for detailed debug reports
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
    if creator:
        # Case 1: Detailed report from ScheduleCreator
        report_content = creator.generate_debug_reports(schedule)
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