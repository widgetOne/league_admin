from model import init_value


def list_filter(primary, filter):
    both = [team for team in primary if team in filter]
    if (len(both) > 0):
        return list(both)
    else:
        return primary

class Schedule(object):
    time_string = ['6pm', '7pm', '8pm', '9pm']
    rec_first = True
    # [{'times': 4, 'courts': 5},
    # {'time': 2, 'court': 1, 'team1': (1, 2), 'team2': (1, 12), 'ref': (1, 8)},
    # {'time': 2, 'court': 1, 'team1': (1, 2), 'team2': (1, 12)},
    # {...]
    def __init__(self, league, team_counts, facs):
        from model import Division
        self.team_counts = team_counts
        self.daycount = len(facs)
        self.divisions = [Division(count, self.daycount) for count in team_counts]
        self.division_count = len(team_counts)
        self.max_fitness = 0
        self.league = league
        self.courts = 5  # todo make dynamic
        self.times = 4  # todo make dynamic
        self.games_per_team = self.daycount

        self.div_max_fitness = [init_value for _ in range(4)]
        self.enhance_success = 0
        self.skillz_clinic_count()

        self.days = []

        for day_idx in range(self.daycount):
            day = self.make_day(facs[day_idx], day_num=day_idx)
            #### self.add_day_to_division_history(day)
            self.days.append(day)
        self.fitness_structure = sum((day.fitness_str() for day in self.days))

    def __repr__(self):
        out = []
        for day in self.days:
            out += day.csv_str()
        return "\n".join(out)

    def gen_csv(self, loc):
        with open(loc, "w") as csv_file:
            print(self.__repr__(), file=csv_file)

    def new_fitness(self):
        self.fitness_structure = sum((day.fitness_str() for day in self.days))
        return self.fitness_structure.value()

    def new_fitness_div(self, div_idx):
        return sum((day.fitness_str() for day in self.days)).div_value(div_idx)

    def new_fitness_div_list(self):
        sch_fitness = sum((day.fitness_str() for day in self.days))
        return [sch_fitness.div_value(idx) for idx in range(self.division_count)]

    def new_fitness_error_breakdown(self):
        sch_fitness = sum((day.fitness_str() for day in self.days))
        return sch_fitness.error_breakdown()

    def make_audit_structures(self):
        from copy import deepcopy
        rolling_sum_play = []
        rolling_sum_ref = []
        total_use = []
        for div_idx in range(self.division_count):
            div_arr = [0] * self.team_counts[div_idx]
            rolling_sum_play.append(deepcopy(div_arr))
            rolling_sum_ref.append(deepcopy(div_arr))
            total_use.append(deepcopy(div_arr))
        return rolling_sum_play, rolling_sum_ref, total_use

    def write_audit_file(self, out_file_path):
        audit_text = self.get_audit_text()
        with open(out_file_path, "w") as csv_file:
            print("\n".join(audit_text), file=csv_file)

    def get_audit_text(self):
        from copy import deepcopy
        # todo: this summation logic could be integrated with fitness.py's
        rolling_sum_play, rolling_sum_ref, total_use = self.make_audit_structures()
        out = ['audit of cumulative plays and refs by team']
        for day in self.days:
            out += day.audit_view(rolling_sum_play, rolling_sum_ref)
        out += ['audit report of total play by each team at each time']
        for day in self.days:
            out += day.audit_total_use_view(total_use)
        out += []
        out += ['final reports']
        play_str = ''
        ref_str = ''
        for div_idx in range(len(self.team_counts)):
            play_str += ",,PLAY DATA," + ",".join([(str(num)) for num in rolling_sum_play[div_idx]])
            ref_str += ",,REF DATA," + ",".join([(str(num)) for num in rolling_sum_ref[div_idx]])
        out += [play_str]
        out += [ref_str]
        out += []
        out += ["Number of times a team has played another team: rec, In, Cmp, Pw, P+"]
        for div_idx in range(len(self.team_counts)):
            for team_idx in range(self.team_counts[div_idx]):
                team = self.divisions[div_idx].teams[team_idx]
                row = ",".join([str(num) for num in team.times_team_played])
                out += [row]
    #    out += ["team play w time"]
    #    for div_idx in range(4):
    #        out += ["team schedules for division %s" % (div_idx + 1)]
    #        for team in self.divisions[div_idx].teams:
    #        ###    history = ','.join(team.times_team_played) qwer
    #            hist = ','.join([str(num) for num in self.div_team_times[div_idx][team.team_idx]])
    #            out += ['team %s games w time = %s' % (int(team.team_idx), hist)]
        out += []
        out += ['bye view']
        for div_idx in range(4):
            out += ["division %s" % div_idx]
            for team_idx in range(self.team_counts[div_idx]):
                team = self.divisions[div_idx].teams[team_idx]
                row = ",".join([str(num) for num in team.games_per_day])
                out += [row]
        return out

    def remake_worst_day(self, count):
        days_fitness = [(idx, day.fitness(self.divisions)) for idx, day in enumerate(self.days)]
        days_fitness.sort(key=lambda x: x[1])
        worst_days = [days_fitness[idx][0] for idx in range(count)]
        fitness = self.try_remake_days(worst_days)
        return fitness

    ### not currently used
    def try_remake_div_days(self, div_idx, day_indexs):
        from copy import deepcopy
        origional_days = deepcopy(self.days)
        origional_division = deepcopy(self.divisions)
        origional_fitness = self.fitness(self.league.games_per_div)
        for day_idx in day_indexs:
            self.subtract_day_from_division_history(self.days[day_idx])
        for day_idx in day_indexs:
            new_day = self.make_day(self.days[day_idx].facilities,
                                    old_day=self.days[day_idx])
            #self.add_day_to_division_history(new_day)
            self.days[day_idx] = new_day
        new_fitness = self.fitness(self.league.games_per_div)
        if origional_fitness > new_fitness:
            self.days = origional_days
            self.divisions = origional_division
            new_fitness = origional_fitness
        return new_fitness

    def try_remake_days(self, day_indexes):
        from copy import deepcopy
        #qwer
        origional_days = deepcopy(self.days)
        origional_division = deepcopy(self.divisions)
        origional_fitness = self.new_fitness()
        for day_idx in day_indexes:
            self.subtract_day_from_division_history(self.days[day_idx])
        for day_idx in day_indexes:
            new_day = self.make_day(self.days[day_idx].facilities,
                                    old_day=self.days[day_idx])
            self.days[day_idx] = new_day
        new_fitness = self.new_fitness()
        if origional_fitness > new_fitness:
            self.days = origional_days
            self.divisions = origional_division
            new_fitness = origional_fitness
        return new_fitness

    def try_remake_days_new_method(self, day_indexs):
        from copy import deepcopy
        origional_days = deepcopy(self.days)
        origional_division = deepcopy(self.divisions)
        origional_fitness = self.fitness(self.league.games_per_div)
        for day_idx in day_indexs:
            self.subtract_day_from_division_history(self.days[day_idx])
        for day_idx in day_indexs:
            new_day = self.make_day(self.days[day_idx].facilities,
                                    old_day=self.days[day_idx])
            self.add_day_to_division_history(new_day)
            self.days[day_idx] = new_day
        new_fitness = self.fitness(self.league.games_per_div)
        if origional_fitness > new_fitness:
            self.days = origional_days
            self.divisions = origional_division
            new_fitness = origional_fitness
        return new_fitness

    def make_day(self, fac, day_num=None, old_day=None):
        from model import Day
        if day_num == None:
            day_num = old_day.num
        day = Day(fac, day_num)
        for div_idx, div in enumerate(self.divisions):
            try:
                if self.fitness_structure.div_value(div_idx) == 0:
                    if old_day != None:
                        day.import_div_games(div_idx, old_day)
                        self.add_day_to_division_history(day, div_idx=div_idx)
                        continue
            except:
                pass
            day.schedule_div_players_then_refs(fac, div_idx, div)
        return day

    def fitness(self, total_games):
        from math import pow
        bye_worth = 75
        if self.max_fitness == 0:
            # todo: max value should be calculated w the schedule
            self.div_max_fitness = []
            for div_idx, div_teams in enumerate(self.team_counts):
                div_fitness = 0
                if (self.days[0].facilities.refs == True):
                    # adjust value to use total games
                    total_reffings = total_games[div_idx]
                    max_ref_teams = total_reffings % div_teams
                    min_ref_teams = div_teams - max_ref_teams
                    min_ref = total_reffings // div_teams
                    max_ref = min_ref + 1
                    div_ref_max_fitness = min_ref_teams * pow(min_ref, 2) + \
                                          max_ref_teams * pow(max_ref, 2)
                    div_fitness -= div_ref_max_fitness
                total_plays = total_games[div_idx]
                total_combinations = div_teams * (div_teams - 1) / 2
                min_plays = total_plays // total_combinations
                max_plays = min_plays + 1
                max_count = total_plays % total_combinations
                min_count = total_combinations - max_count
                loss_to_play_team_v_team = (pow(min_plays, 2) * min_count +
                                pow(max_plays, 2) * max_count) * 2
                div_fitness -= loss_to_play_team_v_team

                total_plays = total_games[div_idx] * 2
                min_plays = total_plays // div_teams
                max_plays = min_plays + 1
                max_count = total_plays % div_teams
                min_count = div_teams - max_count
                loss_to_play = (pow(min_plays, 2) * min_count +
                                pow(max_plays, 2) * max_count)
                div_fitness -= loss_to_play

                bye_count = 0
                for day in self.days:
                    games_per_division = len(day.facilities.div_games[div_idx])
                    bye_count += max(self.team_counts[div_idx] -
                                     games_per_division * 2, 0)
                    # todo:integrate this dynamic bye calculation
                bye_double_max_fitness = bye_count * bye_worth
                div_fitness -= bye_double_max_fitness

            #    if div_idx in [1,3]: # todo, rectify this round robin hack with
            #                         # the regular season schedule logic
            #        ## Add something here about summing up fac games
            #        div_fitness -= 1 # for their extra game
            #        self.max_fitness -= 1 # for their extra game
            #        # todo, make this more unit testible
                self.div_max_fitness.append(div_fitness)
                self.max_fitness += div_fitness
        fitness = 0
        self.div_team_times = []
        for div_idx in range(4):
            self.div_team_times.append([[0]*16 for _
                                        in range(self.team_counts[div_idx])])
        for court in self.days[0].courts:
            for time, game in enumerate(court):
                if game.div >= 0:
                    self.div_team_times[game.div][game.team1][time] += 1
                    self.div_team_times[game.div][game.team2][time] += 1
        total_bye_count = 0
        for div_idx, div in enumerate(self.divisions):
            games_played = 0
            div_ref_actual_fitness = 0
            div_plays_vs_fitness = 0
            div_total_team_play_fitness = 0
            bye_fitness = 0
            ref_debug = ''
            div_fit = -self.div_max_fitness[div_idx]
            team_count = len(div.teams)
            # double book penalty
            double_use_penalty = 0
            for day in self.days:
                for time in range(len(day.courts[0])):
                    teams_used = [0] * team_count
                    for court in range(len(day.courts)):
                        game = day.courts[court][time]
                        if game.div == div_idx:
                            teams_used[game.team1] += 1
                            teams_used[game.team2] += 1
                            teams_used[game.ref] += 1
                    for team_idx, use_count in enumerate(teams_used):
                        if use_count > 1:
                            double_use_penalty -= 100
        #                    print('div %s team %s is used %s'
        #                          % (div_idx, team_idx, use_count))
            for team_idx, team in enumerate(div.teams):
                if (self.days[0].facilities.refs == True):
                    div_ref_actual_fitness -= pow(team.refs, 2)
                    ref_debug += str(team.refs) + ','
                div_total_team_play_fitness -= pow(sum(team.times_team_played) - 1000, 2)
                for plays in team.times_team_played:
                    if plays < 1000:
                        div_plays_vs_fitness -= pow(plays, 2)
                        games_played += plays
                    else:
                        div_plays_vs_fitness -= 100 * (plays - 1000) # penalty for team v self
                # checking for teams scheduled for two locations at once
                for play_at_time in self.div_team_times[div_idx][team_idx]:
                    if play_at_time > 1:
                        div_fit -= 100
                # value for byes in division
                if div_idx in [1,3]:
                    bye_count = 0
                    for games_on_day in team.games_per_day:
                        if games_on_day == 0:
                            bye_count += 1
                            total_bye_count += 1
                        elif games_on_day < 0:
                            bye_fitness -= 100 * bye_worth
                            total_bye_count += 1
                    bye_fitness -= pow(bye_count, 2) * bye_worth
            div_fit += double_use_penalty
            div_fit += bye_fitness
            div_fit += div_total_team_play_fitness
            div_fit += div_plays_vs_fitness
            div_fit += div_ref_actual_fitness
            fitness += div_fit
            div.current_fitness = div_fit
        # todo: fix this bye count detection logic
        if False and total_bye_count < 9:
            print('creating a file as this thing is Fed up')
            self.write_audit_file('/Users/coulter/Desktop/life_notes/' +
                           '2016_q1/scvl/critical_error_debug.txt')
            raise(Exception('critical error in the bye ' +
                            'count for this schedule'))
        return fitness  # qwer

    def get_sitting_counts(self):
        self.div_team_times = []
        for div_idx in range(len(self.team_counts)):
            self.div_team_times.append([[0] * self.league.ntimes
                                        for _ in range(
                    self.team_counts[div_idx])])
        for court in self.days[0].courts:
            for time, game in enumerate(court):
                if game.div >= 0:
                    self.div_team_times[game.div][game.team1][time] += 1
                    self.div_team_times[game.div][game.team2][time] += 1

        sitting_counts = [0] * 8
        for div_idx in range(len(self.team_counts)):
            for team_idx in range(self.divisions[div_idx].team_count):
                last_play = init_value
                play_v_time = self.div_team_times[div_idx][team_idx]
                for time, plays in enumerate(play_v_time):
                    if plays:
                        if last_play == init_value:
                            last_play = time
                        else:
                            sit_time = time - last_play - 1
                            sitting_counts[sit_time] += 1
                            last_play = time
        return sitting_counts

    def sitting_fitness(self):
        '''returns the total number of games sat by all teams'''
        sit_fitness = 0
        long_sit = 0

        sitting_counts = self.get_sitting_counts()
        bad = -999999
        fitness_func = [
            ('sitting is sitting', [0, -15, -30, -45, -60, -75, -90]),
            ('sitting is sitting <h', [0, -1, -2, -3, bad, bad, bad]),
            ('sitting is sitting <45', [0, -1, -2, bad, bad, bad, bad]),
            ('longer is worse quad', [0, -1, -4, -9, -16, -25, -36]),
            ('long sits worse quad', [0, 0, -1, -4, -9, -16, -25]),
            ('min 45 minutes', [0, 0, -2, -200, bad, bad, bad]),
        ]
        count = sum(sitting_counts)
        sum_prod = sum(time * count for time, count in enumerate(sitting_counts))
        average = sum_prod / count * 4
        long_sit = sitting_counts[3]
        results = {}
        for name, func in fitness_func:
            fitness = sum((a * b for a, b in zip(func, sitting_counts)))
            ave = fitness / sum(self.team_counts)
            result = {'fitness': fitness, 'sits': sitting_counts, 'func': func,
                      'ave': ave}
            results[name] = result
        return results

    def add_day_to_division_history(self, day, div_idx=None, sign=1):
        for court_idx, court in enumerate(day.courts):
            for game in court:
                if (game.div == init_value):
                    continue
                if div_idx != None and div_idx!= game.div:
                    continue
                self.divisions[game.div].teams[game.team1].times_team_played[game.team2] += sign
                self.divisions[game.div].teams[game.team2].times_team_played[game.team1] += sign
                if game.ref != init_value:
                    self.divisions[game.div].teams[game.ref].refs += sign
                self.divisions[game.div].teams[game.team1].games_per_day[day.num] += sign
                self.divisions[game.div].teams[game.team2].games_per_day[day.num] += sign

    def subtract_day_from_division_history(self, day):
        self.add_day_to_division_history(day, sign=-1)

    def skillz_clinic_count(self):
        # The number of skillz clinics is the number of open game slots
        total_slots = self.daycount * self.courts * self.times
        total_games = self.games_per_team * sum(self.team_counts) / 2 # 2 teams per game
        self.skillz_clinics = total_slots - total_games
        print("There will be %s skillz clinics in this schedule"
              % self.skillz_clinics)

    def create_json_schedule(self):
        import json
        sch_obj = []
        for day in self.days:
            court_list = []
            for court in range(len(day.courts)):
                time_list = []
                for time in range(len(day.courts[0])):
                    game_dict = day.courts[court][time].gen_dict()
                    time_list.append(game_dict)
                court_list.append(time_list)
            sch_obj.append(court_list)
        out = json.dumps(sch_obj)
        return out

def gen_schedule_from_json(json_input):
    import json
    #out = Schedule()

def load_reg_schedule():
    import pickle
    path = '/Users/coulter/Desktop/life_notes/2016_q1/scvl/'
    tag = '2016-01-22a_'
    sch_py_obj = path + tag + 'python_file_obj.pickle'
    with open(sch_py_obj,'rb') as sch_file:
        schedule = pickle.load(sch_file)
        return schedule

def load_playoff_schedule():
    pass

if __name__ == '__main__':
    sch = load_reg_schedule()
    json_sch = sch.create_json_schedule()
    print(json_sch)
    sch2 = gen_schedule_from_json(json_sch)