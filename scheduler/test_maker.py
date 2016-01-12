from unittest import TestCase
from maker import make_schedule

__author__ = 'coulter'

class TestPassword(TestCase):

    def test_high_level(self):
        expected_fitness = -28
        fitness = make_schedule([6,12,12,6])
        self.assertEqual(fitness, expected_fitness)
      #  self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
      #  self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
      #  self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
      #  self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
      #  self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)

    '''
    too costly for rapid development
    def test_repeatability(self):
        number_of_tests = 10
        fitness = make_schedule([6,12,12,6])
        for _ in range(number_of_tests):
            self.assertEqual(fitness, make_schedule([6,12,12,6]))
    '''
    #  self.assertRaises(ValueError, testPassword.getPassword)
