

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
        out += ',' + div_csv_str[self.div] + "%s" % (self.ref + 1) + ", "
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
                play_str += ",,PLAY DATA," + ",".join([(str(num)) for num in rolling_sum_play[div_idx]])
                ref_str += ",,REF DATA," + ",".join([(str(num)) for num in rolling_sum_ref[div_idx]])
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

    def teams_least_played(self):
        min_plays = min((played for played in self.times_team_played))
        return [team_idx for team_idx, played in enumerate(self.times_team_played)
                if played == min_plays]
