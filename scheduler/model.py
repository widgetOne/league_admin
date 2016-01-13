

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
        self.alternate_div_loc = [inner, outer, outer, inner]
        self.div_games = []
        self.div_times_games = [[] for _ in range(4)]
        spare_slots = [[] for _ in range(4)]
        spare_div = [2,3,0,1]
        # first pass
        for div_idx in range(4):
            games = self.team_counts[div_idx] // 2
            locs, times = self.div_times_locs[div_idx]
            game_slots = [(x,y) for x in locs for y in times]
            for _ in range(len(game_slots) > games): # save off any extra games
                rm_loc = rand(range(games))
                spare_slots[spare_div[div_idx]].append(game_slots[rm_loc])
                del game_slots[rm_loc]
            self.div_games.append(game_slots)
            for court, time in game_slots:
                self.court_divisions[court][time] = div_idx
                self.div_times_games[div_idx].append((court, time))
        # filling in gaps
        for div_idx in range(4):
            locs, times = self.div_times_locs[div_idx]
            for idx in range(self.team_counts[div_idx] // 2 -
                                             len(locs) * len(times) ):
                if len(spare_slots[div_idx]) < 1:
                    raise(Exception())
                court, time = spare_slots[div_idx][0]
                self.court_divisions[court][time] = div_idx
                self.div_times_games[div_idx].append((court, time))
                self.div_games[div_idx].append(spare_slots[div_idx][0])
                del spare_slots[div_idx][0]

class Game(object):
    def __init__(self):
        self.team1 = -1
        self.team2 = -1
        self.ref = -1
        self.div = -1

    def small_str(self):
        div_char = "ricp "
        out = ""
        out += div_char[self.div] + "%2i" % self.team1
        out += 'v' + "%2i" % self.team2
        out += 'r' + "%2i" % self.ref + "  "
        return out

    def csv_str(self):
        if self.div == -1:
            return "SKILLS CLINIC,,"
        div_csv_str = "RICP "
        out = ""
        out += div_csv_str[self.div] + "%s" % (self.team1 + 1)
        out += 'v' + "%s" % (self.team2 + 1)
        out += ',' + div_csv_str[self.div] + "%s" % self.ref + ", "
        return out


class Day(object):
    def __init__(self, facilities):
        from copy import deepcopy
        court = [Game() for _ in range(4)]
        self.courts = [deepcopy(court) for _ in range(5)]
        self.facilities = facilities

    def fitness(self, divisions):
        fitness = sum(self.div_fitness(divisions, div) for div in range(4))
        return fitness

    def div_fitness(self, divisions, div):
        fitness = 0
        for court in self.courts:
            for game in court:
                if div == game.div:
                    team1 = divisions[game.div].teams[game.team1]
                    team2 = divisions[game.div].teams[game.team2]
                    old_count1 = team1.times_team_played[team2.team_idx]
                    old_count2 = team2.times_team_played[team1.team_idx]
                    fitness -= (old_count1 + old_count2) * 2 + 2
        return fitness

    def team_shuffle(self):
        # shuffle all non-reffing teams
        pass # to work on later

    def csv_str(self):
        out = []
        header = "," + ",".join('CT '+ str(idx) + ',Ref' for idx in range(5))
        out += [header]
        time_count = len(self.courts[0])
        for time in range(len(self.courts[0])):
            row = ""
            for court in range(len(self.courts)):
                game_str = self.courts[court][time].csv_str()
                row += game_str
            out += [row]
        out += ["," * 2 * 5]
        return out

    def audit_view(self, rolling_sum_play, rolling_sum_ref):
        out = []
        header = "," + ",".join('CT '+ str(idx + 1) + ',Ref' for idx in range(5))
        header += " ||| Rec Inter Comp Power Playing sums followed by Reffing Sumz"
        out += [header]
        time_count = len(self.courts[0])
        for time in range(len(self.courts[0])):
            row = ""
            for court in range(len(self.courts)):
                game = self.courts[court][time]
                game_str = game.csv_str()
                rolling_sum_ref[game.div][game.ref] += 1
                rolling_sum_play[game.div][game.team1] += 1
                rolling_sum_play[game.div][game.team2] += 1
                row += game_str
            play_str = ""
            ref_str = ""
            for div_idx in range(4):
                play_str += ",,," + ",".join([(str(num)) for num in rolling_sum_play[div_idx]])
                play_str += ",,," + ",".join([(str(num)) for num in rolling_sum_ref[div_idx]])
            out += [row + play_str + ref_str]
        out += ["," * 2 * 5]
        return out

class Division(object):
    def __init__(self, team_count):
        self.teams = []
        self.current_fitness = -1
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
