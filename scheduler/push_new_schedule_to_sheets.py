import caching
import optimizer
import sheets_access
import sheets_formatting
import csv
from schedule import init_value
import league_apps_csv


def push_v2_schedule_everywhere():
    sch = caching.load_v2_current_schedule()

    sheets_access.set_schedule_audit_sheet(sch.get_audit_text())
    league_apps_csv.make_league_apps_scv(sch)

    schedule_list_list = sheets_formatting.format_sand_schedule(sch)
    sheets_access.set_formatted_schedule_to_sheet(schedule_list_list)


if __name__ == '__main__':
    push_v2_schedule_everywhere()
