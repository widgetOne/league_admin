

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
        from model import Division
        self.team_counts = team_counts
        self.divisions = [Division(count) for count in team_counts]
        self.division_count = len(team_counts)
        self.max_fitness = 0
        self.daycount = len(facs)
        self.courts = 5
        self.times = 4
        self.games_per_team = self.daycount

        self.div_max_fitness = [-1 for _ in range(4)]
        self.enhance_success = 0
        self.skillz_clinic_count()

        self.days = []

        for day_idx in range(self.daycount):
            day = self.make_day(facs[day_idx])
            self.add_day_to_division_history(day)
            self.days.append(day)

    def gen_csv(self, loc):
        out = []
        for day in self.days:
            out += day.csv_str()
        with open(loc, "w") as csv_file:
            print("\n".join(out), file=csv_file)

    def gen_audit(self, loc):
        from copy import deepcopy
        rolling_sum_play = []
        rolling_sum_ref = []
        for div_idx in range(4):
            div_arr = [0] * self.team_counts[div_idx]
            rolling_sum_play.append(deepcopy(div_arr))
            rolling_sum_ref.append(deepcopy(div_arr))
        out = []
        for day in self.days:
            out += day.audit_view(rolling_sum_play, rolling_sum_ref)
        out += []
        out += ["Number of times a team has played another team: rec, In, Cmp, Pw"]
        for div_idx in range(4):
            for team_idx in range(self.team_counts[div_idx]):
                team = self.divisions[div_idx].teams[team_idx]
                row = ",".join([str(num) for num in team.times_team_played])
                out += [row]
        out += ["team play w time"]
        for div_idx in range(4):
            out += ["team schedules for division %s" % (div_idx + 1)]
            for team in self.divisions[div_idx].teams:
            ###    history = ','.join(team.times_team_played) qwer
                hist = ','.join([str(num) for num in self.div_team_times[div_idx][team.team_idx]])
                out += ['team %s games w time = %s' % (int(team.team_idx), hist)]
        with open(loc, "w") as csv_file:
            print("\n".join(out), file=csv_file)

    def remake_worst_day(self, count):
        days_fitness = [(idx, day.fitness(self.divisions)) for idx, day in enumerate(self.days)]
        days_fitness.sort(key=lambda x: x[1])
        worst_days = [days_fitness[idx][0] for idx in range(count)]
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
            new_day = self.make_day(self.days[day_idx].facilities,
                                    self.days[day_idx])
            self.add_day_to_division_history(new_day)
            self.days[day_idx] = new_day
        new_fitness = self.fitness()
    #    print("old fitness was %s and new fitness is %s: "
    #          % (origional_fitness, new_fitness), end="")
        if origional_fitness > new_fitness:
    #        print("using OLD schedule")
            self.days = origional_days
            self.divisions = origional_division
            new_fitness = origional_fitness

        return new_fitness

    def make_day(self, fac, old_day=None):
        from model import Day
        tries = 4
        best_day = False
        for _ in range(tries):
            day = Day(fac)
            # first, complete minimum games
            for div_idx, div in enumerate(self.divisions):
                if div.current_fitness == 0:
                    if old_day != None:
                        day.import_div_games(div_idx, old_day)
                        continue
                day.schedule_div_ref_then_play(fac, div_idx, div)  # YOYO
         ###       day.schedule_div_play_then_ref(fac, div_idx, div)  # todo: need a perminent solution here
                # probably an efficient hybrid methods for round robin and regular

            if best_day:
                best_day_fitness = best_day.fitness(self.divisions)
                if day.fitness(self.divisions) > best_day_fitness:
                    best_day = day
            else:
                best_day = day
        return best_day

    def fitness(self):
        from math import pow
        if self.max_fitness == 0:
            self.div_max_fitness = []
            for div_idx, div_teams in enumerate(self.team_counts):
                div_fitness = 0
                if (self.days[0].facilities.refs == True):
                    min_ref = self.games_per_team // 2
                    max_ref = self.games_per_team // 2 + self.games_per_team % 2
                    min_ref_teams = div_teams // 2
                    max_ref_teams = div_teams - min_ref_teams
                    div_ref_max_fitness = min_ref_teams * pow(min_ref, 2) + \
                                          max_ref_teams * pow(max_ref, 2)
                    div_fitness -= div_ref_max_fitness
                others = div_teams - 1
                min_plays = self.games_per_team // others
                max_plays = min_plays + 1
                max_teams = self.games_per_team - others * min_plays
                min_teams = others - max_teams
                loss_per_team = pow(min_plays, 2) * min_teams + pow(max_plays, 2) * max_teams
            #    if div_idx in [1,3]: # todo, rectify this round robin hack with
            #                         # the regular season schedule logic
            #        ## Add something here about summing up fac games
            #        div_fitness -= 1 # for their extra game
            #        self.max_fitness -= 1 # for their extra game
            #        # todo, make this more unit testible
                div_fitness -= loss_per_team * div_teams
                self.div_max_fitness.append(div_fitness)
                self.max_fitness -= div_fitness
        fitness = 0
        self.div_team_times = []
        for div_idx in range(4):
            self.div_team_times.append([[0]*16 for _ in range(self.team_counts[div_idx])])
        for court in self.days[0].courts:
            for time, game in enumerate(court):
                if game.div >= 0:
                    self.div_team_times[game.div][game.team1][time] += 1
                    self.div_team_times[game.div][game.team2][time] += 1
        for div_idx, div in enumerate(self.divisions):
            div_fit = -self.div_max_fitness[div_idx]
            for team_idx, team in enumerate(div.teams):
                if (self.days[0].facilities.refs == True):
                    div_fit -= pow(team.refs, 2)
                for plays in team.times_team_played:
                    if plays < 1000:
                        div_fit -= pow(plays, 2)
                    else:
                        div_fit -= 100 * (plays - 1000) # penalty for team v self
                for play_at_time in self.div_team_times[div_idx][team_idx]:
                    if play_at_time > 1:
                        div_fit -= 50
            fitness += div_fit
            div.current_fitness = div_fit
        return fitness

    def sitting_fitness(self):
        '''returns the total number of games sat by all teams'''
        sit_fitness = 0
        long_sit = 0
        for div_idx in range(4):
            for team_idx in range(self.divisions[div_idx].team_count):
                start = -1
                consecutive = 0
                count = 0
                three_consec_found = False
                play_v_time = self.div_team_times[div_idx][team_idx]
                for time, plays in enumerate(play_v_time):
                    if plays > 0:
                        if start == -1:
                            start = time
                        end = time
                        count += 1
                        consecutive = 0
                        if three_consec_found:
                            long_sit += 1
                            three_consec_found = False
                    else:
                        if start >= 0:
                            consecutive += 1
                    if consecutive == 3:
                        three_consec_found = True
                sit_fitness -= float(end - start - count + 1)
        return round(sit_fitness, 1), long_sit

    def add_day_to_division_history(self, day, sign=1):
        for court_idx, court in enumerate(day.courts):
            for game in court:
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