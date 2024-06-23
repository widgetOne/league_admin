import os


def get_auth_token():
    token_file_name = 'stonewall-volleyball-scheduler-gsheets-auth-token.json'
    token_path = os.path.join('../auth', token_file_name)

    with open(token_path, 'r') as token_file:
        return token_file.read()


if __name__ == '__main__':
    print(get_auth_token())
