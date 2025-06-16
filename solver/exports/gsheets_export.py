import os
import yaml
from gspread_pandas import Spread, Client
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Any
import pandas as pd


def get_auth_token_path():
    """Get the path to the Google Sheets authentication token."""
    token_file_name = 'stonewall-volleyball-scheduler-gsheets-auth-token.json'
    # Path relative to project root (where the script is executed from)
    return os.path.join('auth', token_file_name)


def get_sheets_config():
    """Load the Google Sheets configuration from YAML."""
    config_file_name = 'gsheets_config.yaml'
    # Path relative to project root (where the script is executed from)
    config_path = os.path.join('auth', config_file_name)
    with open(config_path, 'r') as config_file:
        return yaml.safe_load(config_file)


def get_team_name_mapping():
    """Create a mapping from team index to team name using gsheets_config.yaml."""
    config = get_sheets_config()
    team_names = config.get('team_names', {})
    
    team_mapping = {}
    team_idx = 0
    
    # Map teams in order: division_1, division_2, division_3
    for div_name in ['division_1', 'division_2', 'division_3']:
        if div_name in team_names:
            for team_name in team_names[div_name]:
                team_mapping[team_idx] = team_name
                team_idx += 1
    
    return team_mapping


def format_schedule_as_csv(schedule):
    """Format the schedule in the CSV format matching the example.
    
    Args:
        schedule: The solved schedule object
        
    Returns:
        list: List of lists representing CSV rows
    """
    game_report = schedule.get_game_report()
    team_mapping = get_team_name_mapping()
    
    # Group by weekend and time
    csv_data = []
    
    # Get unique weekends and sort them
    weekends = sorted(game_report['weekend_idx'].unique())
    
    for weekend_idx in weekends:
        weekend_games = game_report[game_report['weekend_idx'] == weekend_idx]
        
        # Get unique times for this weekend and sort them
        times = sorted(weekend_games['time'].unique())
        
        # Create header row
        header_row = ['Time', 'Court 1 Team 1', 'Court 1 Team 2', 'Up Ref', 'Line Ref',
                      'Court 2 Team 1', 'Court 2 Team 2', 'Up Ref', 'Line Ref',
                      'Court 3 Team 1', 'Court 3 Team 2', 'Up Ref', 'Line Ref',
                      'Court 4 Team 1', 'Court 4 Team 2', 'Up Ref', 'Line Ref']
        csv_data.append(header_row)
        
        for time in times:
            time_games = weekend_games[weekend_games['time'] == time]
            
            # Convert time to display format (e.g., "12:00" -> "12pm")
            time_str = format_time_display(time)
            
            # Initialize row with time
            row = [time_str]
            
            # Get games by location (court)
            courts = sorted(time_games['location'].unique())
            
            # Fill in up to 4 courts
            for court_idx in range(4):
                if court_idx < len(courts):
                    court_games = time_games[time_games['location'] == courts[court_idx]]
                    if len(court_games) > 0:
                        game = court_games.iloc[0]  # Should only be one game per court per time
                        
                        # Get team names
                        team1_name = team_mapping.get(game['team1'], f"Team {game['team1']}")
                        team2_name = team_mapping.get(game['team2'], f"Team {game['team2']}")
                        ref_name = team_mapping.get(game['ref'], f"Team {game['ref']}")
                        
                        # Add team1, team2, up_ref, line_ref (using same ref for both for now)
                        row.extend([team1_name, team2_name, ref_name, ref_name])
                    else:
                        row.extend(['NO PLAY', 'NO PLAY', 'NO PLAY', 'NO PLAY'])
                else:
                    row.extend(['NO PLAY', 'NO PLAY', 'NO PLAY', 'NO PLAY'])
            
            csv_data.append(row)
        
        # Add blank row between weekends
        csv_data.append([''] * len(header_row))
    
    return csv_data


def format_time_display(time_obj):
    """Convert time object to display format (e.g., "12:00" -> "12pm")."""
    if hasattr(time_obj, 'hour'):
        hour = time_obj.hour
    else:
        # Try to parse string time
        try:
            if ':' in str(time_obj):
                hour = int(str(time_obj).split(':')[0])
            else:
                hour = int(str(time_obj))
        except:
            return str(time_obj)
    
    if hour == 12:
        return "12pm"
    elif hour > 12:
        return f"{hour - 12}pm"
    else:
        return f"{hour}pm"


def get_gspread_sheet():
    """Create and return a Google Sheets client."""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(get_auth_token_path(), scope)
    client = Client(creds=creds)
    config = get_sheets_config()
    sheet = Spread(config['sheet_url'], client=client)
    return sheet


def export_schedule_to_sheets(schedule, creator):
    """Export the schedule and debug reports to Google Sheets.
    
    Args:
        schedule: The solved schedule object
        creator: The schedule creator object with debug reports
    """
    config = get_sheets_config()
    
    # Export the schedule in CSV format
    export_schedule_csv_format(schedule, config['schedule_tab'])
    
    # Export the debug reports
    debug_reports = creator.generate_debug_reports(schedule)
    export_debug_reports(debug_reports, config['debug_report_tab'])
    
    # Also export the structured game report if there's a schedule tab
    # (for easier analysis/filtering)
    sheet = get_gspread_sheet()
    worksheet_names = [ws.title for ws in sheet.sheets]
    if 'schedule' in worksheet_names:
        export_game_report_table(schedule, 'schedule')
    
    print(f"✅ Schedule exported to Google Sheets: {config['sheet_url']}")
    print(f"   - Schedule data in tab: '{config['schedule_tab']}'")
    print(f"   - Debug reports in tab: '{config['debug_report_tab']}'")
    if 'schedule' in worksheet_names:
        print(f"   - Structured game report in tab: 'schedule'")


def export_schedule_csv_format(schedule, tab_name):
    """Export the schedule data in CSV format to a specific Google Sheets tab.
    
    Args:
        schedule: The solved schedule object
        tab_name: The name of the Google Sheets tab to export to
    """
    # Get the CSV formatted data
    csv_data = format_schedule_as_csv(schedule)
    
    # Get the sheet and set data
    sheet = get_gspread_sheet()
    sheet.open_sheet(tab_name)
    worksheet = sheet.sheet
    
    # Clear existing content first
    worksheet.clear()
    
    # Update the entire range at once
    if csv_data:
        rows = len(csv_data)
        cols = len(csv_data[0])
        
        # Convert column number to letter (A, B, C, ..., P for 16 columns)
        end_col = chr(ord('A') + cols - 1)
        cell_range = f'A1:{end_col}{rows}'
        worksheet.update(cell_range, csv_data)


def export_schedule_data(schedule, tab_name):
    """Export the schedule data to a specific Google Sheets tab.
    
    Args:
        schedule: The solved schedule object
        tab_name: The name of the Google Sheets tab to export to
    """
    # Get the volleyball debug schedule (human-readable format)
    volleyball_schedule = schedule.get_volleyball_debug_schedule()
    
    # Convert to list of lines for Google Sheets
    schedule_lines = volleyball_schedule.split('\n')
    
    # Get the sheet and set data
    sheet = get_gspread_sheet()
    sheet.open_sheet(tab_name)
    worksheet = sheet.sheet
    
    # Clear existing content first
    worksheet.clear()
    
    # Set the schedule data (one line per row, single column)
    if schedule_lines:
        cell_range = f'A1:A{len(schedule_lines)}'
        cell_list = worksheet.range(cell_range)
        
        for cell_idx, cell in enumerate(cell_list):
            cell.value = schedule_lines[cell_idx]
        
        worksheet.update_cells(cell_list)


def export_debug_reports(debug_reports, tab_name):
    """Export the debug reports to a specific Google Sheets tab.
    
    Args:
        debug_reports: The debug reports string
        tab_name: The name of the Google Sheets tab to export to
    """
    # Split debug reports into lines
    debug_lines = debug_reports.split('\n')
    
    # Get the sheet and set data
    sheet = get_gspread_sheet()
    sheet.open_sheet(tab_name)
    worksheet = sheet.sheet
    
    # Clear existing content first
    worksheet.clear()
    
    # Set the debug data (one line per row, single column)
    if debug_lines:
        cell_range = f'A1:A{len(debug_lines)}'
        cell_list = worksheet.range(cell_range)
        
        for cell_idx, cell in enumerate(cell_list):
            cell.value = debug_lines[cell_idx]
        
        worksheet.update_cells(cell_list)


def export_game_report_table(schedule, tab_name):
    """Export the game report as a structured table to Google Sheets.
    
    Args:
        schedule: The solved schedule object
        tab_name: The name of the Google Sheets tab to export to
    """
    game_report = schedule.get_game_report().copy()
    
    # Convert any time objects to strings for JSON serialization
    for col in game_report.columns:
        if game_report[col].dtype == 'object':
            # Check if column contains time objects
            sample_val = game_report[col].iloc[0]
            if hasattr(sample_val, 'strftime'):  # It's a time-like object
                game_report[col] = game_report[col].astype(str)
    
    # Get the sheet and set data
    sheet = get_gspread_sheet()
    sheet.open_sheet(tab_name)
    worksheet = sheet.sheet
    
    # Clear existing content first
    worksheet.clear()
    
    # Convert DataFrame to list of lists (including headers)
    data_list = [game_report.columns.tolist()] + game_report.values.tolist()
    
    if data_list:
        rows = len(data_list)
        cols = len(data_list[0])
        
        # Update the entire range at once
        cell_range = f'A1:{chr(ord("A") + cols - 1)}{rows}'
        worksheet.update(cell_range, data_list)


def test_sheets_connection():
    """Test the Google Sheets connection and configuration.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        config = get_sheets_config()
        sheet = get_gspread_sheet()
        
        # Try to access the sheet - use the correct API
        # The Spread object has a method to get worksheets
        worksheets = sheet.sheets
        worksheet_names = [ws.title for ws in worksheets]
        
        print(f"✅ Google Sheets connection successful!")
        print(f"   Sheet URL: {config['sheet_url']}")
        print(f"   Available tabs: {worksheet_names}")
        print(f"   Schedule tab: '{config['schedule_tab']}' {'✅' if config['schedule_tab'] in worksheet_names else '❌ (missing)'}")
        print(f"   Debug tab: '{config['debug_report_tab']}' {'✅' if config['debug_report_tab'] in worksheet_names else '❌ (missing)'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Sheets connection failed: {e}")
        return False


if __name__ == '__main__':
    # Test the connection when run directly
    test_sheets_connection() 