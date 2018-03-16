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


def make_round_robin_schedule(sch_template_path, team_counts):
    canned_path = 'test/scratch/'
    total_schedules = 1  # 12000
    summary, schedules = make_round_robin_game(team_counts, sch_template_path, total_schedules)
    choosing_a_winner = True
    if choosing_a_winner:
        preferred_winner = 'min hour and no-sit'
        sch = summary[preferred_winner]['sch']
        print(sch.get_audit_text())
        current_sum = summary[preferred_winner]
        make_final_report = True
        if make_final_report:
            file_path = 'scratch/{}_round_robin_sch.csv'.format(datetime.date.today())
            sch.gen_csv(file_path)
        print(sch.get_team_round_robin_audit())
        print('''\n\n\n\nThe final schedule has these properties:
              {}
              was seed {} and looks like this:
              {}'''.format(current_sum['team_sit_report'], current_sum['seed'], sch))


def make_2018_spring_round_robin_schedule():
    dir_name = '2018-1-spring'
    file_name = 'round_robin_input_template_maker_2018_1_spring.csv - machine_version.csv'
    sch_template_path = 'inputs/{}/{}'.format(dir_name, file_name)
    team_counts = [6, 10, 13, 11, 4]
    make_round_robin_schedule(sch_template_path, team_counts)


if __name__ == '__main__':
    make_2018_spring_round_robin_schedule()
    #make_regular_season_fall_2016()
    #make_regular_season_spring_2017()
