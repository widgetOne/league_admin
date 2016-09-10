#!/anaconda/bin/python

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

def epoch_now():
    '''this is a simple utility for getting the current epoch'''
    from calendar import timegm
    from time import gmtime
    return timegm(gmtime())

def compare_days(day1, day2):
    ''' this is a debugging and reporting tool'''
    print()
    for time in range(len(day1.courts[0])):
        game1_sum = ""
        game2_sum = ""
        for court in range(len(day1.courts)):
            game1 = day1.courts[court][time]
            game2 = day2.courts[court][time]
            game1_sum += game1.small_str()
            game2_sum += game2.small_str()
        print(game1_sum + "  " + game2_sum)

def make_schedule(team_counts, league, sch_tries=500, seed=None, debug=True):
    from schedule import Schedule
    from random import choice, randrange
    import random
    import pickle
    import datetime
    facilities = league.days
    if seed != None:
        random.seed(seed)
    start = epoch_now()
    sch = Schedule(league, team_counts, facilities)
    sch.seed = seed
    for mut_idx in range(sch_tries):
        if False:
            if sch.daycount > 1:
                target1 = randrange(sch.daycount)
                target2 = (target1 + randrange(sch.daycount-1)) % sch.daycount
                target = [target1, target2]
                sch.try_remake_days(target)
            target = [randrange(sch.daycount)]
            fitness = sch.try_remake_days(target)
        if True:
            count = 1  # randrange(2)
            fitness = sch.remake_worst_day(count)
        # debug logic
        breakdown = sch.new_fitness_error_breakdown()
        if debug:
            print("value = %s while on mutation step %s: %s %s" %
                  (fitness, mut_idx, sch.new_fitness_div_list(), breakdown))
        if (fitness == 0):
            if debug:
                print("correct schedule found!!!!!")
            break
    else:
        raise(FailedToConverge("main make_schedule routine failed to generate schedule in " +
                               "{} tries.".format(sch_tries)))
    fitness = sch.new_fitness()
    end = epoch_now()
    print("total run_emr_job time was {} second and {} iterations".format(float(end - start),
                                                                          mut_idx))
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
    sch = make_schedule(team_counts, league, sch_tries=sch_tries)
    return sch

def make_round_robin(team_counts, sch_tries=500, seed=1, save_progress=False,
                     total_sch=2):
    from facility import SCVL_Round_Robin, League
    import random
    import pickle
    random.seed(seed)
    rec_plays_first = False
    league = League(ndivs=4, ndays=1, ncourts=5, ntimes=4,
                    team_counts=team_counts, day_type=SCVL_Round_Robin)
    best_sit_idx = None
    best_long_sit_idx = None
    schedules = get_schedules()
    initial_seed_schedule_len = len(schedules)

    for seed in range(total_sch):
        print('\nMaking schedule %s.' % seed)
        if seed >= len(schedules):
            sch = make_schedule(team_counts, league,
                                sch_tries=sch_tries, seed=seed, debug=False)
            schedules.append(sch)
        else:
            sch = schedules[seed]
        print("%s - Sitting value = %s. " % (seed, sch.sitting_fitness()[0]))
        print("%s - Min-Sit = %s and Min-long-sit = %s" % (seed, best_sit_idx,
                                                           best_long_sit_idx))
        print("%s\n%s" % (seed, seed))
        if save_progress and seed > initial_seed_schedule_len and (seed % 20) == 0:
            save_schedules(schedules)
    for idx, sch in enumerate(schedules):
        if best_sit_idx == None:
            best_sit_idx = idx
        elif (sch.sitting_fitness()[0] > schedules[best_sit_idx].sitting_fitness()[0]):
            best_sit_idx = idx

        if best_long_sit_idx == None:
            best_long_sit_idx = idx
        elif sch.sitting_fitness()[1] < schedules[best_long_sit_idx].sitting_fitness()[1]:
            best_long_sit_idx = idx
        elif sch.sitting_fitness()[1] == schedules[best_long_sit_idx].sitting_fitness()[1]:
            if sch.sitting_fitness()[0] > schedules[best_long_sit_idx].sitting_fitness()[0]:
                best_long_sit_idx = idx

        print('min = %s, min-long = %s' % (best_sit_idx,
                                           best_long_sit_idx), end='')
        print('The sitting value of schedule %s is %s. ' % (idx, sch.sitting_fitness()[0]), end="")
        print('This is %s minutes of sitting per team.' % (sch.sitting_fitness()[0] / 40 * 15), end='')
        print('long sits = %s' % sch.sitting_fitness()[1])
    if best_sit_idx != None:
        report_schedule('min-sit', best_sit_idx, schedules[best_sit_idx])
    if best_long_sit_idx != None:
        report_schedule('no-long-sit', best_long_sit_idx, schedules[best_long_sit_idx])
    if save_progress:
        save_schedules(schedules)
    return schedules[best_sit_idx]

def get_default_potential_sch_loc(date=None):
    import datetime
    if date == None:
        date = str(datetime.datetime.now().date())
    default_path = 'test/scratch/'
    file_name = default_path + 'round_robin-schedules-from-{}'.format(date)
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
    for seed in range(already_created, total_schedules):
        print('\nMaking schedule %s.' % seed)
        sch = make_schedule(team_counts, fac,
                            sch_tries=sch_tries, seed=seed, debug=False)
        schedules.append(sch)
        if (seed + 1) % 50 == 0: # save every 50th schedule
            # only save progress periodically, as each only takes a second and read/write can be mny
            save_schedules(schedules, file_path=canned_path)
    summary = report_on_schedules(schedules)
    return summary, schedules

def make_round_robin_from_csv_fall_2016():
    import datetime
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
            today = datetime.datetime.now().date()
            file_name = '{}b_round_robin_sch.csv'.format(today)
            file_path = path + file_name
            sch.gen_csv(file_path)


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
        print('{:22s}: sits={} ave={} func={} seed={}'.format(name,
                                                       result['sits'],
                                                       result['ave'],
                                                       result['func'],
                                                       result['seed']))
        times = [15*x for x in range(8)]
        team_scores = []
        for sits in result['team_sits']:
            sum_prod = sum((x*y for x,y in zip(times, sits)))
            team_scores.append(sum_prod)
        print(sorted(team_scores))
    return summary


def summarize_canned_schedules():
    path = 'test/scratch/'
    file_name = 'round_robin_schs_2016-09-07.pkl'
    schedules = get_schedules(file_path=path+file_name)
    results = report_on_schedules(schedules)


if __name__ == '__main__':
    import os
    #   make_round_robin([6,14,14,6], tries=5, seed=5)
    #   make_regular_season([6,13,14,7], ndays=9, sch_tries=4, seed=5)
    #   make_regular_season([6,12,12,6], ndays=9, sch_tries=7000, seed=5)
    #   make_regular_season([6,14,14,6], ndays=9, sch_tries=400, seed=5)
    #   schedule = make_regular_season([6, 13, 14, 7], ndays=9,
    #                                  sch_tries=10000, seed=5)

    #schedule = make_regular_season([6, 13, 14, 7], ndays=9,
    #                               sch_tries=10000, seed=5)

    make_round_robin_from_csv_fall_2016()

    #print('\n'.join(schedule.get_audit_text()))
    #os.system('say "schedule creation is complete"')
