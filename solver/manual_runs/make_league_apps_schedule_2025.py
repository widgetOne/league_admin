import pathlib
from datetime import datetime
from .. import Facilities
from ..exports.gsheets_export import get_gspread_sheet, get_sheets_config, get_team_name_mapping


def read_schedule_from_sheets():
    """Read the raw schedule data from Google Sheets cached_schedule_source tab."""
    sheet = get_gspread_sheet()
    config = get_sheets_config()
    
    # Use cached_schedule_source tab instead of schedule_tab
    tab_name = config.get('cached_schedule_source', 'Intermediate Schedule')
    sheet.open_sheet(tab_name)
    worksheet = sheet.sheet
    all_values = worksheet.get_all_values()
    
    # Skip header row and empty rows
    schedule_data = []
    for row in all_values[1:]:  # Skip header
        if row and any(cell.strip() for cell in row):  # Include rows with any non-empty data
            schedule_data.append(row)
    
    return schedule_data


def parse_schedule_data(schedule_data, dates):
    """Parse raw schedule data into a standardized format.
    
    Args:
        schedule_data: Raw schedule data from Google Sheets
        dates: List of dates for the schedule
        
    Returns:
        list: List of dictionaries with game information:
        [
            {
                'date': '6/22/2025',
                'time': '12pm',
                'court': 1,
                'team1': 'Team A',
                'team2': 'Team B', 
                'up_ref': 'Team C',
                'line_ref': 'Team D'
            },
            ...
        ]
    """
    parsed_games = []
    current_date = None
    date_idx = 0
    
    # Start with the first date
    if dates:
        current_date = dates[0]
    
    for i, row in enumerate(schedule_data):
        if not row:
            continue
            
        time = row[0].strip() if row[0] else ''
        
        # Check if this is a header row (indicates end of current date section)
        if time == 'Time':
            # Move to next date for the upcoming section
            date_idx += 1
            if date_idx < len(dates):
                current_date = dates[date_idx]
            continue
            
        # Skip empty time cells
        if not time:
            continue
            
        # Process each court (4 courts, 4 columns each: Team1, Team2, Up Ref, Line Ref)
        for court_idx in range(4):
            base_col = 1 + (court_idx * 4)  # Starting column for this court
            
            if base_col + 3 >= len(row):
                continue
                
            team1_name = row[base_col].strip() if len(row) > base_col else ''
            team2_name = row[base_col + 1].strip() if len(row) > base_col + 1 else ''
            up_ref_name = row[base_col + 2].strip() if len(row) > base_col + 2 else ''
            line_ref_name = row[base_col + 3].strip() if len(row) > base_col + 3 else ''
            
            if team1_name == 'NO PLAY' or team1_name == '':
                continue
                
            court_num = court_idx + 1
            
            game_info = {
                'date': current_date,
                'time': time,
                'court': court_num,
                'team1': team1_name,
                'team2': team2_name,
                'up_ref': up_ref_name,
                'line_ref': line_ref_name
            }
            
            parsed_games.append(game_info)
    
    return parsed_games


def parse_schedule_to_league_apps_format(schedule_data, dates):
    """Parse schedule data from Google Sheets into League Apps format.
    
    Args:
        schedule_data: Raw schedule data from Google Sheets
        dates: List of dates for the schedule
        
    Returns:
        list: List of dictionaries in League Apps format
    """
    # Use the centralized parsing function
    parsed_games = parse_schedule_data(schedule_data, dates)
    
    league_apps_data = []
    
    for game in parsed_games:
        # Convert date format from MM/DD/YYYY to MM/DD/YYYY for League Apps
        formatted_date = format_date_for_league_apps(game['date'])
        
        # Convert time format (e.g., "12pm" -> "12:00")
        start_time = format_time_for_league_apps(game['time'])
        end_time = format_end_time_for_league_apps(game['time'])
        
        # Create League Apps format entry
        league_apps_entry = {
            'SUB_PROGRAM': '',  # Empty as shown in example
            'HOME_TEAM': game['team1'],
            'AWAY_TEAM': game['team2'],
            'DATE': formatted_date,
            'START_TIME': start_time,
            'END_TIME': end_time,
            'LOCATION': 'Highland Park',  # Default location
            'SUB_LOCATION': f'Court {game["court"]}',
            'TYPE': 'REGULAR_SEASON',
            'NOTES': f'Up Ref {game["up_ref"]}\nLine Ref {game["line_ref"]}'
        }
        
        league_apps_data.append(league_apps_entry)
    
    return league_apps_data


def format_date_for_league_apps(date_str):
    """Convert date from MM/DD/YYYY format to MM/DD/YYYY format for League Apps.
    
    Args:
        date_str: Date string in MM/DD/YYYY format
        
    Returns:
        str: Formatted date string for League Apps
    """
    # The date is already in the correct format, but let's ensure consistency
    try:
        # Parse and reformat to ensure MM/DD/YYYY format
        date_obj = datetime.strptime(date_str, '%m/%d/%Y')
        return date_obj.strftime('%m/%d/%Y')
    except:
        # If parsing fails, return as-is
        return date_str


def format_time_for_league_apps(time_str):
    """Convert time from display format to HH:MM format for League Apps.
    
    Args:
        time_str: Time string (e.g., "12pm", "1pm", "2pm")
        
    Returns:
        str: Time in HH:MM format (e.g., "12:00", "13:00")
    """
    try:
        # Remove 'pm' and convert to 24-hour format
        hour_str = time_str.replace('pm', '').strip()
        hour = int(hour_str)
        
        # Convert to 24-hour format (assuming all times are PM)
        if hour != 12:
            hour += 12
            
        return f"{hour:02d}:00"
    except:
        # If parsing fails, return a default
        return "12:00"


def format_end_time_for_league_apps(time_str):
    """Convert time to end time (start time + 1 hour) for League Apps.
    
    Args:
        time_str: Time string (e.g., "12pm", "1pm", "2pm")
        
    Returns:
        str: End time in HH:MM format (e.g., "13:00", "14:00")
    """
    try:
        # Remove 'pm' and convert to 24-hour format
        hour_str = time_str.replace('pm', '').strip()
        hour = int(hour_str)
        
        # Convert to 24-hour format (assuming all times are PM)
        if hour != 12:
            hour += 12
            
        # Add 1 hour for end time
        end_hour = hour + 1
        
        return f"{end_hour:02d}:00"
    except:
        # If parsing fails, return a default
        return "13:00"


def export_league_apps_schedule(league_apps_data):
    """Export League Apps schedule data to Google Sheets.
    
    Args:
        league_apps_data: List of dictionaries in League Apps format
    """
    sheet = get_gspread_sheet()
    tab_name = "league_apps_schedule"
    
    try:
        # Try to open existing sheet
        sheet.open_sheet(tab_name)
    except:
        # If it doesn't exist, create it or use an existing tab
        print(f"⚠️  Could not access '{tab_name}' tab. Using 'scratch' tab instead.")
        sheet.open_sheet("scratch")
        tab_name = "scratch"
    
    worksheet = sheet.sheet
    
    # Clear existing content
    worksheet.clear()
    
    # Prepare data for export
    if not league_apps_data:
        print("No league apps data to export")
        return
    
    # Create header row
    headers = ['SUB_PROGRAM', 'HOME_TEAM', 'AWAY_TEAM', 'DATE', 'START_TIME', 'END_TIME', 
               'LOCATION', 'SUB_LOCATION', 'TYPE', 'NOTES']
    
    # Convert data to list of lists
    export_data = [headers]
    
    for entry in league_apps_data:
        row = [
            entry['SUB_PROGRAM'],
            entry['HOME_TEAM'],
            entry['AWAY_TEAM'],
            entry['DATE'],
            entry['START_TIME'],
            entry['END_TIME'],
            entry['LOCATION'],
            entry['SUB_LOCATION'],
            entry['TYPE'],
            entry['NOTES']
        ]
        export_data.append(row)
    
    # Update the sheet
    if export_data:
        rows = len(export_data)
        cols = len(export_data[0])
        
        # Convert column number to letter
        end_col = chr(ord('A') + cols - 1)
        cell_range = f'A1:{end_col}{rows}'
        worksheet.update(cell_range, export_data)
        
        print(f"✅ Exported {len(league_apps_data)} games to '{tab_name}' tab in League Apps format")


def make_league_apps_schedule():
    """Main function to generate League Apps schedule format."""
    print("Generating League Apps schedule for 2025...")
    
    # Load facilities to get dates
    current_dir = pathlib.Path(__file__).parent.parent
    facilities_yaml_path = current_dir / "facilities" / "configs" / "volleyball_2025.yaml"
    
    from .. import Facilities
    facilities = Facilities.from_yaml(str(facilities_yaml_path))
    # Get the unique dates from the facilities config
    unique_dates = facilities.dates
    print(f"Loaded {len(unique_dates)} dates: {unique_dates}")

    
    # Read schedule from Google Sheets
    print("Reading schedule from Google Sheets...")
    schedule_data = read_schedule_from_sheets()
    print(f"Read {len(schedule_data)} rows from Google Sheets")
    
    # Parse schedule data into League Apps format
    print("Parsing schedule data into League Apps format...")
    league_apps_data = parse_schedule_to_league_apps_format(schedule_data, unique_dates)
    print(f"Parsed {len(league_apps_data)} games")
    
    # Export to Google Sheets
    print("Exporting League Apps schedule to Google Sheets...")
    export_league_apps_schedule(league_apps_data)
    
    print("✅ League Apps schedule generation complete!")


if __name__ == "__main__":
    make_league_apps_schedule() 