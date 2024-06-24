import pandas as pd
import sheets_access
import caching
import schedule
import numpy as np
from copy import deepcopy
from pprint import pprint


def split_out_reffing(sch):
    for day in sch.days:
        for time in range(len(day.courts[0])):
            games = [day.courts[court][time]
                     for court in range(len(day.courts))]
            games = list(filter(lambda game: game.ref != schedule.init_value,
                                games))
            up_refs = [(game.div, game.ref) for game in games]
            line_refs = up_refs[1:] + up_refs[:1]
            new_refs = ((up, line) for up, line in zip(up_refs, line_refs))
            for game, refs in zip(games, new_refs):
                game.ref = refs
    return sch


def format_sand_schedule(sch):
    output_data = []
    all_times = ['12pm', '1pm', '2pm', '3pm', '4pm']
    split_sch = split_out_reffing(deepcopy(sch))
    header_data = ['Time'] + sum(
                   [[f"Court {c+1} Team 1", f"Court {c+1} Team 1",
                     'Up Ref', 'Line Ref']
                    for c in range(len(split_sch.days[0].courts))], [])
    total_cols = 1 + 4 * len(split_sch.days[0].courts)
    blank_row = ['' for _ in range(total_cols)]
    team_name_cypher = get_team_name_cypher()
    get_team_name = lambda team_tup: team_name_cypher[team_tup]
    for day in split_sch.days:
        output_data.append(header_data)
        times = all_times[-len(day.courts[0]):]
        for time_idx, time_str in enumerate(times):
            row_list = [time_str]
            for court_idx in range(len(day.courts)):
                game = day.courts[court_idx][time_idx]
                if game.div != schedule.init_value:
                    game_teams = [
                        (game.div, game.team1),
                        (game.div, game.team2),
                        game.ref[0],
                        game.ref[1],
                    ]
                    team_names = list(map(get_team_name, game_teams))
                else:
                    team_names = ['NO PLAY' for _ in range(4)]
                row_list += team_names
            output_data.append(row_list)
        output_data.append(blank_row)
    return output_data


def review_int_team_play_times():
    int_teams = list(range(10))
    df = pd.DataFrame(int_teams, index=int_teams)
    all_times = ['12pm', '1pm', '2pm', '3pm', '4pm']
    for time in all_times:
        df[time] = 0
    df.drop([0], axis=1, inplace=True)
    sch = caching.get_schedule_with_caching()
    for day_idx in range(len(sch.days)):
        df[day_idx] = 0
    for day_idx, day in enumerate(sch.days):
        for court in day.courts:
            times = all_times[-len(court):]
            for game, time in zip(court, times):
                if game.div == 1:
                    df[time][game.team1] += 1
                    df[time][game.team2] += 1
                    df[day_idx][game.team1] += 1
                    df[day_idx][game.team2] += 1
    df = df.replace([0], "")
    print(df)


def get_team_name_cypher():
    team_data = sheets_access.get_team_names_data()
    team_cypher = {}
    for team_idx, team_row in enumerate(team_data):
        for div_idx, team_name in enumerate(team_row):
            team_id = (div_idx, team_idx)
            team_cypher[team_id] = team_name
    return team_cypher


if __name__ == '__main__':
    pprint(review_int_team_play_times())
