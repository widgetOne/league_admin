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
"""

from pprint import pprint

def list_filter(primary, filter):
    both = [team for team in primary if team in filter]
    if (len(both) > 0):
        return list(both)
    else:
        return primary


class Game(object):
    def __init__(self):
        self.team1 = -1
        self.team2 = -1
        self.ref = -1
        self.div = -1

class Day(object):
    def __init__(self):
        from copy import deepcopy
        court = [Game() for _ in range(4)]
        self.courts = [deepcopy(court) for _ in range(5)]

    def fitness(self, divisions):
        fitness = 0
        for court in self.courts:
            for game in court:
                team1 = divisions[game.div].teams[game.team1]
                team2 = divisions[game.div].teams[game.team2]
                old_count1 = team1.times_team_played[team2.team_idx]
                old_count2 = team2.times_team_played[team1.team_idx]
                fitness -= (old_count1 + old_count2) * 2 + 2
        return fitness

class Division(object):
    def __init__(self, team_count):
        self.teams = []
        self.team_count = team_count
        for team_idx in range(team_count):
            self.teams.append(Team(team_idx, team_count))

    def teams_w_least_ref(self):
        min_plays = min([team.refs for team in self.teams])
        return [team_num for team_num, team in enumerate(self.teams)
                if team.refs == min_plays]

    def teams_w_most_play(self):
        max_plays = max([team.games for team in self.teams])
        return [team_num for team_num, team in enumerate(self.teams)
                if team.games == max_plays]

    def teams_w_least_play(self):
        min_plays = min((team.games for team in self.teams))
        return [team_num for team_num, team in enumerate(self.teams)
                if team.games == min_plays]

    def fitness(self):
        fitness = 0
        for team in self.teams:
            pass

class Team(object):
    def __init__(self, team_idx, teams_in_division):
        time_slots = 4
        self.games = 0
        self.refs = 0
        self.team_idx = team_idx
        self.days_comma_games = []
        self.time_slot_count = [0 for _ in range(time_slots)]
        self.times_team_played = [0 for _ in range(teams_in_division)]
        self.times_team_played[team_idx] = 1000

    def add_game(self, court, time, team1, team2, ref):
        self.games.append(Game(court, team1, team2, ref))

    def teams_least_played(self):
        min_plays = min((played for played in self.times_team_played))
        return [team_idx for team_idx, played in enumerate(self.times_team_played)
                if played == min_plays]

class Schedule(object):
    time_string = ['6pm','7pm','8pm','9pm']
    rec_first = True
    def __init__(self, seed, team_counts):
        import random
        self.seed = seed
        self.team_counts = team_counts
        self.divisions = [Division(count) for count in team_counts]
        self.division_count = len(team_counts)

        self.daycount = 9
        self.courts = 5
        self.times = 4
        self.games_per_team = 9

        self.skillz_clinic_count()

        self.days = []
        random.seed(self.seed)
        self.random = random
        for day_idx in range(self.daycount):
            self.make_day(day_idx)

    def rand(self, set):
        index = self.random.randrange(len(set))
        return set[index]

    def make_day(self, day_idx):
        inner = [1,2,3]
        outer = [0,4]
        first_slots = [0,1]
        later_slots = [2,3]
        tries = 555
        best_day = False

        for _ in range(tries):
            day = Day()
            rec_plays_first = (day_idx % 2 == 1)
            if rec_plays_first:
                rec_comp_times = first_slots
                inter_power_times = later_slots
            else:
                rec_comp_times = first_slots
                inter_power_times = later_slots
            div_play_time_loc = [
                                (rec_comp_times, outer),
                                (inter_power_times, inner),
                                (rec_comp_times, inner),
                                (inter_power_times, outer),
                                 ]

            # first, complete minimum games
            for div_idx, div in enumerate(self.divisions):
                times, locs = div_play_time_loc[div_idx]
                games = div.team_count // 2
                game_slots = [(x,y) for x in locs for y in times]
                ref_slots = game_slots.copy()
                for _ in range(len(game_slots) > games): # save off any extra games
                    del game_slots[self.rand(range(games))]
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
               #         print("team %s and team %s are playing on court %s at %s"
               #               % (team1.team_idx, team2_idx, court, time))
                        del teams_to_play[teams_to_play.index(team2_idx)]
                    if day.courts[court][time].team1 < 0:
                        team2_obj = div.teams[day.courts[court][time].team1]
                        best_opponent = team2_obj.teams_least_played()
                        best_list = list_filter(teams_to_play, best_opponent)
                        team1_idx = self.rand(best_list)
                        day.courts[court][time].team1 = team1_idx
             #           print("team %s and team %s are playing on court %s at %s"
             #                 % (team1.team_idx, team2_idx, court, time))
                        del teams_to_play[teams_to_play.index(team1_idx)]

                # trying to clean up some of the game combinates
            if best_day:
                if day.fitness(self.divisions) > best_day.fitness(self.divisions):
                    print("new best day!!!")
                    best_day = day
                print("The fitness of this day is %s" % best_day.fitness(self.divisions))
            else:
                best_day = day
        print("problem team after = %s" %
              self.divisions[3].teams[5].times_team_played[5])

        for court in best_day.courts:
            for game in court:
                print("team %s and team %s w ref %s in div %s"
                          % (game.team1, game.team2, game.ref, game.div))
                if (game.div == -1):
                    continue
                self.divisions[game.div].teams[game.team1].times_team_played[game.team2] += 1
                self.divisions[game.div].teams[game.team2].times_team_played[game.team1] += 1
                self.divisions[game.div].teams[game.ref].refs += 1

        print("problem team = %s" %
              self.divisions[3].teams[5].times_team_played[5])
        self.days.append(best_day)

    def review_schedule(self):
        from math import pow
        fitness = 0
        for div_idx, div in enumerate(self.divisions):
            for team_idx, team in enumerate(div.teams):
                print("cross team play for team %s in division %s" % (div_idx, team_idx),)
                pprint( "%s and reffed %s " % (team.times_team_played, team.refs))
                fitness -= pow(team.refs, 2)
                for plays in team.times_team_played:
                    if plays < 1000:
                        fitness -= pow(plays, 2)
        # construct thorestical max
        print("total schedule fitness = %s" % fitness)
        max_fitness = 0
        min_ref = self.games_per_team // 2
        max_ref = self.games_per_team // 2 + self.games_per_team % 2
        max_fitness -= (pow(min_ref, 2) + pow(max_ref, 2)) * sum(self.team_counts) / 2.0
        for teams in self.team_counts:
            others = teams - 1
            min_plays = self.games_per_team // others
            max_plays = min_plays + 1
            max_teams = self.games_per_team - others * min_plays
            min_teams = others - max_teams
            loss_per_team = pow(min_plays, 2) * min_teams + pow(max_plays, 2) * max_teams
            max_fitness -= loss_per_team * teams
        print("total schedule max_fitness = %s" % max_fitness)
        print("delta to best possible = %s" % (max_fitness - fitness))

    def fitness(self):
        pass

    def skillz_clinic_count(self):
        # The number of skillz clinics is the number of open game slots
        total_slots = self.daycount * self.courts * self.times
        total_games = self.games_per_team * sum(self.team_counts) / 2 # 2 teams per game
        self.skillz_clinics = total_slots - total_games
        print("There will be %s skillz clinics in this schedule"
              % self.skillz_clinics)

    def create_daily_schedule(self):
        pass

def make_schedule(team_counts):
    sch = Schedule(0, team_counts)
    sch.review_schedule()


if __name__ == '__main__':
    make_schedule([6,12,12,6])



