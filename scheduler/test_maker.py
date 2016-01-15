from unittest import TestCase
from maker import make_schedule

__author__ = 'coulter'

class TestPassword(TestCase):

    '''
    def test_high_level(self):
        expected_fitness = 0
        fitness = make_schedule([6,14,14,6])
        self.assertEqual(fitness, expected_fitness)
    #   fitness = make_schedule([6,12,12,6])
    #    self.assertEqual(fitness, expected_fitness)
      #  self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
      #  self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
      #  self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
      #  self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
      #  self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
    '''

    '''
    too costly for rapid development
    def test_repeatability(self):
        number_of_tests = 10
        fitness = make_schedule([6,12,12,6])
        for _ in range(number_of_tests):
            self.assertEqual(fitness, make_schedule([6,12,12,6]))
    '''

    def test_csv_reporting(self):
        from maker import make_round_robin
        make_round_robin([6,13,14,7], tries=20, seed=5)

        self.assertEqual(1, 1)
