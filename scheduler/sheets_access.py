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


def get_team_names_data():
    teams = get_gspread_range('team names', 'A1:C11')
    return teams


def set_formatted_schedule_to_sheet(schedule_list_list):
    sheet = get_gspread_sheet()
    sheet.open_sheet('robot_schedule_upload__dont_edit')
    col_count = len(schedule_list_list[0])
    end_col_options = {17: "Q", 21: "U"}
    edit_me_worksheet = sheet.sheet
    cell_range = f'A1:{end_col_options[col_count]}{len(schedule_list_list)}'
    cell_list = edit_me_worksheet.range(cell_range)
    schedule_list = sum(schedule_list_list, [])
    for cell_idx, cell in enumerate(cell_list):
        cell.value = schedule_list[cell_idx]
    edit_me_worksheet.update_cells(cell_list)
    return


if __name__ == '__main__':
    print(set_formatted_schedule_to_sheet())
