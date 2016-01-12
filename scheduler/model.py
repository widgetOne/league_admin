

### YOYO: turn this into an abstract class

def rand(item_list):
    from random import randrange
    index = randrange(len(item_list))
    return item_list[index]

class Facility_Day(object):
    def __init__(self, court_count, time_count):
        self.court_count = court_count
        self.time_count = time_count
        self.refs = False
        self.court_divisions = [[-1 for _ in range(time_count)]
                       for __ in range(court_count)]
        self.div_times_locs = []
        self.day_type = -1 # tool for distinguishing types for days during mutation
        self.div_games = []
        self.set_division()

    def set_division(self):
        raise(NotImplementedError("missing contrete implimentation of abstract set_division method"))
        # logic will be need for how these divisions are set


class SCVL_Facility_Day(Facility_Day):
    def __init__(self, court_count, time_count, team_counts, rec_first):
        self.rec_first = rec_first
        if (rec_first):
            self.day_type = 0
        else:
            self.day_type = 1
        self.team_counts = team_counts
        super(SCVL_Facility_Day, self).__init__(court_count, time_count)
        self.refs = True

    def set_division(self):
        inner = [1,2,3]
        outer = [0,4]
        first_slots = [0,1]
        later_slots = [2,3]

        if self.rec_first:
            rec_comp_times = first_slots
            inter_power_times = later_slots
        else:
            rec_comp_times = first_slots
            inter_power_times = later_slots
        self.div_times_locs = [
                            (outer, rec_comp_times),
                            (inner, inter_power_times),
                            (inner, rec_comp_times),
                            (outer, inter_power_times),
                             ]
        self.div_games = []
        for div_idx in range(4):
            games = self.team_counts[div_idx] // 2
            locs, times = self.div_times_locs[div_idx]
            game_slots = [(x,y) for x in locs for y in times]
            for _ in range(len(game_slots) > games): # save off any extra games
                del game_slots[rand(range(games))]
            self.div_games.append(game_slots)
            for court, time in game_slots:
                self.court_divisions[court][time] = div_idx

class Game(object):
    def __init__(self):
        self.team1 = -1
        self.team2 = -1
        self.ref = -1
        self.div = -1

class Day(object):
    def __init__(self, facilities):
        from copy import deepcopy
        court = [Game() for _ in range(4)]
        self.courts = [deepcopy(court) for _ in range(5)]
        self.facilities = facilities

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
