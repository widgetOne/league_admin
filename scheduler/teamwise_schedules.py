import os
import re
from pprint import pprint
import caching
from optimizer import save_schedules, get_schedules
from sheets_formatting import format_sand_schedule
from copy import deepcopy


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

def format_team_schedules(split_schedule, team_schedules):
    output_schedules = deepcopy(team_schedules)
    column_cypher = get_column_cypher(split_schedule[0])
    day_strings = get_day_strings()
    day_idx = 0
    today_str, today_has_play = day_strings[day_idx]
    add_to_all_schedules(output_schedules, today_str)
    print(output_schedules)


def upload_teamwise_schedules():
    sch = load_current_schedule()
    split_sch = format_sand_schedule(sch)
    team_schedules = [[list() for _ in range(div_count)] for div_count in sch.team_counts]
    teamwise_schedule = format_team_schedules(split_sch, team_schedules)


if __name__ == '__main__':
    upload_teamwise_schedules()
