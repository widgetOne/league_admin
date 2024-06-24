import os
import yaml
from gspread_pandas import Spread, Client
from oauth2client.service_account import ServiceAccountCredentials


def get_auth_token_path():
    token_file_name = 'stonewall-volleyball-scheduler-gsheets-auth-token.json'
    return os.path.join('../auth', token_file_name)


def get_sheets_config():
    config_file_name = 'gsheets_config.yaml'
    config_path = os.path.join('../auth', config_file_name)
    with open(config_path, 'r') as config_file:
        return yaml.safe_load(config_file)


def get_gspread_sheet():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = (ServiceAccountCredentials
             .from_json_keyfile_name(get_auth_token_path(), scope))
    client = Client(creds=creds)
    config = get_sheets_config()
    sheet = Spread(config['sheet_url'], client=client)
    return sheet


def get_gspread_range(worksheet_name, sheet_range):
    sheet = get_gspread_sheet()
    sheet.open_sheet(worksheet_name)
    worksheet = sheet.sheet
    return worksheet.get(sheet_range)


def get_team_names():
    config = get_sheets_config()
    teams = get_gspread_range('team names', 'A1:C11')
    print(teams)


if __name__ == '__main__':
    print(get_team_names())
