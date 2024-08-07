import caching
import optimizer
import sheets_access
import sheets_formatting
import csv
from schedule import init_value


def make_league_apps_scv(sch):
    header_base = 'SUB_PROGRAM	HOME_TEAM	AWAY_TEAM	DATE	START_TIME	END_TIME	LOCATION	SUB_LOCATION	TYPE	NOTES'
    header = header_base.split('\t')
    split_sch = sheets_formatting.split_out_reffing(sch)
    team_cypher = sheets_formatting.get_team_name_cypher()
    data = [header]
    start_times = ['12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
    day_strs = ['06/30/2024', '07/14/2024',  '07/28/2024',  '08/04/2024',  '08/11/2024', ]
    for day_idx, day in enumerate(split_sch.days):
        for time in range(len(day.courts[0])):
            for court_idx in range(len(day.courts)):
                game = day.courts[court_idx][time]
                if game.div == init_value:
                    continue
                row = [
                    '',
                    team_cypher[(game.div, game.team1)],
                    team_cypher[(game.div, game.team2)],
                    day_strs[day_idx],
                    start_times[time],
                    start_times[time+1],
                    'Highland Park',
                    f'Court {court_idx+1}',
                    'REGULAR_SEASON',
                    f'Up Ref {team_cypher[game.ref[0]]}\nLine Ref {team_cypher[game.ref[1]]}',
                ]
                data.append(row)
    output_path = 'scratch/2024_sand_vball_league_apps.csv'
    export_to_csv_file = False
    if export_to_csv_file:
        with open(output_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(data)
        with open(output_path, 'r') as csv_file:
            csv_str = csv_file.read()
            print(csv_str)
    else:
        sheets_access.set_league_apps_csv_sheet(data)
        #print(data)


def push_v2_schedule_everywhere():
    sch = caching.load_v2_current_schedule()
    sheets_access.set_schedule_audit_sheet(sch.get_audit_text())
    schedule_list_list = sheets_formatting.format_sand_schedule(sch)
    sheets_access.set_formatted_schedule_to_sheet(schedule_list_list)


if __name__ == '__main__':
    sch = caching.load_v2_current_schedule()
    make_league_apps_scv(sch)
