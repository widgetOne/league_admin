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


def make_regular_season(team_counts, ndays=9, sch_tries=500, seed=1):
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
                        sch_tries=sch_tries, seed=seed, debug=True)
    save_schedules([sch], canned_path)
    audit_text = sch.get_audit_text()
    print("\n".join(audit_text))

def make_round_robin_fall_2016():
    team_counts = [6, 10, 11, 10, 6]
    sch_template_path = 'test/Fall-2016-scrap-round_robin_csv_e.csv'
    canned_path = 'test/scratch/'
    total_schedules = 9205
    summary, schedules = make_round_robin_game(team_counts, sch_template_path, total_schedules)
    choosing_a_winner = False
    if choosing_a_winner:
        # pick schedule and generate the csv reports
        #sch = schedules[2047]
        sch = summary['sitting is sitting <45']['sch']
        audit_text = sch.get_audit_text()
        print("\n".join(audit_text))
        make_final_report = False
        if make_final_report:
            path = 'test/scratch/'
            today = datetime.date.today()
            file_name = '{}b_round_robin_sch.csv'.format(today)
            file_path = path + file_name
            sch.gen_csv(file_path)


def make_regular_season_spring_2017():
    team_counts = [6, 11, 11, 11, 6]
    canned_path = get_default_potential_sch_loc(str(datetime.date.today()))
    sch_template_path = 'inputs/reg_season/spring_2017_template.csv'
    sch_tries = 5000
    fac = facility.sch_template_path_to_fac(sch_template_path, team_counts)
    seed = 1
    print('\nMaking schedule %s.' % seed)
    sch = make_schedule(team_counts, fac,
                        sch_tries=sch_tries, seed=seed, debug=True)
    save_schedules([sch], canned_path)
    audit_text = sch.get_audit_text()
    print("\n".join(audit_text))


if __name__ == '__main__':
    make_regular_season_fall_2016()
    #make_regular_season_spring_2017()

