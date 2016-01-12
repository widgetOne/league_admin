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


def list_filter(primary, filter):
    both = [team for team in primary if team in filter]
    if (len(both) > 0):
        return list(both)
    else:
        return primary

class Schedule(object):
    time_string = ['6pm','7pm','8pm','9pm']
    rec_first = True
    def __init__(self, team_counts, facs):
        import random
        from model import Division
        self.team_counts = team_counts
        self.divisions = [Division(count) for count in team_counts]
        self.division_count = len(team_counts)
        self.max_fitness = 0
        self.daycount = 9
        self.courts = 5
        self.times = 4
        self.games_per_team = 9

        self.enhance_success = 0
        self.skillz_clinic_count()

        self.days = []
        self.random = random
        for day_idx in range(self.daycount):
            day = self.make_day(facs[day_idx])
            self.add_day_to_division_history(day)
            self.days.append(day)

    def rand(self, set):
        index = self.random.randrange(len(set))
        return set[index]

    def remake_worst_day(self):
        days_fitness = [day.fitness(self.divisions) for day in self.days]
        worst_day_fitness = min([day.fitness(self.divisions) for day in self.days])
        worst_days = [day_idx for day_idx, day in enumerate(self.days)
                      if day.fitness(self.divisions) == worst_day_fitness]
   #     pprint("the days fitness's and then the worst of them")
   #     pprint(days_fitness)
   #     pprint(worst_days)
        fitness = self.try_remake_days(worst_days)
        return fitness

    def try_remake_days(self, day_indexs):
        from copy import deepcopy
        origional_days = deepcopy(self.days)
        origional_division = deepcopy(self.divisions)
        origional_fitness = self.fitness()
        for day_idx in day_indexs:
            self.subtract_day_from_division_history(self.days[day_idx])
        for day_idx in day_indexs:
            new_day = self.make_day(self.days[day_idx].facilities)
      #      compare_days(new_day, self.make_day(self.days[day_idx].facilities))
            self.days[day_idx] = new_day
        new_fitness = self.fitness()
    #    new_day.courts[1][1].team1 = 4
    #    if new_day != self.days[day_idx]:
    #        self.enhance_success += 1
    #    else:
    #        raise(Exception("fail to enhance after %s successes" % self.enhance_success))
        if origional_fitness < self.fitness():
            self.days = origional_days
            self.divisions = origional_division
            new_fitness = origional_fitness
        return new_fitness

    def make_day(self, fac):
        from random import shuffle
        from model import Day
        from model import SCVL_Facility_Day
        tries = 10
        best_day = False
        for _ in range(tries):
            day = Day(fac)
            # first, complete minimum games
            for div_idx, div in enumerate(self.divisions):
                locs, times = fac.div_times_locs[div_idx]
                games = div.team_count // 2
                game_slots = fac.div_games[div_idx].copy()
                shuffle(game_slots)
                ref_slots = game_slots.copy()
                teams_to_play = list(range(div.team_count))
                ''' ignoring odd cases for now
                if div.team_count % 2 == 1:
                    most_games = div.teams_w_most_play()
                    odd_team_out = most_games[self.random.randrange(len(most_games))]
                    del teams_to_play[odd_team_out]
                '''
                # add refs
                for game_idx in range(games):
                    short_ref_teams = list_filter(teams_to_play, div.teams_w_least_ref())
                    current_team_num = self.rand(short_ref_teams)
                    court, ref_time = game_slots[game_idx]
                    day.courts[court][ref_time].ref = current_team_num
                    day.courts[court][ref_time].div = div_idx
                    play_time = times[(times.index(ref_time) + 1) % len(times)]
                    if (court, play_time) in game_slots:
                        day.courts[court][play_time].team1 = current_team_num
                    else:
                        court = locs[(locs.index(court) + 1) % len(locs)]
                        day.courts[court][play_time].team2 = current_team_num
                    del teams_to_play[teams_to_play.index(current_team_num)]

                # fill in players
                for game_idx in range(games):
                    court, time = game_slots[game_idx]
                    if day.courts[court][time].team2 < 0:
                        team1 = div.teams[day.courts[court][time].team1]
                        best_opponent = team1.teams_least_played()
                        best_list = list_filter(teams_to_play, best_opponent)
                        team2_idx = self.rand(best_list)
                        day.courts[court][time].team2 = team2_idx
                        del teams_to_play[teams_to_play.index(team2_idx)]
                    if day.courts[court][time].team1 < 0:
                        team2_obj = div.teams[day.courts[court][time].team1]
                        best_opponent = team2_obj.teams_least_played()
                        best_list = list_filter(teams_to_play, best_opponent)
                        team1_idx = self.rand(best_list)
                        day.courts[court][time].team1 = team1_idx
                        del teams_to_play[teams_to_play.index(team1_idx)]

                # trying to clean up some of the game combinates
            if best_day:
                best_day_fitness = best_day.fitness(self.divisions)
                if day.fitness(self.divisions) > best_day_fitness:
            #        print("new best day with fitness of %s!!!" % best_day_fitness)
                    best_day = day
            #    print("The fitness of this day is %s" % best_day.fitness(self.divisions))
            else:
                best_day = day
     #   print("problem team = %s" %
     #         self.divisions[3].teams[5].times_team_played[5])
        return best_day

    def fitness(self):
        from math import pow
        if self.max_fitness == 0:
            min_ref = self.games_per_team // 2
            max_ref = self.games_per_team // 2 + self.games_per_team % 2
            self.max_fitness -= (pow(min_ref, 2) + pow(max_ref, 2)) * sum(self.team_counts) / 2.0
            for teams in self.team_counts:
                others = teams - 1
                min_plays = self.games_per_team // others
                max_plays = min_plays + 1
                max_teams = self.games_per_team - others * min_plays
                min_teams = others - max_teams
                loss_per_team = pow(min_plays, 2) * min_teams + pow(max_plays, 2) * max_teams
                self.max_fitness -= loss_per_team * teams
        fitness = -self.max_fitness
    #    print("cross team data")
        for div_idx, div in enumerate(self.divisions):
            for team_idx, team in enumerate(div.teams):
                start = "team %s in division %s " % (team_idx, div_idx)
     #           pprint(start + "%s and reffed %s " % (team.times_team_played, team.refs))
                fitness -= pow(team.refs, 2)
                for plays in team.times_team_played:
                    if plays < 1000:
                        fitness -= pow(plays, 2)
        # construct thorestical max
    #    print("total schedule fitness = %s" % fitness)
        return fitness

    def add_day_to_division_history(self, day, sign=1):
        for court_idx, court in enumerate(day.courts):
            for game in court:
    #            print("team %s and team %s w ref %s in div %s on court %s"
    #                      % (game.team1, game.team2, game.ref, game.div, court_idx))
                if (game.div == -1):
                    continue
                self.divisions[game.div].teams[game.team1].times_team_played[game.team2] += sign
                self.divisions[game.div].teams[game.team2].times_team_played[game.team1] += sign
                self.divisions[game.div].teams[game.ref].refs += sign

    def subtract_day_from_division_history(self, day):
        self.add_day_to_division_history(day, sign=-1)

    def skillz_clinic_count(self):
        # The number of skillz clinics is the number of open game slots
        total_slots = self.daycount * self.courts * self.times
        total_games = self.games_per_team * sum(self.team_counts) / 2 # 2 teams per game
        self.skillz_clinics = total_slots - total_games
        print("There will be %s skillz clinics in this schedule"
              % self.skillz_clinics)

    def create_daily_schedule(self):
        pass

def make_schedule(team_counts, seed=1):
    import random
    from model import SCVL_Facility_Day
    facilities = []
    random.seed(seed)
    for day_idx in range(9):
        rec_plays_first = day_idx % 2 == 1
        facilities.append(SCVL_Facility_Day(5, 4,
                                            team_counts, rec_plays_first))
    tries = 0
    sch = Schedule(team_counts, facilities)
    for _ in range(tries):
        random.seed(_ + 34534)
        fitness = sch.try_remake_days(range(9))
    for _ in range(34):
        random.seed(_ + 123)
        target = [sch.rand(range(9))]
        fitness = sch.try_remake_days(target)
        fitness = sch.remake_worst_day()
        print("fitness = %s" % fitness)
    fitness = sch.fitness()
    return fitness

if __name__ == '__main__':
    make_schedule([6,12,12,6])



