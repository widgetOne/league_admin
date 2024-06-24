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


def get_gspread_client():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = (ServiceAccountCredentials
             .from_json_keyfile_name(get_auth_token_path(), scope))
    client = Client(creds=creds)
    return client


def get_team_names():
    config = get_sheets_config()
    print(config)


if __name__ == '__main__':
    print(get_team_names())
