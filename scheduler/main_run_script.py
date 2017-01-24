'''
This is the central location for driving the other modules. It should primarily
contain seasons and SCVL specific location.
'''
import facility
from optimizer import make_schedule, save_schedules
from optimizer import make_round_robin_game, get_default_potential_sch_loc
import datetime
from facility import SCVL_Facility_Day
from facility import Facility
from pprint import pprint

def make_regular_season(team_counts, ndays=9, sch_tries=500, seed=1):
    """not currently used"""
    days = []
    import random
    random.seed(seed)
    league = Facility(ndivs=4, ndays=ndays, ncourts=5, ntimes=4,
                    team_counts=team_counts, day_type=SCVL_Facility_Day)
    league.debug_print()
    sch = make_schedule(team_counts, league, sch_tries=sch_tries)
    return sch

def make_regular_season_fall_2016():
    team_counts = [6, 10, 11, 10, 6]
    canned_path = get_default_potential_sch_loc('2016-09-10')
    sch_template_path = 'test/reg_season/draft_fac_a.csv'
    sch_tries = 5000
    fac = facility.sch_template_path_to_fac(sch_template_path, team_counts)
    seed = 1
    print('\nMaking schedule %s.' % seed)
    sch = make_schedule(team_counts, fac,
                        sch_tries=sch_tries, seed=seed, debug=True, save_play_schedule=True)
    save_schedules([sch], canned_path)
    print(sch.get_audit_text())


def make_round_robin_spring_2017():
    team_counts = [6, 12, 11, 10, 6]
    sch_template_path = 'inputs/2017-spring/round_robin_template_2017-01-21a.csv'
    canned_path = 'test/scratch/'
    total_schedules = 3000
    summary, schedules = make_round_robin_game(team_counts, sch_template_path, total_schedules)
    choosing_a_winner = True
    if choosing_a_winner:
        #pprint(summary)
        sch = summary['min hour and no-sit']['sch']
        print(sch)
        make_final_report = True
        if make_final_report:
            file_path = 'scratch/{}b_round_robin_sch.csv'.format(datetime.date.today())
            sch.gen_csv(file_path)


def make_regular_season_spring_2017():
    team_counts = [6, 12, 11, 10, 6]
    canned_path = get_default_potential_sch_loc(str(datetime.date.today()))
    sch_template_path = 'inputs/reg_season/spring_2017_template_01_23b.csv'
    sch_tries = 5000
    fac = facility.sch_template_path_to_fac(sch_template_path, team_counts)
    seed = 10  # 4 got through play
    print('\nMaking schedule %s.' % seed)
    sch = make_schedule(team_counts, fac, sch_tries=sch_tries, seed=seed, debug=True,
                        save_play_schedule=True)
    save_schedules([sch], canned_path)
    print(sch.get_audit_text())
    make_final_report = True
    print(sch)
    print(sch.solution_debug_data(1))
    if make_final_report:
        file_path = 'output/2017_spring/2017_spring_regular_season_sch_{}.csv'.format(datetime.date.today())
        sch.gen_csv(file_path)


if __name__ == '__main__':
    #make_regular_season_fall_2016()
    make_regular_season_spring_2017()
