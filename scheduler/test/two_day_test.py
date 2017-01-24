import datetime
import os, sys
from pprint import pprint
basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, basedir + '/../')
import facility
from optimizer import make_schedule, save_schedules
from optimizer import make_round_robin_game, get_default_potential_sch_loc


def run_two_day_test():
    team_counts = [4, 10, 10, 10, 6]
    canned_path = get_default_potential_sch_loc(str(datetime.date.today()))
    sch_template_path = 'support_files/two_day_test.csv'
    sch_tries = 5000
    fac = facility.sch_template_path_to_fac(sch_template_path, team_counts)
    seed = 3
    print('\nMaking schedule %s.' % seed)
    sch = make_schedule(team_counts, fac, sch_tries=sch_tries, seed=seed, debug=True)
    #save_schedules([sch], canned_path)
    audit_text = sch.get_audit_text()
    print("\n".join(audit_text))


if __name__ == '__main__':
    run_two_day_test()