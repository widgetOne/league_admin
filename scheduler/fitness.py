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
    fitness = -min_defect
    fitness += sum((int(pow(value, 2)) for value in array))
    return fitness

class ScheduleDivFitness(object):
    def __init__(self, count, games=[]):
        from copy import deepcopy
        blank_1d = [0] * count
        blank_vs = []
        for idx in range(count):
            line = deepcopy(blank_1d)
            line[idx] = 1000 # weight to prevent teams playing self
            blank_vs.append(line)
        self._plays = deepcopy(blank_1d)
        self._refs = deepcopy(blank_1d)
        self._vs = deepcopy(blank_vs)
        for game in games:  # There may be no games
            pass

    def __add__(self, other, sign=1):
        self._plays = add_lists(self._plays, other._plays, sign)
        self._refs = add_lists(self._refs, other._refs, sign)
        for idx, (self_list, other_list) in enumerate(zip(self._vs, other._vs)):
            self._vs[idx] = add_lists(self_list, other_list, sign)
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

    def fitness(self):
        fitness = 0
        fitness += even_distribution_fitness(self._plays)
        fitness += even_distribution_fitness(self._refs)
        # self._vs = deepcopy(blank_2d)
        return fitness

class ScheduleFitness(object):
    def __init__(self, facilities=None, games=[]):
        self._divs = []  # first, we create the blank slates for the sums
        for count in facilities.team_counts:
            div = ScheduleDivFitness(count)
            self._divs.append(div)
        for game in games:  # There may be no games
            pass

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

    def fitness(self):
        fitness = sum((div.fitness() for div in self._divs))
        return fitness

if __name__ == '__main__':
    pass