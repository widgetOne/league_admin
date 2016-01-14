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

def epochNow():
    from calendar import timegm
    from time import gmtime
    return timegm(gmtime())

def compare_days(day1, day2):
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

def make_schedule(team_counts, facilities, tries=500):
    from schedule import Schedule
    from random import choice, randrange
    start = epochNow()
    sch = Schedule(team_counts, facilities)
    for mut_idx in range(tries):
        target1 = randrange(9)
        target2 = (target1 + randrange(8)) % 9
        target = [target1, target2]
        sch.try_remake_days(target)
        target = [randrange(9)]
        sch.try_remake_days(target)
        count = 1 + randrange(4)
        fitness = sch.remake_worst_day(count)
        print("fitness = %s while on mutation step %s: " % (fitness, mut_idx), end="")
        pprint([sch.divisions[idx].current_fitness for idx in range(4)])
        if (fitness == 0):
            print("correct schedule found!!!!!")
            break
    fitness = sch.fitness()
    end = epochNow()
    print("total run time was %s second" % (float(end - start)))
    path = '/Users/coulter/Desktop/life_notes/2016_q1/scvl/'
    sch.gen_csv(path + "test.csv")
    sch.gen_audit(path + "test_audit_2016_spr.csv")
    return fitness

def make_regular_season(team_counts, tries=500, seed=1):
    from facility import SCVL_Facility_Day
    from facility import League
    days = []
    import random
    random.seed(seed)
    league = League
    for day_idx in range(9):
        rec_plays_first = day_idx % 2 == 1
        days.append(SCVL_Facility_Day(5, 4,
                                            team_counts, rec_plays_first))
    league.days = days
    fitness = make_schedule(team_counts, days, tries=tries)
    return fitness

def make_round_robin(team_counts, tries=500):
    from model import SCVL_Round_Robin
    facilities = []
    rec_plays_first = False
    facilities.append(SCVL_Round_Robin(5, 4,
                                       team_counts, rec_plays_first))
    fitness = make_schedule(team_counts, facilities, tries=tries)
    return fitness

if __name__ == '__main__':
    make_regular_season([6,14,14,6], tries=500, seed=5)



