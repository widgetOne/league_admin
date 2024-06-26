import os
import re
from pprint import pprint
import caching
from optimizer import save_schedules, get_schedules
from sheets_formatting import format_sand_schedule, get_team_name_cypher
from copy import deepcopy
from sheets_access import get_team_names_data

def load_current_schedule():
    path = 'scratch'
    schedule_name = 'round_robin-schedules-from-2024-06-24.pkl'
    full_path = os.path.join(path, schedule_name)
    return get_schedules(full_path)[0]


def format_teamwise_row():
    pass


def get_day_strings():
    # the date and if play is taking place
    return [
        ('June 30th - Week 1', True),
        ('July 7th - 7/4!', False),
        ('July 14th - Week 2', True),
        ('July 21th - Stonewall Nationals', False),
        ('July 28th - Week 3', True),
        ('August 4th - Week 4', True),
        ('August 11th - Week 5', True),
        ('August 16th - Volley Ball!!', False),
        ('August 17th/18th - Playoffs', False),
        ('August 24th/25th - Playoffs Rain Day', False),
    ]


def get_column_cypher(column_one):
    team_regex = r' Team .*'
    remove_team = lambda x: re.sub(team_regex, '', x)
    column_cypher = list(map(remove_team, column_one))
    return column_cypher


def add_to_all_schedules(team_schedules, day_string):
    for div in team_schedules:
        for team_sch in div:
            team_sch.append(day_string)


inv_team_cypher = None
def get_inv_cypher():
    global inv_team_cypher
    if inv_team_cypher is None:
        basic_cypher = get_team_name_cypher()
        inv_cypher = {v:k for k, v in basic_cypher.items()}
        inv_team_cypher = inv_cypher
    return inv_team_cypher


def get_play_str(time, court_idx, opponent_name):
    return f'{time}: Play on Court {court_idx+1} vs {opponent_name}'


def get_ref_str(time, ref_type, court_idx):
    return f'{time}: {ref_type} on Court {court_idx+1}'


def add_entries_for_row(team_schedules, row, column_cypher):
    time = row[0]
    inv_team_cypher = get_inv_cypher()
    court_count = int((len(row) - 1) // 4)
    for court_idx in range(court_count):
        start_idx = 1 + 4 * court_idx
        if row[start_idx] == 'NO PLAY':
            continue
        team1_name = row[start_idx]
        team1 = inv_team_cypher[team1_name]
        team2_name = row[start_idx+1]
        team2 = inv_team_cypher[team2_name]
        team_schedules[team1[0]][team1[1]].append(get_play_str(time, court_idx, team2_name))
        team_schedules[team2[0]][team2[1]].append(get_play_str(time, court_idx, team1_name))
        for ref_idx in range(start_idx+2, start_idx+4):
            ref_team = inv_team_cypher[row[ref_idx]]
            team_schedules[ref_team[0]][ref_team[1]].append(get_ref_str(time, column_cypher[ref_idx], court_idx))


def format_team_schedules(split_schedule, team_schedules):
    output_schedules = deepcopy(team_schedules)
    column_cypher = get_column_cypher(split_schedule[0])
    day_strings = get_day_strings()
    day_idx = 0
    today_str, today_has_play = day_strings[day_idx]
    add_to_all_schedules(output_schedules, today_str)
    for row in split_schedule[1:]:
        if row[0] == "Time":
            continue
        elif row[0] == '':
            today_has_play = False
            while not today_has_play and day_idx < len(day_strings) - 1:
                day_idx += 1
                add_to_all_schedules(output_schedules, '')
                today_str, today_has_play = day_strings[day_idx]
                add_to_all_schedules(output_schedules, today_str)
        else:
            add_entries_for_row(output_schedules, row, column_cypher)
    return output_schedules


def upload_teamwise_schedules():
    sch = load_current_schedule()
    split_sch = format_sand_schedule(sch)
    team_schedules = [[list() for _ in range(div_count)] for div_count in sch.team_counts]
    #print(split_sch)
    teamwise_schedule = format_team_schedules(split_sch, team_schedules)
    print(teamwise_schedule)


if __name__ == '__main__':
    upload_teamwise_schedules()
