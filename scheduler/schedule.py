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

        self.days = []

        for day_idx in range(self.daycount):
            day = self.make_day(facs[day_idx], day_num=day_idx)
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

    def fitness(self):
        self.fitness_structure = sum((day.fitness_str() for day in self.days))
        return self.fitness_structure.value()

    def fitness_div(self, div_idx):
        return sum((day.fitness_str() for day in self.days)).div_value(div_idx)

    def fitness_div_list(self):
        sch_fitness = sum((day.fitness_str() for day in self.days))
        return [sch_fitness.div_value(idx) for idx in range(self.division_count)]

    def fitness_error_breakdown(self):
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
        out += []
        out += ['bye view']
        for div_idx in range(len(self.team_counts)):
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
        original_days = deepcopy(self.days)
        original_division = deepcopy(self.divisions)
        original_fitness = self.fitness(self.league.games_per_div)
        for day_idx in day_indexs:
            self.subtract_day_from_division_history(self.days[day_idx])
        for day_idx in day_indexs:
            new_day = self.make_day(self.days[day_idx].facilities,
                                    old_day=self.days[day_idx])
            self.days[day_idx] = new_day
        fitness = self.fitness(self.league.games_per_div)
        if original_fitness > fitness:
            self.days = original_days
            self.divisions = original_division
            fitness = original_fitness
        return fitness

    def try_remake_days(self, day_indexes):
        from copy import deepcopy
        original_days = deepcopy(self.days)
        original_division = deepcopy(self.divisions)
        original_fitness = self.fitness()
        for day_idx in day_indexes:
            self.subtract_day_from_division_history(self.days[day_idx])
        for day_idx in day_indexes:
            new_day = self.make_day(self.days[day_idx].facilities,
                                    old_day=self.days[day_idx])
            self.days[day_idx] = new_day
        fitness = self.fitness()
        if original_fitness > fitness:
            self.days = original_days
            self.divisions = original_division
            fitness = original_fitness
        return fitness

    def try_remake_days_new_method(self, day_indexs):
        from copy import deepcopy
        original_days = deepcopy(self.days)
        original_division = deepcopy(self.divisions)
        original_fitness = self.fitness(self.league.games_per_div)
        for day_idx in day_indexs:
            self.subtract_day_from_division_history(self.days[day_idx])
        for day_idx in day_indexs:
            new_day = self.make_day(self.days[day_idx].facilities,
                                    old_day=self.days[day_idx])
            self.add_day_to_division_history(new_day)
            self.days[day_idx] = new_day
        fitness = self.fitness(self.league.games_per_div)
        if original_fitness > fitness:
            self.days = original_days
            self.divisions = original_division
            fitness = original_fitness
        return fitness

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

    def get_sitting_counts(self):
        from copy import deepcopy
        from fitness import add_lists
        self.div_team_times = []
        list_of_times = [0] * self.league.ntimes
        total_sits = [0] * 8
        for div_idx in range(len(self.team_counts)):
            team_count = self.team_counts[div_idx]
            div_times = [deepcopy(list_of_times) for _ in range(team_count)]
            self.div_team_times.append(div_times)
        for court in self.days[0].courts:
            for time, game in enumerate(court):
                if game.div >= 0:
                    self.div_team_times[game.div][game.team1][time] += 1
                    self.div_team_times[game.div][game.team2][time] += 1
        #for div_idx in range(len(self.team_counts)):
        #    div_sits = [sitting_counts for _ in range(len(self.team_counts[div_idx))]]
        #league_sits = [div_sits for _ in range(len(self.team_counts))]
        team_sits = []
        for div_idx in range(len(self.team_counts)):
            for team_idx in range(self.divisions[div_idx].team_count):
                last_play = init_value
                play_v_time = self.div_team_times[div_idx][team_idx]
                temp_sits = [0] * 8
                team_total_sit = 0
                for time, plays in enumerate(play_v_time):
                    if plays:
                        if last_play == init_value:
                            last_play = time
                        else:
                            sit_time = time - last_play - 1
                            temp_sits[sit_time] += 1
                            last_play = time
                            team_total_sit += sit_time * 15
                team_sits.append(temp_sits)
                total_sits = add_lists(total_sits, temp_sits)
        return total_sits, team_sits

    def sitting_fitness(self):
        '''returns the total number of games sat by all teams'''
        sit_fitness = 0
        long_sit = 0

        sitting_counts, team_sits = self.get_sitting_counts()
        bad = -999999
        # todo: refactor to a team centric fitness
        # todo: calculation a division-wise fitness
        # todo: have the selection logic pick the best divisional schedule,
        #       not the best schedules that co-enside.
        fitness_func = [
            ('sitting is sitting', [0, -15, -30, -45, -60, -75, -90]),
            ('sitting is sitting <h', [0, -15, -30, -45, bad, bad, bad]),
            ('sitting is sitting <45', [0, -1, -2, bad, bad, bad, bad]),
            ('longer is worse quad', [0, -5, -20, -45, -80, -125, -180]),
            ('long sits worse quad', [0, 0, -1, -4, -9, -16, -25]),
            ('min 45 minutes', [0, 0, -2, -200, bad, bad, bad]),
        ]
        time_cypher = [0,15,30,45,   60,75,90,115,   130,145]
        team_wise_penality = [-5000,0,0,0,   0,-10,bad,bad,   bad,bad]
        count = sum(sitting_counts)
        sum_prod = sum(time * count for time, count in enumerate(sitting_counts))
        average = sum_prod / count * 4
        results = {}
        # calc team-wise sitting function
        team_penalty_total = 0
        for team_sit in team_sits:
            team_sit_total = sum((a * b for a, b in zip(team_sit, time_cypher)))
            team_penalty_total += team_wise_penality[int(team_sit_total / 15)]
        teamwise_fitness = team_penalty_total / len(team_sits)
        # calc the total sit fitness for various functions
        for name, func in fitness_func:
            raw_fitness = sum((a * b for a, b in zip(func, sitting_counts)))
            fitness = raw_fitness - teamwise_fitness
            ave = fitness / sum(self.team_counts)
            result = {'fitness': fitness, 'sits': sitting_counts, 'func': func,
                      'ave': ave, 'team_sits': team_sits,
                      'teamwise_fitness': teamwise_fitness,
                      'raw_fitness': raw_fitness}
            results[name] = result
        return results

    def add_day_to_division_history(self, day, div_idx=None, sign=1):
        for court_idx, court in enumerate(day.courts):
            for game in court:
                if (game.div == init_value):
                    continue
                if div_idx != None and div_idx!= game.div:
                    continue
                fake_values = [init_value, -1]
                if game.team1 not in fake_values and game.team2 not in fake_values:
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

    def add_reffing_to_day(self, day_idx):
        for div_idx, div in enumerate(self.divisions):
            self.days[day_idx].add_reffing(div_idx, div)

    def clear_all_reffing(self):
        for day in self.days:
            court_list = day.courts
            for court in court_list:
                for game in court:
                    game.ref = init_value
        for div in self.divisions:
            for team in div.teams:
                team.refs = 0

    def add_reffing(self):
        max_number_of_attempts = 500  # not expected to happen
        for _ in range(max_number_of_attempts):
            self.clear_all_reffing()
            for day_idx in range(len(self.days)):
                self.add_reffing_to_day(day_idx)
            print(self.fitness())
            if self.fitness() == 0:
                break

    def switch_teams(self, div_idx, team1, team2):
        teams = [team1, team2]
        otherer = create_get_other(teams)
        for day_idx, day in enumerate(self.days):
            for court_idx, court in enumerate(day.courts):
                for time_idx, game in enumerate(court):
                    if game.div == div_idx:
                        if game.team1 in teams:
                            game.team1 = otherer(game.team1)
                        if game.team2 in teams:
                            game.team2 = otherer(game.team2)
                        if game.ref in teams:
                            game.ref = otherer(game.ref)
                    self.days[day_idx].courts[court_idx][time_idx] = game

def create_get_other(list):
    def other(current):
        if list[0] == current:
            return list[1]
        else:
            return list[0]
    return other

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

if __name__ == '__main__':
    sch = load_reg_schedule()
    json_sch = sch.create_json_schedule()
    print(json_sch)
    sch2 = gen_schedule_from_json(json_sch)