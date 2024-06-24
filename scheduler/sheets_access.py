import os
import yaml


def get_auth_token():
    token_file_name = 'stonewall-volleyball-scheduler-gsheets-auth-token.json'
    token_path = os.path.join('../auth', token_file_name)
    with open(token_path, 'r') as token_file:
        return token_file.read()


def get_sheet_config():
    config_file_name = 'google_sheets_vball_config.yaml'


def get_sheets_config():
    config_file_name = 'gsheets_config.yaml'
    config_path = os.path.join('../auth', config_file_name)
    with open(config_path, 'r') as coonfig_file:
        return coonfig_file.read()


if __name__ == '__main__':
    print(get_sheets_config())
