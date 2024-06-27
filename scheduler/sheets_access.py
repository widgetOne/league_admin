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
    teams = get_gspread_range('team names', 'A2:C11')
    return teams


def set_formatted_schedule_to_sheet(schedule_list_list):
    sheet = get_gspread_sheet()
    sheet.open_sheet('robot_schedule_upload__dont_edit')  # 'v2 schedule', 'robot_schedule_upload__dont_edit'
    col_count = len(schedule_list_list[0])
    end_col_options = {17: "Q", 21: "U"}
    edit_me_worksheet = sheet.sheet
    cell_range = f'A1:{end_col_options[col_count]}{len(schedule_list_list)}'
    cell_list = edit_me_worksheet.range(cell_range)
    schedule_list = sum(schedule_list_list, [])
    for cell_idx, cell in enumerate(cell_list):
        cell.value = schedule_list[cell_idx]
    edit_me_worksheet.update_cells(cell_list)


def set_schedule_audit_sheet(audit_report):
    audit_lines = audit_report.split('\n')
    sheet = get_gspread_sheet()
    sheet.open_sheet('uploaded_schedule_audit_report')  #  'v2 schedule audit', 'uploaded_schedule_audit_report'
    audit_worksheet = sheet.sheet
    cell_range = f'A1:A{len(audit_lines)}'
    cell_list = audit_worksheet.range(cell_range)
    for cell_idx, cell in enumerate(cell_list):
        cell.value = audit_lines[cell_idx]
    audit_worksheet.update_cells(cell_list)


def set_league_apps_csv_sheet(schedule_csv_data):
    # TODO: Time to refactor cell pushing logic to a helper function
    sheet = get_gspread_sheet()
    sheet.open_sheet('league_apps_csv')
    csv_worksheet = sheet.sheet
    cell_range = f'A1:J{len(schedule_csv_data)}'
    cell_data = sum(schedule_csv_data, [])
    cell_list = csv_worksheet.range(cell_range)
    for cell_idx, cell in enumerate(cell_list):
        cell.value = cell_data[cell_idx]
    csv_worksheet.update_cells(cell_list)


def set_division_teamwise_schedules(div_schs, sheet_name):
    sheet = get_gspread_sheet()
    sheet.open_sheet(sheet_name)
    max_rows = max(len(sch) for sch in div_schs)
    col_count = len(div_schs)
    end_col_options = {8: "H", 10: "J"}  # turn this into a real function
    div_worksheet = sheet.sheet
    offset_rows = 3
    cell_range = f'A{offset_rows}:{end_col_options[col_count]}{offset_rows+max_rows-1}'
    cell_list = div_worksheet.range(cell_range)
    div_schedules_t = list(map(list, zip(*div_schs)))
    div_schedule_cell_list = sum(div_schedules_t, [])
    for cell_idx, cell in enumerate(cell_list):
        cell.value = div_schedule_cell_list[cell_idx]
    div_worksheet.update_cells(cell_list)


def set_teamwise_schedules_to_sheet(teamwise_schedules):
    sheet_names = ['Bumpers', 'Setters', 'Spikers']
    for div_schs, sheet_name in zip(teamwise_schedules, sheet_names):
        set_division_teamwise_schedules(div_schs, sheet_name)


if __name__ == '__main__':
    print(set_formatted_schedule_to_sheet())
