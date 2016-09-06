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

from pprint import pprint

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

def make_schedule(team_counts, league, sch_tries=500, seed=None):
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
        if True:
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
        print("value = %s while on mutation step %s: %s %s" %
              (fitness, mut_idx, sch.new_fitness_div_list(), breakdown))
        if (fitness == 0):
            print("correct schedule found!!!!!")
            break
    fitness = sch.fitness(league.games_per_div)
    end = epoch_now()
    print("total run time was %s second" % (float(end - start)))
    path = '/Users/coulter/Desktop/life_notes/2016_q1/scvl/'
    # todo, change this to use print(datetime.datetime.now().date())
    tag = '2016-07-18a_'
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
                                sch_tries=sch_tries, seed=seed)
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

def save_schedules(schedules):
    import pickle
    import datetime
    path = '/Users/coulter/Desktop/life_notes/2016_q1/scvl/'
    todays_date = print(datetime.datetime.now().date())
    schedule_name = path + 'round_robin-schedules-from-{}'.format(todays_date)
    with open(schedule_name, 'wb') as pickle_file:
        pickle.dump(schedules, pickle_file)

def get_schedules():
    import os
    import pickle
    # todo: add logic here to grab the round robin object with the newest date
    path = '/Users/coulter/Desktop/life_notes/2016_q2/scvl/'
    round_r_schedules_path = path + 'new-round-robin-schedules-objects'
    if os.path.isfile(round_r_schedules_path):
        with open(round_r_schedules_path, 'rb') as pic_file:
            schedules = pickle.load(pic_file)
    else:
        schedules = []
    return schedules

def report_schedule(name, sch_idx, schedule):
    print("reporting %s from schedule %s with a average sitting time of %s and %s long sits."
          % (name, sch_idx, (schedule.sitting_fitness()[0] / 40 * 15), schedule.sitting_fitness()[1]))
    path = '/Users/coulter/Desktop/life_notes/2016_q1/scvl/'
    schedule.gen_csv(path + name + "-simple_2016_spr.csv")
    schedule.write_audit_file(path + name + "-audit_2016_spr.csv")


if __name__ == '__main__':
    import os
    #   make_round_robin([6,14,14,6], tries=5, seed=5)
    #   make_regular_season([6,13,14,7], ndays=9, sch_tries=4, seed=5)
    #   make_regular_season([6,12,12,6], ndays=9, sch_tries=7000, seed=5)
    #   make_regular_season([6,14,14,6], ndays=9, sch_tries=400, seed=5)
    #   schedule = make_regular_season([6, 13, 14, 7], ndays=9,
    #                                  sch_tries=10000, seed=5)
    schedule = make_regular_season([6, 13, 14, 7], ndays=9,
                                   sch_tries=10000, seed=5)
    #print('\n'.join(schedule.get_audit_text()))
    os.system('say "schedule creation is complete"')
