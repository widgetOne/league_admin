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
    
    # Export the schedule
    export_schedule_data(schedule, config['schedule_tab'])
    
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
    game_report = schedule.get_game_report()
    
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