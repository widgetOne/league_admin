
init_value = -999999

class Game(object):
    def __init__(self, team1=init_value, team2=init_value,
                 ref=init_value, div=init_value,
                 time=init_value, court=init_value):
        self.team1 = team1
        self.team2 = team2
        self.ref = ref
        self.div = div
        self.time = time
        self.court = court

    def small_str(self):
        div_char = "ricp "
        out = ""
        out += div_char[self.div] + "%2i" % self.team1
        out += 'v' + "%2i" % self.team2
        out += 'r' + "%2i" % self.ref + "  "
        return out


    def csv_str(self):
        if self.div == init_value:
            return "WARM UP  ,,"
        div_csv_str = ['REC', 'INT', 'COM', 'POW', 'P+ ', '']
        teams = [self.team1 + 1, self.team2 + 1]
        out = "{} {}v{}".format(div_csv_str[self.div], min(teams), max(teams))
        if self.ref > -1:
            ref_str = self.ref + 1
        else:
            ref_str = 'X'
        out += ',' + div_csv_str[self.div] + " %s" % (ref_str) + ", "
        return out


    def gen_dict(self):
        out = {
                'team1': self.team1,
                'team2': self.team2,
                'ref': self.ref,
                'div': self.div,
                'time': self.time,
                'court': self.court,
        }
        return out


class Day(object):
    def __init__(self, facilities, day_num):
        from copy import deepcopy
        self.courts = []
        for court_idx in range(facilities.court_count):
            self.courts.append([Game(time=idx, court=court_idx)
                                for idx in range(facilities.time_count)])
        self.facilities = facilities
        self.num = day_num

    def games(self):
        all_games = []
        for court in self.courts:
            all_games += court
        return all_games

    def fitness_str(self):
        from fitness import ScheduleFitness
        return ScheduleFitness(self.facilities, self.games())

    def isolated_new_fitness(self):
        return self.fitness_str().value()

    def fitness(self, divisions):
        fix_this_team_num_to_be_dynamic = 5
        fitness = sum(self.div_fitness(divisions, div) for div in range(fix_this_team_num_to_be_dynamic))
        return fitness

    def set_refs_in_div(self, history):
        pass

    def div_fitness(self, divisions, div_idx):
        fitness = 0
        team_count = len(divisions[div_idx].teams)
        played_at_time = [0] * len(divisions[div_idx].teams)
        div = divisions[div_idx]
        new_games = [(sum(team.times_team_played) - 1000) for team in div.teams]
        for court in self.courts:
            for game in court:
                if div_idx == game.div:
                    team1 = divisions[game.div].teams[game.team1]
                    team2 = divisions[game.div].teams[game.team2]
                    new_games[team1.team_idx] += 1
                    new_games[team2.team_idx] += 1
                    old_count1 = team1.times_team_played[team2.team_idx]
                    old_count2 = team2.times_team_played[team1.team_idx]
            #        value -= (old_count1 + old_count2) * 2 + 2
                    played_at_time[team1.team_idx] += 1
                    played_at_time[team2.team_idx] += 1
                    if team1 == team2:
                        fitness -= 100
        for count in new_games:
            fitness -= count * count
        for time in range(len(self.courts[0])):
            teams_used = [0] * team_count
            for court in range(len(self.courts)):
                game = self.courts[court][time]
                if game.div == div_idx:
                    teams_used[game.team1] += 1
                    teams_used[game.team2] += 1
                    if game.ref != init_value:
                        teams_used[game.ref] += 1
            for team_idx, use_count in enumerate(teams_used):
                if use_count > 1:
                    double_use_penalty = 100
                    fitness -= double_use_penalty
        return fitness

    def csv_str(self):
        out = []
        header = ",".join('CT '+ str(idx+1) + ',Ref' for idx in range(5))
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
        header = ",".join('CT '+ str(idx + 1) for idx in range(5))
        header += ",  ||| Rec Inter Comp Power Playing" +\
                  " sums followed by Reffing Sums"
        out += [header]
        time_count = len(self.courts[0])
        for time in range(len(self.courts[0])):
            row = ""
            for court in range(len(self.courts)):
                game = self.courts[court][time]
                game_str = game.csv_str()
                if (game.div >= 0):
                    if (game.ref >= 0):
                        rolling_sum_ref[game.div][game.ref] += 1
                    rolling_sum_play[game.div][game.team1] += 1
                    rolling_sum_play[game.div][game.team2] += 1
                row += game_str
            play_str = ""
            ref_str = ""
            for div_idx in range(5):
                play_str += ",,PLAY DATA," + ",".join([(str(num)) for num in rolling_sum_play[div_idx]])
                ref_str += ",,REF DATA," + ",".join([(str(num)) for num in rolling_sum_ref[div_idx]])
            out += [row + play_str + ref_str]
        out += ["," * 2 * 5]
        return out

    def audit_total_use_view(self, total_use):
        out = []
    #    header = "," + ",".join('CT '+ str(idx + 1) + ',Ref' for idx in range(5))
        header = ",".join('CT '+ str(idx + 1) for idx in range(5))
        header += ",  ||| Rec Inter Comp Power Playing sums followed by Reffing Sums"
        out += [header]
        time_count = len(self.courts[0])
        for time in range(len(self.courts[0])):
            for time_idx in range(len(total_use)):
                for team_idx in range(len(total_use[time_idx])):
                    total_use[time_idx][team_idx] = 0
            row = ""
            for court in range(len(self.courts)):
                game = self.courts[court][time]
                game_str = game.csv_str()
                if (game.div >= 0):
                    if (game.ref >= 0):
                        total_use[game.div][game.ref] += 1
                        total_use[game.div][game.team1] += 1
                        total_use[game.div][game.team2] += 1
                row += game_str
            use_str = ""
            for div_idx in range(5):
                use_str += ",,Total Use," + ",".join([(str(num)) for num in total_use[div_idx]])
            out += [row + use_str]
        out += ["," * 2 * 5]
        return out

    def import_div_games(self, div_idx, old_day):
        from copy import deepcopy
        # copy forward the games from the old day in this div
        for court_idx, court in enumerate(old_day.courts):
            for time_idx, game in enumerate(court):
                if old_day.courts[court_idx][time_idx].div == div_idx:
                    self.courts[court_idx][time_idx] = deepcopy(game)

    def schedule_div_players_then_refs(self, fac, div_idx, div):
        from random import shuffle, choice
        from schedule import list_filter
        game_slots = fac.div_games[div_idx].copy()
        shuffle(game_slots)
        day_idx = fac.day_idx
        # fill in players
        for court, time in game_slots:
            self.courts[court][time].div = div_idx
            # place team 1
            free = self.teams_free_at_time(div_idx, time, div.team_count)
            least_played = div.teams_w_least_play()
            best_list = free
            best_list = list_filter(best_list, least_played)
            team1_idx = choice(best_list)
            self.courts[court][time].team1 = team1_idx
            div.add_play_for_team(team1_idx, day_idx)
            # place team 2
            free = self.teams_free_at_time(div_idx, time, div.team_count)
            team1 = div.teams[team1_idx]
            best_opponent = team1.teams_least_played()
            least_played = div.teams_w_least_play()
            best_list = free
            best_list = list_filter(best_list, least_played)
            best_list = list_filter(best_list, best_opponent)
            team2_idx = choice(best_list)
            self.courts[court][time].team2 = team2_idx
            div.add_play_for_team(team2_idx, day_idx, team1_idx)

    def teams_free_at_time(self, div_idx, time, team_count):
        free = {idx : 0 for idx in range(team_count)}
        for court in self.courts:
            game = court[time]
            if game.div == div_idx:
                free.pop(game.team1, 0)
                free.pop(game.team2, 0)
                free.pop(game.ref, 0)
        return list(free.keys())

    def totals(self):
        totals = {}
        return totals

    def get_free_to_ref(self, div_idx, time):
        potential_refs = set([])
        for delta in [-1, 1]:
            source_time = time + delta
            if 0 <= source_time < self.facilities.time_count:
                for court_idx in range(self.facilities.court_count):
                    game = self.courts[court_idx][source_time]
                    if game.div == div_idx:
                        potential_refs.add(game.team1)
                        potential_refs.add(game.team2)
        for court_idx in range(self.facilities.court_count):
            game = self.courts[court_idx][time]
            if game.div == div_idx:
                potential_refs.discard(game.team1)
                potential_refs.discard(game.team2)
                if game.ref > -1:
                    potential_refs.discard(game.ref)
        return list(potential_refs)

    def add_reffing(self, div_idx, div):
        from random import shuffle, choice
        from schedule import list_filter
        fac = self.facilities
        game_slots = fac.div_games[div_idx].copy()
        shuffle(game_slots)
        day_idx = fac.day_idx
        for court, time in game_slots:
            game = self.courts[court][time]
            ref_options = self.get_free_to_ref(div_idx, time)
            if len(ref_options) == 0:
                raise(Exception('we can\'t seem to find a ref for ' +
                                'time = {}, court = {}, day = {}'.format(court, time, day_idx)))
            best_ref_list = list_filter(ref_options, div.teams_w_least_ref())
            reffing_team = choice(best_ref_list)
            game.ref = reffing_team
            div.teams[reffing_team].refs += 1


class Division(object):
    def __init__(self, team_count, ndays):
        self.teams = []
        self.current_fitness = init_value
        self.team_count = team_count
        for team_idx in range(team_count):
            self.teams.append(Team(team_idx, team_count, ndays))

    def teams_w_least_ref(self):
        min_refs = min([team.refs for team in self.teams])
        return [team_num for team_num, team in enumerate(self.teams)
                if team.refs == min_refs]

    def teams_w_most_play(self):
        max_plays = max([team.games for team in self.teams])
        return [team_num for team_num, team in enumerate(self.teams)
                if team.games == max_plays]

    def teams_w_least_play(self):
        min_plays = min((team.games for team in self.teams))
        return [team_num for team_num, team in enumerate(self.teams)
                if team.games == min_plays]

    def add_play_for_team(self, team_num, day_idx, opponent_num=-1, sign=1):
        self.teams[team_num].games += sign
        self.teams[team_num].games_per_day[day_idx] += sign
        if opponent_num > -1:
            # Don't add opponent games as that was done previously
            self.teams[team_num].times_team_played[opponent_num] += sign
            self.teams[opponent_num].times_team_played[team_num] += sign

    def add_ref_for_team(self, team_num, sign=1):
        self.teams[team_num].refs += sign


class Team(object):
    def __init__(self, team_idx, teams_in_division, ndays):
        time_slots = 4
        self.games = 0
        self.refs = 0
        self.team_idx = team_idx
        ###  self.days_comma_games = []
        ### self.time_slot_count = [0 for _ in range(time_slots)]
        self.games_per_day = [0] * ndays
        self.times_team_played = [0 for _ in range(teams_in_division)]
        self.times_team_played[team_idx] = 1000

    def teams_least_played(self):
        min_plays = min((played for played in self.times_team_played))
        return [team_idx for team_idx, played in enumerate(self.times_team_played)
                if played == min_plays]
