'''
This is the central location for driving the other modules. It should primarily
contain seasons and SCVL specific location.
'''
import facility
from optimizer import make_schedule, save_schedules, FailedToConverge
from optimizer import make_round_robin_game, get_default_potential_sch_loc
import datetime


def make_regular_season_schedule(sch_template_path, team_counts, seed=3, sch_tries=5000, cycle_seeds=0):
    canned_path = get_default_potential_sch_loc(str(datetime.date.today()))
    fac = facility.sch_template_path_to_fac(sch_template_path, team_counts)
    print('\nMaking schedule %s.' % seed)
    if cycle_seeds:
        for cycling_seed in range(seed, cycle_seeds):
            try:
                sch = make_schedule(team_counts, fac, sch_tries=sch_tries, seed=cycling_seed, debug=True,
                                    save_play_schedule=True)
            except FailedToConverge:
                continue
            print('Things worked for seed {}'.format(cycling_seed))
            break
    else:
        sch = make_schedule(team_counts, fac, sch_tries=sch_tries, seed=seed, debug=True, save_play_schedule=True)
    save_schedules([sch], canned_path)
    print(sch.get_audit_text())
    make_final_report = True
    teams_to_shift_out_court = [(0, 0), (1, 10), (2, 11), (1, 8)]
    court_to_shift_from = 3 - 1
    sch.try_shift_team_out_of_court(teams_to_shift_out_court, court_to_shift_from)

    '''
    saving copies of schedule tweeking tools for easy reference and use
    
    sch.switch_teams(div_idx=3, team1=9, team2=10)
    sch.switch_teams(div_idx=3, team1=1, team2=4)

    games_to_switch = [{'day': 5, 'court': 0, 'time': 0}, {'day': 5, 'court': 0, 'time': 1}]
    sch.switch_specific_games(*games_to_switch)
    sch.switch_specific_refs(*games_to_switch)
    
    sch.switch_specific_refs(*games_to_switch)
    
    sch.switch_days(1, 7)

    '''

    if make_final_report:
        file_path = 'output/2018-2-Fall/2018_fall_regular_season_sch_{}.csv'.format(datetime.date.today())
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


def make_2018_fall_regular_season_schedule():
    dir_name = '2018-2-fall'
    file_name = 'regular_2018-09-15h.csv'
    sch_template_path = 'inputs/{}/{}'.format(dir_name, file_name)
    team_counts = [5, 11, 14, 13, 4]
    #make_regular_season_schedule(sch_template_path, team_counts, seed=2, sch_tries=400, cycle_seeds=60)
    make_regular_season_schedule(sch_template_path, team_counts, seed=3, sch_tries=10000)


def make_2024_sand_schedule():
    dir_name = 'stonewall/2024-outdoor'
    file_name = 'sand_2024-06-20a.csv'
    sch_template_path = 'inputs/{}/{}'.format(dir_name, file_name)
    team_counts = [10, 10, 8]
    #make_regular_season_schedule(sch_template_path, team_counts, seed=2, sch_tries=400, cycle_seeds=60)
    make_regular_season_schedule(sch_template_path, team_counts, seed=4, sch_tries=1000)


if __name__ == '__main__':
    make_2024_sand_schedule()
