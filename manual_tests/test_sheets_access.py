"""
Manual test: verify that the Google Sheets config and auth token are working.

Run from the project root:
    python -m manual_tests.test_sheets_access

Or from the manual_tests/ directory:
    cd manual_tests && python test_sheets_access.py

Checks:
  1. gsheets_config.yaml has a sheet_url
  2. The service-account token file exists
  3. We can authenticate and open the sheet (confirms edit-level access)
  4. Prints the spreadsheet title
"""

import os
import sys
import re

# ---------------------------------------------------------------------------
# Path setup – mirror the relative-path logic used in scheduler/sheets_access.py
# but resolve from *this* file's location so the test works regardless of cwd.
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
_AUTH_DIR = os.path.join(_PROJECT_ROOT, 'auth')

# Add the scheduler dir to sys.path so we *could* import sheets_access in the
# future, but for this smoke test we intentionally duplicate the minimal logic
# to keep the test self-contained and easy to debug.
sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'scheduler'))


def _load_config():
    """Load gsheets_config.yaml from the auth directory."""
    import yaml
    config_path = os.path.join(_AUTH_DIR, 'gsheets_config.yaml')
    if not os.path.isfile(config_path):
        sys.exit(f"FAIL: config file not found at {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    print(f"  config loaded from {config_path}")
    return config


def _check_sheet_url(config):
    """Verify a sheet_url key exists and looks plausible."""
    url = config.get('sheet_url')
    if not url:
        sys.exit("FAIL: 'sheet_url' is missing or empty in config")
    if 'docs.google.com/spreadsheets' not in url:
        sys.exit(f"FAIL: sheet_url doesn't look like a Google Sheets URL: {url}")
    # Extract the spreadsheet ID for display
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    sheet_id = match.group(1) if match else '(could not parse)'
    print(f"  sheet_url present  – spreadsheet ID: {sheet_id}")
    return url


def _check_token_file():
    """Verify the service-account JSON token exists."""
    token_filename = 'stonewall-volleyball-scheduler-gsheets-auth-token.json'
    token_path = os.path.join(_AUTH_DIR, token_filename)
    if not os.path.isfile(token_path):
        sys.exit(f"FAIL: token file not found at {token_path}")
    print(f"  token file exists  – {token_path}")
    return token_path


def _connect_and_print_title(sheet_url, token_path):
    """
    Open the spreadsheet using the same libraries as sheets_access.py
    (gspread_pandas + oauth2client) and print its title.
    """
    from gspread_pandas import Spread, Client
    from oauth2client.service_account import ServiceAccountCredentials

    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(token_path, scope)
    client = Client(creds=creds)

    spread = Spread(sheet_url, client=client)
    title = spread.spread.title
    print(f"  spreadsheet title  – \"{title}\"")

    # Confirm write-capable scope by listing worksheets (requires at least
    # reader access; the drive scope we request implies editor if the service
    # account has been granted it on the sheet).
    ws_names = [ws.title for ws in spread.spread.worksheets()]
    print(f"  worksheets ({len(ws_names)})    – {', '.join(ws_names[:6])}"
          + (" …" if len(ws_names) > 6 else ""))


def main():
    print("\n=== Manual Test: Google Sheets Access ===\n")

    print("[1/3] Loading config …")
    config = _load_config()

    print("[2/3] Checking local files …")
    sheet_url = _check_sheet_url(config)
    token_path = _check_token_file()

    print("[3/3] Connecting to Google Sheets …")
    _connect_and_print_title(sheet_url, token_path)

    print("\n✅  All checks passed.\n")


if __name__ == '__main__':
    main()
