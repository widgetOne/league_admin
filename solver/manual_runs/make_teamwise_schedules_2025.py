import pathlib
from datetime import datetime
from .. import Facilities
from ..exports.gsheets_export import get_gspread_sheet, get_sheets_config, get_team_name_mapping
from .make_league_apps_schedule_2025 import read_schedule_from_sheets, parse_schedule_data



def parse_schedule_for_teamwise(schedule_data, dates):
    """Parse the schedule data for teamwise schedules (including both up and line refs).
    
    Args:
        schedule_data: Raw schedule data from Google Sheets
        dates: List of dates from facilities config
        
    Returns:
        dict: Structured schedule data by team
    """
    # Use the centralized parsing function
    parsed_games = parse_schedule_data(schedule_data, dates)
    
    team_mapping = get_team_name_mapping()
    # Create reverse mapping (team name -> team index)
    name_to_idx = {name: idx for idx, name in team_mapping.items()}
    
    # Initialize team schedules
    team_schedules = {idx: [] for idx in range(len(team_mapping))}
    
    for game in parsed_games:
        team1_name = game['team1']
        team2_name = game['team2']
        up_ref_name = game['up_ref']
        line_ref_name = game['line_ref']
        
        # Add playing entries for team1 and team2
        if team1_name in name_to_idx:
            team_idx = name_to_idx[team1_name]
            team_schedules[team_idx].append({
                'date': game['date'],
                'time': game['time'],
                'activity': 'Play',
                'court': game['court'],
                'opponent': team2_name
            })
            
        if team2_name in name_to_idx:
            team_idx = name_to_idx[team2_name]
            team_schedules[team_idx].append({
                'date': game['date'],
                'time': game['time'],
                'activity': 'Play',
                'court': game['court'],
                'opponent': team1_name
            })
        
        # Add reffing entry for up ref
        if up_ref_name in name_to_idx:
            team_idx = name_to_idx[up_ref_name]
            team_schedules[team_idx].append({
                'date': game['date'],
                'time': game['time'],
                'activity': 'Up Ref',
                'court': game['court'],
                'opponent': None
            })
        
        # Add reffing entry for line ref
        if line_ref_name in name_to_idx:
            team_idx = name_to_idx[line_ref_name]
            team_schedules[team_idx].append({
                'date': game['date'],
                'time': game['time'],
                'activity': 'Line Ref',
                'court': game['court'],
                'opponent': None
            })
    
    return team_schedules


def format_team_schedule(team_schedule, dates):
    """Format a single team's schedule for display.
    
    Args:
        team_schedule: List of schedule entries for one team
        dates: List of all dates in the season
        
    Returns:
        list: Formatted schedule lines
    """
    # Group by date
    schedule_by_date = {}
    for entry in team_schedule:
        date = entry['date']
        if date not in schedule_by_date:
            schedule_by_date[date] = []
        schedule_by_date[date].append(entry)
    
    formatted_lines = []
    
    for i, date in enumerate(dates):
        formatted_lines.append(date)
        
        if date in schedule_by_date:
            # Sort by time
            date_entries = sorted(schedule_by_date[date], key=lambda x: x['time'])
            
            for entry in date_entries:
                if entry['activity'] == 'Play':
                    line = f"{entry['time']} - Play Court {entry['court']} vs {entry['opponent']}"
                elif entry['activity'] == 'Up Ref':
                    line = f"{entry['time']} - Up Ref Court {entry['court']}"
                elif entry['activity'] == 'Line Ref':
                    line = f"{entry['time']} - Line Ref Court {entry['court']}"
                else:  # Fallback for any other activity type
                    line = f"{entry['time']} - {entry['activity']} Court {entry['court']}"
                formatted_lines.append(line)
        else:
            formatted_lines.append("Bye week")
        
        # Add empty line between dates, but not after the last date
        if i < len(dates) - 1:
            formatted_lines.append("")
    
    return formatted_lines


def export_teamwise_schedules(team_schedules, dates):
    """Export individual team schedules to Google Sheets in side-by-side columns.
    
    Args:
        team_schedules: Dictionary of team schedules
        dates: List of dates from facilities config
    """
    team_mapping = get_team_name_mapping()
    sheet = get_gspread_sheet()
    
    # Use a single sheet for all team schedules
    tab_name = "teamwise_schedules"
    
    try:
        # Try to open existing sheet
        sheet.open_sheet(tab_name)
    except:
        # If it doesn't exist, we'll use the scratch tab or create content in existing tab
        try:
            sheet.open_sheet("scratch")
            tab_name = "scratch"
        except:
            print("⚠️  Could not access teamwise schedules sheet")
            return
    
    worksheet = sheet.sheet
    
    # Clear existing content
    worksheet.clear()
    
    # Build side-by-side schedule data
    # First, format all team schedules
    all_team_schedules = []
    team_names = []
    
    for team_idx in sorted(team_mapping.keys()):
        team_name = team_mapping[team_idx]
        team_schedule = team_schedules.get(team_idx, [])
        
        # Format the team's schedule
        formatted_schedule = format_team_schedule(team_schedule, dates)
        
        # Add team name as header
        team_column = [team_name, ""] + formatted_schedule
        all_team_schedules.append(team_column)
        team_names.append(team_name)
    
    # Find the maximum length to pad all columns to the same height
    max_length = max(len(schedule) for schedule in all_team_schedules) if all_team_schedules else 0
    
    # Pad all columns to the same length
    for schedule in all_team_schedules:
        while len(schedule) < max_length:
            schedule.append("")
    
    # Transpose the data so each team is a column
    # Create rows where each row contains one entry from each team's schedule
    schedule_data = []
    for row_idx in range(max_length):
        row = []
        for team_schedule in all_team_schedules:
            row.append(team_schedule[row_idx])
        schedule_data.append(row)
    
    # Update the sheet
    if schedule_data:
        rows = len(schedule_data)
        cols = len(schedule_data[0])
        
        # Convert column number to letter
        end_col = chr(ord('A') + cols - 1) if cols <= 26 else f"A{chr(ord('A') + cols - 27)}"
        cell_range = f'A1:{end_col}{rows}'
        worksheet.update(cell_range, schedule_data)
    
    print(f"✅ Exported all team schedules to '{tab_name}' tab in {len(team_names)} columns")


def make_teamwise_schedules():
    """Main function to generate teamwise schedules."""
    print("Generating teamwise schedules for 2025...")
    
    # Load facilities to get dates
    current_dir = pathlib.Path(__file__).parent.parent
    facilities_yaml_path = current_dir / "facilities" / "configs" / "volleyball_2025.yaml"
    facilities = Facilities.from_yaml(str(facilities_yaml_path))
    dates = facilities.dates
    
    print(f"Loaded {len(dates)} dates: {dates}")
    
    # Read schedule from Google Sheets
    print("Reading schedule from Google Sheets...")
    schedule_data = read_schedule_from_sheets()
    print(f"Read {len(schedule_data)} rows from Google Sheets")
    
    # Parse the schedule data
    print("Parsing schedule data...")
    team_schedules = parse_schedule_for_teamwise(schedule_data, dates)
    
    # Count activities per team
    team_mapping = get_team_name_mapping()
    for team_idx, team_name in team_mapping.items():
        activities = len(team_schedules.get(team_idx, []))
        print(f"  {team_name}: {activities} activities")
    
    # Export teamwise schedules
    print("Exporting teamwise schedules to Google Sheets...")
    export_teamwise_schedules(team_schedules, dates)
    
    print("✅ Teamwise schedules generated successfully!")


if __name__ == "__main__":
    make_teamwise_schedules() 