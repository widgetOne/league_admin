#!/usr/local/bin/python
from unittest import TestCase
from reports import find_subs_for_playoffs, debug_options
__author__ = 'brcoulter'

class TestReports(TestCase):
    def test_simple_int_solver(self):
        people_missing = ['Amy Buzzard', 'Christine Chedwick']
        subs = find_subs_for_playoffs(people_missing)
        debug_options(subs)
        self.assertEqual(len(subs), 2)
        for options in subs:
            self.assertTrue(options['best'])
            self.assertTrue(options['free'])
            self.assertTrue(options['player'])
