import pathlib
from datetime import datetime
from .. import Facilities
from ..exports.gsheets_export import get_gspread_sheet, get_sheets_config, get_team_name_mapping, get_team_counts_from_sheets
from .make_league_apps_schedule_2025 import read_schedule_from_sheets, parse_schedule_data, parse_schedule_to_league_apps_format, export_league_apps_schedule


def make_league_apps_schedule():
    """Main function to generate League Apps schedule format."""
    print("Generating League Apps schedule for the season...")
    
    # Load facilities to get dates
    current_dir = pathlib.Path(__file__).parent.parent
    facilities_yaml_path = current_dir / "facilities" / "configs" / "volleyball.yaml"
    
    from .. import Facilities
    team_counts = get_team_counts_from_sheets()
    facilities = Facilities.from_yaml(str(facilities_yaml_path), team_counts=team_counts)
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
