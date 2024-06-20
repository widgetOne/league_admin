from model import init_value, WeirdReffingCollision
import random
import copy
from pprint import pprint
import fitness
import traceback


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

    # todo: this div_idx flag doesn't seem to work yet, for some reason
    def fitness(self, div_idx=None):
        if div_idx is None:
            self.fitness_structure = sum((day.fitness_str() for day in self.days))
        else:
            self.fitness_structure = sum((day.fitness_str(div_idx) for day in self.days))
        return self.fitness_structure.value()

    def fitness_div(self, div_idx):
        return sum((day.fitness_str() for day in self.days)).div_value(div_idx)

    def fitness_div_list(self):
        sch_fitness = sum((day.fitness_str() for day in self.days))
        return [sch_fitness.div_value(idx) for idx in range(self.division_count)]

    def fitness_error_breakdown(self, div_idx=None):
        sch_fitness = sum((day.fitness_str(div_idx=div_idx) for day in self.days))
        return sch_fitness.error_breakdown()

    def fitness_by_day(self):
        return [day.fitness_str().value() for day in self.days]

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

    def get_game_div_count_list(self):
        div_totals = {}
        for day in self.days:
            for court in day.courts:
                for game in court:
                    if game.div > -1:
                        div_totals[game.div] = div_totals.get(game.div, 0) + 1
        output = [0] * (max(div_totals.keys()) + 1)
        for key, value in div_totals.items():
            output[key] = value
        return output

    def get_audit_text(self):
        from copy import deepcopy
        # todo: this summation logic could be integrated with fitness.py's
        rolling_sum_play, rolling_sum_ref, total_use = self.make_audit_structures()
        out = ['\n\nSchedule Audit Report']
        out += ['\nCumulative Plays and Refs by Team']
        out += ['This section displays the schedule along-side running totals of the play/ref for each team']
        out += ['in the league. It is generated programatically, so you can audit its accuracy for specific']
        out += ['teams and areas, and then infer the overall behavior. The final line of this section states']
        out += ['the play and ref totals for each team over the season']
        for day in self.days:
            out += day.audit_view(rolling_sum_play, rolling_sum_ref)
        out += ['\n\n\nCumulative Play / Ref Totals']
        play_str = ''
        ref_str = ''
        for div_idx in range(len(self.team_counts)):
            play_str += ",,PLAY DATA," + ",".join([(str(num)) for num in rolling_sum_play[div_idx]])
            ref_str += ",,REF DATA," + ",".join([(str(num)) for num in rolling_sum_ref[div_idx]])
        out += [play_str]
        out += [ref_str]
        out += ['\n\nTotal Use Audit']
        out += ['This report displays the total use (play and ref) for each team in each time']
        out += ['slot for each day. This is useful for checking that no one is double-booked']
        out += ['(playing on two courts at a time, playing and reffing at the same time, etc']
        for day in self.days:
            out += day.audit_total_use_view(total_use)
        out += ['\n\n\nVs View']
        out += ["Number of times a team has played another team: rec, In, Cmp, Pw, P+"]
        out += ["These are the total times each team will play another team in their own division"]
        out += ["This data is symmetric for obvious reasons. The '1000' values are esentially filler"]
        out += ["for the spaces for a team playing itself."]
        for div_idx in range(len(self.team_counts)):
            for team_idx in range(self.team_counts[div_idx]):
                team = self.divisions[div_idx].teams[team_idx]
                row = ",".join([str(num) for num in team.times_team_played])
                out += [row]
        out += []
        out += ['\n\n\nBye View']
        out += ['Below are the counts of the number of games each team has in a given week']
        for div_idx in range(len(self.team_counts)):
            out += ["division %s" % div_idx]
            for team_idx in range(self.team_counts[div_idx]):
                team = self.divisions[div_idx].teams[team_idx]
                row = ",".join([str(num) for num in team.games_per_day]) + \
                      '  total: {}'.format(sum((1 for num in team.games_per_day if num == 0)))
                out += [row]
        out += ['\n\n\nRepeated Play View\n']
        out += [self.get_sequencial_vs_play_report()]
        out += ['\n\n\nOpen Play Report\n']
        out += [self.get_open_play_report()]
        out += ['\n\n\nDouble Ref Report\n']
        out += [self.get_double_ref_report()]
        out += ['\n\n\nSolution Error']
        out += ['This section reports what is checked for each division, and displays the total number']
        out += ['of errors for each category, for each division. This is basically always all 0.']
        out += [self.solution_debug_data()]
        out += ['\n\n\n\n']
        return '\n'.join(out)

    def get_team_round_robin_audit(self):
        day = self.days[0]
        time_slots = len(day.courts[0])
        div_histories = [[[0] * time_slots for _ in range(count)] for count in self.team_counts]
        for court in day.courts:
            for game_time, game in enumerate(court):
                if game.team1 > -1:
                    div_histories[game.div][game.team1][game_time] += 1
                    div_histories[game.div][game.team2][game_time] += 1
        asdf = '\n\n'.join('\n'.join((','.join((str(game) for game in team_hist)) for team_hist in div_hist)) for div_hist in div_histories)
        return asdf

    def get_sequencial_vs_play_report(self):
        """Collection all the vs games in order and assess how much they repeat.
        This is only really an issue for the smaller leagues (rec and P+)"""
        vs_play = [[[] for _ in range(count)] for count in self.team_counts]
        for day in self.days:
            for court in day.courts:
                for game in court:
                    if game.div not in (init_value, -1):
                        vs_play[game.div][game.team1].append(game.team2)
                        vs_play[game.div][game.team2].append(game.team1)
        vs_repeat_period = [[[] for _ in range(count)] for count in self.team_counts]
        output = '\nDebug of repeats of the same vs match over successive games'
        output += '\nEach line is the readout for one team'
        output += '\nThe first list in a line are the opposing teams for each game and '
        output += '\nthe second list are the successive games before that team is played again.'
        output += '\n(the default for this is 0 if the team is not played again in a season)'
        for div_idx, div_vs_play in enumerate(vs_play):
            output += '\nOutput for division:  {}\n'.format(div_idx)
            for team_idx, team_vs_play in enumerate(div_vs_play):
                for idx1 in range(len(team_vs_play)):
                    for idx2 in range(idx1 + 1, len(team_vs_play)):
                        if team_vs_play[idx1] == team_vs_play[idx2]:
                            vs_repeat_period[div_idx][team_idx].append(idx2 - idx1)
                            break
                    else:
                        vs_repeat_period[div_idx][team_idx].append(0)
                output += ','.join([str(num) for num in vs_play[div_idx][team_idx]]) + '   '
                output += ','.join([str(num) for num in vs_repeat_period[div_idx][team_idx]]) + '\n'
        return output


    def get_open_play_report(self):
        """Generate a report of teams with open play opertunities vs day for debugging"""
        output = '\nDebug of open play opertunties in the schedule.'
        output += '\nFirst, there is a report of what the facilities objects view as open play.'
        output += '\nThen there is the day-by-day running total of the number'
        output += '\nof oppertinies a team has to play open play i.e. when a team has'
        output += '\na game before or after an open play / skills clinic slot'
        output += '\nOpen play slots'
        for idx, day in enumerate(self.days):
            open_play_times = day.facility_day.get_open_play_times()
            output += '\nThe open play oppertunies for day {} are {}'.format(idx, open_play_times)
        output += '\nOpen oppertunities by team'
        total_fit = 0
        for idx, day in enumerate(self.days):
            day_fit = day.fitness_str()
            total_fit += day_fit
            output += '\nOpen play data after day {} is {}'.format(idx, total_fit.open_play_lists())
        return output

    def get_double_ref_report(self):
        """Generate a report of teams with open play opertunities vs day for debugging"""
        output = '\nDebug of double ref metrics. This means one team getting forced'
        output += '\nto ref twice in the same day'
        for idx, day in enumerate(self.days):
            day_fitness = day.fitness_str()
            output += '\ndouble refs for day {}: {}'.format(idx, day_fitness.get_double_ref_lists())
        return output

    '''
    def remake_worst_day(self, count):
        days_fitness = [(idx, day.fitness(self.divisions)) for idx, day in enumerate(self.days)]
        days_fitness.sort(key=lambda x: x[1])
        worst_days = [days_fitness[idx][0] for idx in range(count)]
        fitness = self.try_remake_days(worst_days)
        return fitness
    '''

    def try_remake_play_imbalance(self, div_idx):
        """This routine enqueues all days with non-mean number of game plays to be remade"""
        # todo 2018-09-09: not completed
        days_to_remake = random.sample(all_day_indexes, day_remake_count)
        self.try_remake_div_days(div_idx, days_to_remake)


    def try_remake_a_few_random_days(self, div_idx, day_remake_count):
        all_day_indexes = range(len(self.days))
        days_to_remake = random.sample(all_day_indexes, day_remake_count)
        self.try_remake_div_days(div_idx, days_to_remake)


    #def
    # todo: create a mutation subroutine which tries to


    def try_remake_div_days(self, div_idx, day_indexes):
        from copy import deepcopy
        # todo 2018-09-09: can I accellerate things by making this more focused?
        day_backups = {day_idx: deepcopy(self.days[day_idx]) for day_idx in day_indexes}
        original_division = deepcopy(self.divisions[div_idx])
        # todo: there should be a way to focus this and the later fitness function to just this div
        original_fitness = self.fitness()
        for day_idx in day_indexes:
            self.subtract_day_from_division_history(self.days[day_idx])
        for day_idx in day_indexes:
            new_day = self.make_day(self.days[day_idx].facility_day,
                                    old_day=self.days[day_idx], target_div_idx=div_idx)
            self.days[day_idx] = new_day
        fitness = self.fitness()
        # fudge factor to allow more drift in solution, to avoid local stability issues
        local_stability_avoidance_fudge_factor = 0
        if original_fitness > fitness + local_stability_avoidance_fudge_factor:
            for day_idx in day_indexes:
                self.days[day_idx] = day_backups[day_idx]
            self.divisions[div_idx] = original_division
            fitness = original_fitness
        return fitness

    '''
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
    '''

    # todo: not currently used. use or delete
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

    def make_day(self, fac, day_num=None, old_day=None, target_div_idx=None):
        from model import Day
        if day_num == None:
            day_num = old_day.num
        day = Day(fac, day_num)
        if target_div_idx is not None:
            division_list = [(target_div_idx, self.divisions[target_div_idx])]
        else:
            division_list = list(enumerate(self.divisions))  # todo: use or delete this code. Woudl probably need a deep copy up above
        for div_idx, div in enumerate(self.divisions):
            try:
                if self.fitness_structure.div_value(div_idx) == 0 or (target_div_idx is not None and target_div_idx != div_idx):
                    if old_day != None:
                        day.import_div_games(div_idx, old_day)
                        self.add_day_to_division_history(day, div_idx=div_idx)
                        continue
            except:
                pass
            day.schedule_div_players_without_refs(fac, div_idx, div)
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
            ('min hour and no-sit', [-180, 0, -5, -600, bad, bad, bad]),
            ('min hour and small-sit', [-200, 0, 0, -200, bad, bad, bad]),
        ]
        game_length = 20
        time_cypher = [game_length * idx for idx in range(10)]
        team_wise_penality = [-5000,0,0,0,   -100,bad,bad,bad,   bad,bad]
        count = sum(sitting_counts)
        sum_prod = sum(time * count for time, count in enumerate(sitting_counts))
        average = sum_prod / count * 4
        results = {}
        # calc team-wise sitting function
        team_penalty_total = 0
        for team_sit in team_sits:
            team_sit_total = sum((a * b for a, b in zip(team_sit, time_cypher)))
            team_penalty_total += team_wise_penality[int(team_sit_total / 20)]
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
                    if (self.divisions[game.div].teams[game.team2].times_team_played[game.team1] < 0 or
                       self.divisions[game.div].teams[game.team2].times_team_played[game.team1] < 0):
                        raise(Exception('there is something wrong going on'))
                    if game.ref != init_value:
                        self.divisions[game.div].teams[game.ref].refs += sign
                    self.divisions[game.div].teams[game.team1].games_per_day[day.num] += sign
                    self.divisions[game.div].teams[game.team2].games_per_day[day.num] += sign

    def subtract_day_from_division_history(self, day, div_idx=None):
        self.add_day_to_division_history(day, div_idx=div_idx, sign=-1)

    def skillz_clinic_count(self):
        # The number of skillz clinics is the number of open game slots
        total_slots = self.daycount * self.courts * self.times
        total_games = self.games_per_team * sum(self.team_counts) / 2  # 2 teams per game
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

    def clear_all_reffing_for_division(self, division_idx):
        for day in self.days:
            court_list = day.courts
            for court in court_list:
                for game in court:
                    if game.div == division_idx:
                        game.ref = init_value
        for team in self.divisions[division_idx].teams:
            team.refs = 0

    def try_transfer_reffing(self, div, div_idx):
        """
        The purpose of this method is to transfer ref responsibilities from a team with too
        many to a team w too few. This routine ends once either list is empty
        :param from_list: List of teams w the most reffings
        :param to_list: List of teams w the least
        :return: the division structure with the revised reffing history
        """
        reffings = [team.refs for team in div.teams]
        from_list = [idx for idx, ref_count in enumerate(reffings) if ref_count == max(reffings)]
        to_list = [idx for idx, ref_count in enumerate(reffings) if ref_count == min(reffings)]
        for day in self.days:
            from_list, to_list, div = day.try_transfer_reffing(from_list, to_list, div, div_idx)
            if not (from_list and to_list):
                break
        return div

    def ref_transfering_is_neeeded(self, div):
        reffings = [team.refs for team in div.teams]
        if max(reffings) - min(reffings) > 1:
            return True
        else:
            return False

    def add_reffing(self, debug=False):
        max_number_of_attempts = 100  # not expected to happen
        for div_idx, div in enumerate(self.divisions):
            print('Adding Reffing for division {}'.format(div_idx))
            for idx in range(max_number_of_attempts):
                self.clear_all_reffing_for_division(div_idx)
                try:
                    for day_idx in range(len(self.days)):
                        self.days[day_idx].add_reffing(div_idx, self.divisions[div_idx])
                    if self.ref_transfering_is_neeeded(div):
                        div = self.try_transfer_reffing(div, div_idx)
                    if debug:
                        print(self.solution_debug_data(idx))
                    current_fitness = self.fitness()
                    if current_fitness == 0:
                        break

                except WeirdReffingCollision:   #   WeirdReffingCollision    ValueError     qwer
                    print('i like waffles')
                    continue
            else:
                print('Initial traceback was asdf:\n{}'.format(traceback.format_exc()))
                print(self.solution_debug_data(1))
                print(self.get_audit_text())
                # qwer todo raise(Exception('Could not find ref solution for div_idx {}'.format(div_idx)))

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

    def solution_debug_data(self, mut_idx=0, div_idx=None):
        fitness = self.fitness()
        def get_sorted_breakdown(div_idx):
            error_dict = self.fitness_error_breakdown(div_idx=div_idx)
            error_item_list = sorted(list(error_dict.items()))
            error_item_list = list(filter(lambda x: x[1], error_item_list))
            return str(error_item_list)
        if div_idx == None:
            breakdown = '\n'.join(['division {} breakdown: {}'.format(div_idx, [get_sorted_breakdown(div_idx) for div_idx in range(5)])])
        else:
            breakdown = 'division {} breakdown: {}'.format(div_idx, get_sorted_breakdown(div_idx))
        return "value = {} while on mutation step   {}  : division fitness = {}    {}".format(
              fitness, mut_idx, self.fitness_div_list(), breakdown)

    def try_move_game_from_court(self, day_idx, target_court_idx, time):
        div_idx = self.days[day_idx].courts[target_court_idx][time].div
        for alternate_court_idx in range(len(self.days[day_idx].courts)):
            alternate_game = self.days[day_idx].courts[alternate_court_idx][time]
            if alternate_court_idx != target_court_idx and div_idx == alternate_game.div:
                (self.days[day_idx].courts[target_court_idx][time],
                 self.days[day_idx].courts[alternate_court_idx][time]) = \
                    (self.days[day_idx].courts[alternate_court_idx][time],
                    self.days[day_idx].courts[target_court_idx][time])
                break

    def try_shift_team_out_of_court(self, div_teams, court_idx_to_avoid):
        for div_idx, team_idx in div_teams:
            for day_idx, day in enumerate(self.days):
                for time, game in enumerate(day.courts[court_idx_to_avoid]):
                    if game.div == div_idx and team_idx in [game.team1, game.team2]:
                        self.try_move_game_from_court(day_idx, court_idx_to_avoid, time)

    def switch_specific_games(self, game_data1, game_data2):
        game1 = copy.deepcopy(self.days[game_data1['day']].courts[game_data1['court']][game_data1['time']])
        game2 = copy.deepcopy(self.days[game_data2['day']].courts[game_data2['court']][game_data2['time']])
        if game1.div != game2.div:
            raise(Exception('Tried to switch games at {} and {} but they are not the same division:\n'.format(game_data1, game_data2) +
                            'game1 = {}, game2 = {}'.format(game1, game2)))
        self.days[game_data1['day']].courts[game_data1['court']][game_data1['time']] = game2
        self.days[game_data2['day']].courts[game_data2['court']][game_data2['time']] = game1

    def switch_specific_refs(self, game_data1, game_data2):
        game1 = copy.deepcopy(self.days[game_data1['day']].courts[game_data1['court']][game_data1['time']])
        game2 = copy.deepcopy(self.days[game_data2['day']].courts[game_data2['court']][game_data2['time']])
        if game1.div != game2.div:
            raise(Exception('Tried to switch games at {} and {} but they are not the same division:\n'.format(game_data1, game_data2) +
                            'game1 = {}, game2 = {}'.format(game1, game2)))
        self.days[game_data1['day']].courts[game_data1['court']][game_data1['time']].ref = game2.ref
        self.days[game_data2['day']].courts[game_data2['court']][game_data2['time']].ref = game1.ref

    def switch_days(self, day1, day2):
        (self.days[day1], self.days[day2]) = (self.days[day2], self.days[day1])
        self.days[day1].num = day1
        self.days[day2].num = day2
        self.days[day1].facilities.day_idx = day1
        self.days[day2].facilities.day_idx = day2

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
    with open(sch_py_obj, 'rb') as sch_file:
        schedule = pickle.load(sch_file)
        return schedule

if __name__ == '__main__':
    sch = load_reg_schedule()
    json_sch = sch.create_json_schedule()
    print(json_sch)
    sch2 = gen_schedule_from_json(json_sch)