from unittest import TestCase
from maker import make_schedule

__author__ = 'coulter'

class TestPassword(TestCase):

    def test_high_level(self):
        fitness = make_schedule([6,12,12,6])
        self.assertEqual(fitness, -36)

    #  self.assertRaises(ValueError, testPassword.getPassword)
