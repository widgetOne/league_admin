from typing import Optional
import pathlib
import datetime
from .schedule import Schedule
from .schedule_creator import ScheduleCreator

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
