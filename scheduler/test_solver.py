#!/usr/local/bin/python
from unittest import TestCase
from solver import Solver
__author__ = 'brcoulter'


class TestSolver(TestCase):
    def test_simple_int_solver(self):
        import random
        random.seed(1)

        class IntSolver(Solver):
            def __init__(self, state=-10):
                self._state = state

            def fitness(self, state=None):
                if state is None:
                    state = self._state
                return state

            def mutate_half(self):
                self._state /= 2

            def mutate_subtract(self):
                self._state = min(self._state + 1, 0)

        initial_value = -14
        int_solver = IntSolver(initial_value)
        self.assertEqual(int_solver.fitness(), initial_value)

        print(int_solver._state)

        int_solver.mutate()
        self.assertLess(initial_value, int_solver.fitness())

        while int_solver._state != 0:
            int_solver.mutate()
            print(int_solver._state)
        self.assertAlmostEquals(int_solver.fitness(), 0, 10**-11)
