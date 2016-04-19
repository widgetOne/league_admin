#!/usr/local/bin/python
__author__ = 'brcoulter'

'''Defining the abstract optimizer class that will become the building
   block for the various schedule components'''

from abc import ABCMeta
from abc import abstractmethod
class Solver(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        self._state = None

    def mutation_methods(self):
        '''This routine finds all mutate_* methods returns their names'''
        import re
        mutation_re = re.compile('^mutate_')
        mutation_methods = [param for param in dir(self)
                            if mutation_re.match(param)]
        return mutation_methods

    def mutate(self):
        '''This routine finds all other mutate_* methods and calls one'''
        from random import choice
        methods = self.mutation_methods()
        if not methods:
            raise(Exception('A Solver sub-class was created that does not' +
                            'contain any mutate_ methods'))
        # todo: make this more clever. For now, random
        current_method = choice(methods)
        getattr(self, current_method)() # calling the chosen method

    @abstractmethod
    def fitness(self, state=None):
        '''This function will return a non-positive value describing how
        far from being ACCEPTABLE the current schedule is. Only a object
        with a value of 0 is acceptable in a final schedule'''
        pass

    def optimality(self, state=None):
        '''This function returns a non-negative value describing how optimized
        the current solution is. Any value is acceptable, but a higher value
        is better'''
        return 0

    def enhance(self):
        from copy import deepcopy
        old_state = deepcopy(self._state)
        self.mutate()
        if self.fitness < self.fitness(old_state):
            self._state = old_state


if __name__ == '__main__':
    pass
