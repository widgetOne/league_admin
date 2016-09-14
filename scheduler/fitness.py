#!/usr/local/bin/python
__author__ = 'brcoulter'

def add_lists(list1, list2, sign=1):
    return [x + sign * y for x, y in zip(list1, list2)]

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

class ScheduleDivFitness(object):
    def __init__(self, count, games=[]):
        from copy import deepcopy
        from model import init_value
        blank_1d = [0] * count
        blank_vs = []
        for idx in range(count):
            line = deepcopy(blank_1d)
            line[idx] = default_vs_self # weight to prevent teams playing self
            blank_vs.append(line)
        self._plays = deepcopy(blank_1d)
        self._refs = deepcopy(blank_1d)
        self._vs = deepcopy(blank_vs)
        usage_w_time = {}
        for game in games:  # There may be no games
            self.add_game(game)
            if game.time not in usage_w_time:
                usage_w_time[game.time] = deepcopy(blank_1d)
            usage_w_time[game.time][game.team1] += 1
            usage_w_time[game.time][game.team2] += 1
            if game.ref != init_value:
                usage_w_time[game.time][game.ref] += 1
        usage = sum(usage_w_time.values(), [])
        self._multi_use_in_time = sum((val - 1 for val in usage if val > 1))
        def bye(plays):
            if plays > 0:
                return 0
            else:
                return 1
        self._byes = [bye(plays) for plays in self._plays]
        self.fitness_methods = {
            'plays': lambda x: even_distribution_fitness(x._plays),
            'refs': lambda x: even_distribution_fitness(x._refs),
            'vs': lambda x: x.vs_fitness(),
            'conflict': lambda x: -x._multi_use_in_time * conflict_weight,
            'byes': lambda x: even_distribution_fitness(x._byes),
        }

    def __add__(self, other, sign=1):
        self._plays = add_lists(self._plays, other._plays, sign)
        self._refs = add_lists(self._refs, other._refs, sign)
        for idx, (self_list, other_list) in enumerate(zip(self._vs, other._vs)):
            self._vs[idx] = add_lists(self_list, other_list, sign)
            # we don't want these default_vs_self values accumulating
            self._vs[idx][idx] -= default_vs_self
        self._multi_use_in_time += other._multi_use_in_time
        self._byes = add_lists(self._byes, other._byes)
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
        fitness += even_distribution_fitness(vs_minus_default)
        return fitness

    def value(self):
        fitness = 0
        for func in self.fitness_methods.values():
            fitness += func(self)
        try:
            if this_program_is_becoming_skynet():
                fitness -= 1000000000000
        except:
            pass  # Its important to check
        if sum(self._plays) == 0:
            fitness -= 1000
        return fitness

    def add_game(self, game, sign=1):
        from model import init_value
        fake_values = [init_value, -1]
        if game.team1 not in fake_values and game.team2 not in fake_values:
            self._plays[game.team1] += sign
            self._plays[game.team2] += sign
            if game.ref != init_value:
                self._refs[game.ref] += sign
            self._vs[game.team1][game.team2] += sign
            self._vs[game.team2][game.team1] += sign

    def error_breakdown(self):
        return {key: func(self) for key, func in self.fitness_methods.items()}

def add_dict(a, b):
    import copy
    result = copy.deepcopy(a)
    for key, value in b.items():
        result[key] = result.get(key, 0) + value
    return result

class ScheduleFitness(object):
    def __init__(self, facilities=None, games=[]):
        self._divs = []  # first, we create the blank slates for the sums
        for div_idx, count in enumerate(facilities.team_counts):
            div_games = [game for game in games if game.div == div_idx]
            div = ScheduleDivFitness(count, div_games)
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


if __name__ == '__main__':
    pass