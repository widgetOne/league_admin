from unittest import TestCase
from maker import make_schedule

__author__ = 'coulter'

class TestPassword(TestCase):

    def test_high_level(self):
        expected_fitness = -24
        fitness = make_schedule([6,12,12,6])
        self.assertEqual(fitness, expected_fitness)
        self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
        self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
        self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
        self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)
        self.assertEqual(make_schedule([6,12,12,6]), expected_fitness)

    #  self.assertRaises(ValueError, testPassword.getPassword)
