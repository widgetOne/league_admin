import traceback
import datetime
import random
import os
"""
reqs
1. generate teams based on the following constraints
    -all teams get same number of games
    -reffing is as balanced as possible
    -reffing must before or after play
    -cannot play/ref in more than one court at a time

stretch objectives:
1. minimize:
    -[will require names to teams] downtime between activities (play or ref)
Design:
Objects:
    Facility[1] - retains data on where can be played
        days[days-per-schedule] - distinct days in the schedule
            slots[division] - array of court-time tuples for that division
            sheet[court][time] - array of game slots in sheet form
    Division[1] - total set of teams in the league
        teams[teams-per-division] - team object in league
            contains team history (times reffed, times played another team,etc)
    Schedule[1] - retain a specific schedule
        days[days-per-season] - contains games for a given day
            contains team, ref, division, court and time data for all games
    where does games-per-team go?
"""

class FailedToConverge(Exception):
    pass


def compare_days(day1, day2):
    ''' this is a debugging and reporting tool'''
    print()
    for time in range(len(day1.courts[0])):
        game1_sum = ""
        game2_sum = ""
        for court in range(len(day1.courts)):
            game1 = day1.courts[court][time]
            game2 = day2.courts[court][time]
            game1_sum += game1.csv_str()
            game2_sum += game2.csv_str()
        print(game1_sum + "  " + game2_sum)


def play_schedule_pkl_path():
    return 'scratch/play_schedule_{}.pkl'.format(datetime.date.today())


def make_schedule(team_counts, league, sch_tries=500, seed=None, debug=True, reffing=True,
                  save_play_schedule=False):
    from schedule import Schedule
    import pickle
    start = datetime.datetime.now()
    if seed != None:
        random.seed(seed)
    try:
        if save_play_schedule and os.path.isfile(play_schedule_pkl_path()):
            sch = get_schedules(play_schedule_pkl_path())[0]
            mut_idx = 0
        else:
            facilities = league.days
            sch = Schedule(league, team_counts, facilities)
            #print([num / 4.0 for num in sch.get_game_div_count_list()])
            # add play schedule
            for div_idx in range(5):  # todo: if kept, make this dynamic
                for mut_idx in range(sch_tries):
                    if True:
                        sch.try_remake_a_few_random_days(div_idx, 1)
                        sch.try_remake_a_few_random_days(div_idx, random.randrange(1, sch.daycount + 1))
                    if debug:
                        print(sch.solution_debug_data(mut_idx, div_idx))
                    if (sch.fitness_div_list()[div_idx] == 0):
                        if debug:
                            print("correct schedule found for division {}!!!!!\n\n\n".format(div_idx))
                        break
                else:
                    print(sch.solution_debug_data(1))
                    print(sch.get_audit_text())
                    raise(FailedToConverge("main make_schedule routine failed to generate schedule in " +
                                           "{} tries.".format(sch_tries)))
            if save_play_schedule and not os.path.isfile(play_schedule_pkl_path()):
                save_schedules([sch], play_schedule_pkl_path())
        # add reffing duties
        #games_to_switch = [{'day': 1, 'court': 1, 'time': 0}, {'day': 1, 'court': 1, 'time': 1}]
        #games_to_switch = [{'day': 1, 'court': 3, 'time': 0}, {'day': 1, 'court': 3, 'time': 1}]
        #sch.switch_specific_games(*games_to_switch)

        if reffing:
            sch.add_reffing(debug=debug)
        if debug:
            print(sch.solution_debug_data(mut_idx))
        delta = (datetime.datetime.now() - start).total_seconds()
        print("total run_emr_job time was {} second and {} iterations".format(delta, mut_idx))
        path = '/Users/coulter/Desktop/life_notes/2016_q1/scvl/'
        # todo, change this to use print(datetime.datetime.now().date())
        save_sch = False
        if save_sch:
            tag = '2016-09-06a_'
            sch.gen_csv(path + tag + "simple.csv")
            sch.write_audit_file(path + tag + "audit_2016_spr.csv")
            sch_py_obj = path + tag + 'python_file_obj.pickle'
            with open(sch_py_obj,'wb') as sch_file:
                pickle.dump(sch, sch_file)
    except (Exception, KeyboardInterrupt) as e:
        print(sch.get_audit_text())
        print('Initial traceback was:\n{}'.format(traceback.format_exc()))
        raise (e)
    return sch

def make_regular_season(team_counts, ndays=9, sch_tries=500, seed=1):
    from facility import SCVL_Facility_Day
    from facility import League
    days = []
    import random
    random.seed(seed)
    league = League(ndivs=4, ndays=ndays, ncourts=5, ntimes=4,
                    team_counts=team_counts, day_type=SCVL_Facility_Day)
    league.debug_print()


    try:
        sch = make_schedule(team_counts, league, sch_tries=sch_tries)
    except (Exception, KeyboardInterrupt) as e:
        print(sch)
        print('Initial traceback was:\n{}'.format(traceback.format_exc()))
        raise (e)
    return sch

def get_default_potential_sch_loc(date=None):
    import datetime
    if date == None:
        date = str(datetime.datetime.now().date())
    default_path = 'scratch/'
    file_name = default_path + 'round_robin-schedules-from-{}.pkl'.format(date)
    return file_name

def save_schedules(schedules, file_path=None):
    import pickle
    if file_path == None:
        file_path = get_default_potential_sch_loc()
    for sch in schedules:
        try:
            del sch.fitness_structure
        except:
            pass
    print(os.getcwd())
    with open(file_path, 'wb') as pickle_file:
        pickle.dump(schedules, pickle_file)

def get_schedules(file_path=None):
    import os
    import pickle
    if file_path == None:
        file_path = get_default_potential_sch_loc()
    try:
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as pic_file:
                schedules = pickle.load(pic_file)
        else:
            schedules = []
    except:
        schedules = []
    return schedules

def report_schedule(name, sch_idx, schedule):
    print("reporting %s from schedule %s with a average sitting time of %s and %s long sits."
          % (name, sch_idx, (schedule.sitting_fitness()[0] / 40 * 15), schedule.sitting_fitness()[1]))
    path = '/Users/coulter/Desktop/life_notes/2016_q1/scvl/'
    schedule.gen_csv(path + name + "-simple_2016_spr.csv")
    schedule.write_audit_file(path + name + "-audit_2016_spr.csv")


def make_round_robin_game(team_counts, sch_template_path, total_schedules, canned_path=None):
    import facility
    sch_tries = 500  # at the moment we rarely need more than 4
    fac = facility.sch_template_path_to_fac(sch_template_path, team_counts)
    schedules = get_schedules(file_path=canned_path)
    already_created = len(schedules)
    try:
        target_seeds = list(range(already_created, total_schedules))
        for seed in target_seeds:
            print('\nMaking schedule %s.' % seed)
            sch = make_schedule(team_counts, fac,
                                sch_tries=sch_tries, seed=seed, debug=False, reffing=False)
            schedules.append(sch)
            if (seed + 1) % 25 == 0: # save every 25th schedule
                # todo: change this to be time based so round round and reg can use same logic
                # only save progress periodically, as each only takes a second and read/write can be mny
                save_schedules(schedules, file_path=canned_path)
    except KeyboardInterrupt:
        pass
    summary = report_on_schedules(schedules)
    return summary, schedules

def report_on_schedules(schedules):
    summary = {}
    for idx, sch in enumerate(schedules):
        results = sch.sitting_fitness()
        for name, result in results.items():
            if name in summary:
                old_fitness = summary[name]['fitness']
            else:
                old_fitness = -999999
            if result['fitness'] > old_fitness:
                result['seed'] = idx
                result['sch'] = sch
                summary[name] = result
    for name, result in sorted(summary.items()):
        result['name'] = name
        print('{:22s}: sits={}          ave={} func={} seed={}'.format(name, result['sits'],
                                                       result['ave'], result['func'],
                                                       result['seed']))
        times = [20*x for x in range(8)]
        team_sit_report = []
        for sits in result['team_sits']:
            sum_prod = sum((x*y for x,y in zip(times, sits)))
            team_sit_report.append(sum_prod)
            team_sit_report = sorted(team_sit_report)
        print(team_sit_report)
        summary[name]['team_sit_report'] = team_sit_report
    return summary


def summarize_canned_schedules():
    path = 'test/scratch/'
    file_name = 'round_robin_schs_2016-09-07.pkl'
    schedules = get_schedules(file_path=path+file_name)
    results = report_on_schedules(schedules)


