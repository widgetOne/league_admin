'''
This is the central location for driving the other modules. It should primarily
contain seasons and SCVL specific location.
'''
import facility
from optimizer import make_schedule, save_schedules
from optimizer import make_round_robin_game, get_default_potential_sch_loc
import datetime


def make_regular_season_schedule(sch_template_path, team_counts):
    canned_path = get_default_potential_sch_loc(str(datetime.date.today()))
    sch_tries = 5000
    fac = facility.sch_template_path_to_fac(sch_template_path, team_counts)
    seed = 3
    print('\nMaking schedule %s.' % seed)
    sch = make_schedule(team_counts, fac, sch_tries=sch_tries, seed=seed, debug=True, save_play_schedule=True)
    save_schedules([sch], canned_path)
    print(sch.get_audit_text())
    make_final_report = True
    teams_to_shift_out_court = [(2, 0), (0, 3), (1, 6), (0, 2), (1, 2)]
    court_to_shift_from = 3 - 1
    sch.try_shift_team_out_of_court(teams_to_shift_out_court, court_to_shift_from)
    # 	Jeffrey K. 1, Matthew K. 2,	Andrew M. 5, scott team 9,  Tracy G. 11, 	Fernando 11
    # board teams = 1,2, 5, 9, 11
    # teams playing now = 1, 2, 3, 4, 6, 7, 8, 11
    # not playing now = 5, 9, 10
    # board playing now:

    sch.switch_teams(div_idx=3, team1=9, team2=10)
    # board teams = 1,2, 5, 9, 11
    # teams playing now = 1, 2, 3, 4, 6, 7, 8, 10
    # not playing now = 5, 9, 11
    sch.switch_teams(div_idx=3, team1=1, team2=4)
    # board teams = 1,2, 5, 9, 11
    # teams playing now = 1, 3, 4, 5, 6, 7, 8, 10
    # not playing now = 2, 9, 11
    sch.switch_teams(div_idx=3, team1=0, team2=8)
    # board teams = 1,2, 5, 9, 11
    # teams playing now = 1, 3, 4, 5, 6, 7, 8, 10
    # not playing now = 2, 9, 11
    sch.switch_teams(div_idx=3, team1=6, team2=4)
    # board teams = 1,2, 5, 9, 11
    # teams playing now = 1, 3, 4, 5, 6, 7, 8, 10
    # not playing now = 2, 9, 11
    sch.switch_teams(div_idx=3, team1=7, team2=8)
    # board teams = 1,2, 5, 9, 11
    # teams playing now = 1, 3, 4, 5, 6, 7, 8, 10
    # not playing now = 2, 9, 11


    '''
    games_to_switch = [{'day': 5, 'court': 0, 'time': 0}, {'day': 5, 'court': 0, 'time': 1}]
    sch.switch_specific_games(*games_to_switch)
    sch.switch_specific_refs(*games_to_switch)
    games_to_switch = [{'day': 5, 'court': 4, 'time': 0}, {'day': 5, 'court': 4, 'time': 1}]
    sch.switch_specific_games(*games_to_switch)
    sch.switch_specific_refs(*games_to_switch)
    '''
    #
    # 2, 8
    #sch.switch_days(1, 7)
    # 2->8, 8->6, 6->2
    #sch.switch_days(1, 7)
    #sch.switch_days(1, 5)
    print(sch.fitness())
    print(sch)
    print(sch.solution_debug_data(1))
    #print(sch.days[0].get_csv())
    if make_final_report:
        file_path = 'output/2017_spring/2017_spring_regular_season_sch_{}.csv'.format(datetime.date.today())
        sch.gen_csv(file_path)
        file_path = 'scratch/audit_2017_spring_regular_season_sch_{}.text'.format(datetime.date.today())
        with open(file_path, 'w') as audit_file:
            audit_file.write(sch.get_audit_text())


def make_2018_spring_regular_season_schedule():
    dir_name = '2018-1-spring'
    file_name = 'Copy of f-ing copy of a GD google doc - machine_inpiut.csv'
    sch_template_path = 'inputs/{}/{}'.format(dir_name, file_name)
    team_counts = [6, 10, 13, 11, 4]
    make_regular_season_schedule(sch_template_path, team_counts)


if __name__ == '__main__':
    make_2018_spring_regular_season_schedule()
