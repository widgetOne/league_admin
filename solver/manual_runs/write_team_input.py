"""Write team names to the 'team_input' tab in Google Sheets."""

from ..exports.gsheets_export import get_gspread_sheet, get_sheets_config


def write_team_input():
    """Write team names from gsheets_config.yaml to the 'team_input' tab."""
    config = get_sheets_config()
    team_names = config.get('team_names', {})

    # Build columns: rec (division_1), intermediate (division_2), competitive (division_3)
    rec_teams = team_names.get('division_1', [])
    int_teams = team_names.get('division_2', [])
    comp_teams = team_names.get('division_3', [])

    # Find max length for padding
    max_len = max(len(rec_teams), len(int_teams), len(comp_teams))

    # Build data with headers
    data = [['rec', 'intermediate', 'competitive']]
    for i in range(max_len):
        row = [
            rec_teams[i] if i < len(rec_teams) else '',
            int_teams[i] if i < len(int_teams) else '',
            comp_teams[i] if i < len(comp_teams) else '',
        ]
        data.append(row)

    # Write to Google Sheets
    sheet = get_gspread_sheet()
    sheet.open_sheet('team_input')
    worksheet = sheet.sheet

    # Clear existing content
    worksheet.clear()

    # Write all data
    rows = len(data)
    cell_range = f'A1:C{rows}'
    worksheet.update(cell_range, data)

    print(f"✅ Wrote {max_len} teams to 'team_input' tab")
    print(f"   rec: {len(rec_teams)} teams")
    print(f"   intermediate: {len(int_teams)} teams")
    print(f"   competitive: {len(comp_teams)} teams")


if __name__ == '__main__':
    write_team_input()
