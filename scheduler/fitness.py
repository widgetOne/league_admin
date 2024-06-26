#!/usr/local/bin/python
import copy
from pprint import pprint
__author__ = 'brcoulter'

def add_lists(list1, list2, sign=1):
    return [x + sign * y for x, y in zip(list1, list2)]

def add_list_of_lists(list_of_lists1, list_of_lists2, sign):
    output = copy.deepcopy(list_of_lists1)
    for idx1, listlist2 in enumerate(list_of_lists2):
        for idx2, list2 in enumerate(listlist2):
            if sign == 1:
                output[idx1][idx2] += list2
            else:
                for item in list2:
                    output[idx1][idx2].remove(item)
    return output

def even_distribution_fitness(array):
    from math import pow
    length = len(array)
    total = sum(array)
    min_flat_value = total // length
    max_flat_value = min_flat_value + 1
    max_value_count = total % length
    min_value_count = length - max_value_count
    min_defect = int(min_value_count * pow(min_flat_value, 2) +
                     max_value_count * pow(max_flat_value, 2))
    fitness = min_defect
    fitness -= sum((int(pow(value, 2)) for value in array))
    return fitness

default_vs_self = 1000  # weight to prevent but no precludes teams playing self
conflict_weight = 100

def fitness_of_0_or_1_is_good(value):
    if value in (0,1):
        return 0
    else:
        return -1

def division_specific_bye_fitness(bye_array):
    """
    the 6 team divisions cannot accept any double headers and still have enough refs, but the
    other divisions can
    :return: fitness of this division in terms of byes
    """
    if len(bye_array) == 6:
        bye_fitness = sum((fitness_of_0_or_1_is_good(bye) for bye in bye_array))
    else:
        bye_fitness = even_distribution_fitness(bye_array)
    return bye_fitness


class ScheduleDivFitness(object):
    def __init__(self, count, day_num, games=[], bye_requirement=0, open_play_times=[]):
        # TODO: This needs refactored into an array of fitness objects, that all have a consistent interface
        # for target data collection, target data summation, fitness. Then these objects would be assigned to
        # this class, like "self.fitness_methods" is now.
        from copy import deepcopy
        from model import init_value
        blank_1d = [0] * count
        blank_vs = []
        for idx in range(count):
            line = deepcopy(blank_1d)
            line[idx] = default_vs_self  # weight to prevent teams playing self
            blank_vs.append(line)
        self._plays = deepcopy(blank_1d)
        self._refs = deepcopy(blank_1d)
        self._vs = deepcopy(blank_vs)
        self._vs_by_day = [[[] for _ in range(count)] for _ in range(count)]
        self._play_over_time = [{} for _ in range(count)]
        self.bye_requirement = bye_requirement
        self._open_play = deepcopy(blank_1d)
        self._play_times = [{} for _ in range(count)]
        self._usage_times = [{} for _ in range(count)]
        usage_w_time = {}
        for game in games:  # There may be no games
            self.add_game(game, day_num)
            if game.time not in usage_w_time:
                usage_w_time[game.time] = deepcopy(blank_1d)
            usage_w_time[game.time][game.team1] += 1
            self._play_times[game.team1][game.time] = self._play_times[game.team1].get(game.time, 0) + 1
            self._usage_times[game.team1][game.time] = self._usage_times[game.team1].get(game.time, 0) + 1
            usage_w_time[game.time][game.team2] += 1
            self._play_times[game.team2][game.time] = self._play_times[game.team2].get(game.time, 0) + 1
            self._usage_times[game.team2][game.time] = self._usage_times[game.team2].get(game.time, 0) + 1
            if game.ref is not None and game.ref != init_value:
                usage_w_time[game.time][game.ref] += 1
                self._usage_times[game.ref][game.time] = self._usage_times[game.ref].get(game.time, 0) + 1
        usage = sum(usage_w_time.values(), [])
        THREE_HOUR_DAY_PENALTY = -1
        def get_max_time_gap(time_dict):
            is_3h_day = time_dict and max(time_dict.keys()) - min(time_dict.keys()) > 1
            return THREE_HOUR_DAY_PENALTY if is_3h_day else 0
        self._play_gaps = list(map(get_max_time_gap, self._play_times))
        self._three_hours_days = list(map(get_max_time_gap, self._usage_times))
        self._multi_use_in_time = sum((val - 1 for val in usage if val > 1))
        def bye(plays):
            if plays == 0:
                return 1
            elif plays > 2:
                #return 10  # to suppress triple headers
                return 10  # to suppress triple headers
            else:
                return 0
        self._byes = [bye(play_num) for play_num in self._plays]
        self.successive_byes = sum((a and b for a,b in zip(self._byes[:-1], self._byes[1:])))
        def double_ref(ref):
            if ref > 1:
                return 1
            else:
                return 0
        self._double_refs = sum((double_ref(refs) for refs in self._refs))
        #if games and games[0].div != 1:
        #    self._open_play = self.get_team_open_play(games, open_play_times, self._open_play)
        self.fitness_methods = {
            'plays': lambda x: even_distribution_fitness(x._plays),
            'refs': lambda x: even_distribution_fitness(x._refs),
            'vs_evenness': lambda x: x.vs_fitness(),
            'play_gaps': lambda x: sum(p * 19 for p in x._play_gaps),
            'no_vs_repeats': lambda x: x.vs_repeat_fitness(),
            'conflict': lambda x: -conflict_weight * x._multi_use_in_time,
            'byes_total': lambda x: (x.bye_requirement - sum(x._byes)) * 3,
            'bye_evenness': lambda x: even_distribution_fitness(x._byes),
            # 'open_play_evenness': lambda x: even_distribution_fitness(x._open_play),
            'successive_byes': lambda x: x.successive_byes_fitness(),
            'double_refs': lambda x: -conflict_weight * x._double_refs,
        }

        """
        Additional criteria discussed but not implemented:
           no reffing on days with double headers
           All teams must play the first week
        """

    def __add__(self, other, sign=1):
        self._plays = add_lists(self._plays, other._plays, sign)
        self._refs = add_lists(self._refs, other._refs, sign)
        for idx, (self_list, other_list) in enumerate(zip(self._vs, other._vs)):
            self._vs[idx] = add_lists(self_list, other_list, sign)
            # we don't want these default_vs_self values accumulating
            self._vs[idx][idx] -= default_vs_self
        self._multi_use_in_time += other._multi_use_in_time
        self._byes = add_lists(self._byes, other._byes, sign)
        self._open_play = add_lists(self._open_play, other._open_play, sign)
        self._double_refs += other._double_refs * sign
        self._vs_by_day = add_list_of_lists(self._vs_by_day, other._vs_by_day, sign)
        self.successive_byes += other.successive_byes * sign
        self._play_over_time = [add_dict(a, b) for a,b in zip(self._play_over_time, other._play_over_time)]
        self._three_hours_days = add_lists(self._three_hours_days, other._three_hours_days, sign)
        self._play_gaps = add_lists(self._play_gaps, other._play_gaps, sign)
        return self

    def __radd__(self, other):
        # I only expect this to happen when generating a summation
        if other != 0:
            raise (TypeError('trying to add a ScheduleDivTotal to something ' +
                             'of type {}, '.format(type(other)) +
                             'with value {} which '.format(other) +
                             'ScheduleDivTotal does not know how to handle'))
        else:
            return self

    def __sub__(self, other):
        return self.__add__(other, sign=-1)

    def vs_fitness(self):
        # note, in vs, default_vs_self is used as a default weight
        fitness = int(pow(default_vs_self, 2)) * len(self._vs)
        fitness -= sum((int(pow(self._vs[idx][idx], 2))
                        for idx in range(len(self._vs))))
        vs_minus_default = []
        for idx, row in enumerate(self._vs):
            vs_minus_default += row[:idx] + row[idx + 1:]
            if any((value < 0 for value in row)):
                raise(Exception('There is a negative vs value'))
        fitness += even_distribution_fitness(vs_minus_default)
        return fitness

    def vs_repeat_fitness(self):
        """
        This routine returns fitness based on name teams playing the same match twice in a row
        :return: fitness integer
        """
        fitness = 0
        for row in self._vs_by_day:
            for match in row:
                if len(match) < 2:
                    continue  # not enough repeats of same match to be an issue
                else:
                    for idx in range(len(match) - 1):
                        if abs(match[idx] - match[idx+1]) < 2:
                            fitness -= 1
        return fitness

    def value(self):
        fitness = 0
        for func in self.fitness_methods.values():
            fitness += func(self)
        if sum(self._plays) == 0:  # Is unlikely to ever happen
            fitness -= 1001  # something unique to flag the odd behavior
        return fitness

    def add_game(self, game, day_num, sign=1):
        from model import init_value
        fake_values = [init_value, -1]
        if game.team1 not in fake_values and game.team2 not in fake_values:
            self._plays[game.team1] += sign
            self._plays[game.team2] += sign
            if isinstance(game.ref, tuple):
                #self._refs[game.ref] += sign
                raise(Exception('using tuple, out of division reffing without finishing fitness refactor. save div_idx?'))
            elif game.ref is not None and game.ref != init_value:
                self._refs[game.ref] += sign
            self._vs[game.team1][game.team2] += sign
            self._vs[game.team2][game.team1] += sign
            self._play_over_time[game.team1][day_num] = self._play_over_time[game.team1].get(day_num, 0) + sign
            self._play_over_time[game.team2][day_num] = self._play_over_time[game.team2].get(day_num, 0) + sign
            if sign == 1:
                self._vs_by_day[game.team1][game.team2].append(day_num)
                self._vs_by_day[game.team2][game.team1].append(day_num)
            else:
                self._vs_by_day[game.team1][game.team2].remove(day_num)
                self._vs_by_day[game.team2][game.team1].remove(day_num)


    def error_breakdown(self):
        return {key: func(self) for key, func in self.fitness_methods.items()}

    def successive_byes_fitness(self):
        fitness = 0
        for team_play_w_time_dict in self._play_over_time:
            team_play_w_time_list = dict_to_list(team_play_w_time_dict)
            for day_idx in range(len(team_play_w_time_list)-1):
                if team_play_w_time_list[day_idx] == 0 and team_play_w_time_list[day_idx+1] == 0:
                    fitness -= 1
        return fitness

    def get_team_open_play(self, games, open_play_times, open_play_opertunities):
        ######2018-09-05#### raise(Exception('This code change is needed but has not been evaluated yet'))
        if not open_play_times:
            return
        team_busy_data = [{} for _ in range(len(open_play_opertunities))]
        for game in games:
            for team in [game.team1, game.team2, game.ref]:
                if game.ref > -1:
                    team_busy_data[team].add(game.time)
        for team_idx, team_obligations in enumerate(team_busy_data):
            for open_time in open_play_times:
                if (open_time not in team_obligations and
                        (open_time + 1 in team_obligations or
                        open_time - 1 in team_obligations)):
                    open_play_opertunities[team_idx] = 1
        return open_play_opertunities


def dict_to_list(dictionary):
    max_key = max(dictionary.keys())
    def try_get_number_from_dict(loc_dict, num):
        if num in loc_dict:
            return num
        else:
            return num
    return [try_get_number_from_dict(dictionary, num) for num in range(max_key)]

def add_dict(a, b):
    import copy
    result = copy.deepcopy(a)
    for key, value in b.items():
        result[key] = result.get(key, 0) + value
    return result

class ScheduleFitness(object):
    def __init__(self, day_num, bye_requirements, facilities=None, games=[], div_idx=None):
        self._divs = []  # first, we create the blank slates for the sums
        if div_idx is not None and div_idx >= len(facilities.team_counts):
            raise Exception(f'weird event where div_idx = {div_idx}')
        if div_idx is None:
            div_counts = list(enumerate(facilities.team_counts))
        else:
            div_counts = [(div_idx, facilities.team_counts[div_idx])]
        open_play_times = facilities.get_open_play_times()
        for div_idx, count in div_counts:
            div_games = [game for game in games if game.div == div_idx]
            div = ScheduleDivFitness(count, day_num, div_games, bye_requirements[div_idx],
                                     open_play_times=open_play_times)
            self._divs.append(div)

    def __add__(self, other, sign=1):
        for div, other_div in zip(self._divs, other._divs):
            div.__add__(other_div, sign)
        return self

    def __radd__(self, other):
        # I only expect this to happen when generating a summation
        if other != 0:
            raise(TypeError('trying to add a ScheduleTotal to something ' +
                            'of type {}, '.format(type(other)) +
                            'with value {} '.format(other) +
                            'which ScheduleTotal does not know how to handle'))
        else:
            return self

    def __sub__(self, other):
        return self.__add__(other, sign=-1)

    def get_three_hour_days(self):
        return -sum(sum(div._three_hours_days) for div in self._divs)

    def value(self):
        fitness = sum((div.value() for div in self._divs))
        return fitness

    def div_value(self, div_idx):
        return self._divs[div_idx].value()

    def error_breakdown(self):
        result = {}
        for div in self._divs:
            result = add_dict(result, div.error_breakdown())
        return result

    def open_play_lists(self):
        return [div._open_play for div in self._divs]

    def get_double_ref_lists(self):
        return [div._double_refs for div in self._divs]


if __name__ == '__main__':
    pass