import os
import re
from pprint import pprint
import caching
from optimizer import save_schedules, get_schedules
from sheets_formatting import format_sand_schedule, get_team_name_cypher
from copy import deepcopy
from sheets_access import get_team_names_data, set_teamwise_schedules_to_sheet


def format_teamwise_row():
    pass


def get_day_strings():
    # the date and if play is taking place
    return [
        ('June 30th - Week 1', True),
        ('July 7th - NO GAMES', False),
        ('July 14th - Week 2', True),
        ('July 21th - NO GAMES', False),
        ('July 28th - Week 3', True),
        ('August 4th - Week 4', True),
        ('August 11th - Week 5', True),
        ('August 16th - The Volley Ball!!', False),
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


cached_inv_team_cypher = None
def get_inv_cypher():
    global cached_inv_team_cypher
    if cached_inv_team_cypher is None:
        basic_cypher = get_team_name_cypher()
        inv_cypher = {v:k for k, v in basic_cypher.items()}
        cached_inv_team_cypher = inv_cypher
    return cached_inv_team_cypher


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


def reffing_in_last_schedule_day(team_schedule):
    max_daily_events = 6
    for line in team_schedule[:-max_daily_events:-1]:
        # TODO: should probably make this more robust to team names/day changes
        if 'ref' in line.lower():
            return True
        if ' - week ' in line.lower():
            return False
    raise(Exception(f'flaw in this function when parsing schedule {team_schedule}'))


def add_no_reffing_notes(team_schedules):
    for div_idx, div_schs in enumerate(team_schedules):
        for team_idx, team_sch in enumerate(div_schs):
            if not reffing_in_last_schedule_day(team_sch):
                team_sch.append('No Reffing')


def format_team_schedules(split_schedule, source_schedule):
    output_schedules = deepcopy(source_schedule)
    column_cypher = get_column_cypher(split_schedule[0])
    team_cypher = get_team_name_cypher()
    for div_idx, div_schs in enumerate(output_schedules):
        for team_idx, team_sch in enumerate(div_schs):
            print()
            team_sch.append(team_cypher[(div_idx, team_idx)])
    day_strings = get_day_strings()
    day_idx = 0
    today_str, today_has_play = day_strings[day_idx]
    add_to_all_schedules(output_schedules, today_str)
    for row in split_schedule[1:]:
        if row[0] == "Time":  # header row for new set of games
            continue
        elif row[0] == '':  # blank row between days
            add_no_reffing_notes(output_schedules)
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
    sch = caching.load_current_schedule()
    split_sch = format_sand_schedule(sch)
    team_schedules = [[list() for _ in range(div_count)] for div_count in sch.team_counts]
    teamwise_schedule = format_team_schedules(split_sch, team_schedules)
    set_teamwise_schedules_to_sheet(teamwise_schedule)
    print(teamwise_schedule)


if __name__ == '__main__':
    upload_teamwise_schedules()
