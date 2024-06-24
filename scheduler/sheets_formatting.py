import pandas as pd
import sheets_access
import caching
import schedule
import numpy as np


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


def generate_sand_schedule_csv():
    output_csv = ''
    sch = caching.get_schedule_with_caching()
    split_sch = split_out_reffing(sch)
    for day in split_sch.days:
        for court in day.courts:
            for game in court:
                print(game)


def review_int_team_play_times():
    int_teams = list(range(10))
    df = pd.DataFrame(int_teams, index=int_teams)
    all_times = ['12pm', '1pm', '2pm', '3pm', '4pm']
    for time in all_times:
        df[time] = 0
    df.drop([0], axis=1, inplace=True)
    sch = caching.get_schedule_with_caching()
    for day in sch.days:
        for court in day.courts:
            times = all_times[-len(court):]
            for game, time in zip(court, times):
                if game.div == 1:
                    df[time][game.team1] += 1
                    df[time][game.team2] += 1
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
    print(get_team_name_cypher())
