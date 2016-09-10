from unittest import TestCase
from maker import make_schedule
__author__ = 'coulter'


class TestMaker(TestCase):

    '''
    def test_high_level(self):
        expected_fitness = 0
        value = make_schedule([6,14,14,6])
        self.assertEqual(value, expected_fitness)
    #   value = make_schedule([6,12,12,6])
    #    self.assertEqual(value, expected_fitness)
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
        value = make_schedule([6,12,12,6])
        for _ in range(number_of_tests):
            self.assertEqual(value, make_schedule([6,12,12,6]))
    '''
    '''
    # todo: I think the round robin did not survive the
    $ regular season refactoring
        def test_round_robin_integration(self):
            from maker import make_round_robin
            sch = make_round_robin([6,13,14,7], sch_tries=5,
                                   total_sch=2, seed=5)
            self.assertEqual(sch.seed, 1)
            self.assertEqual(sch.sitting_fitness()[0], -62.0)
            self.assertEqual(sch.sitting_fitness()[1], 3)
    '''

    #   def make_round_robin(team_counts, sch_tries=500, seed=1,
    #                        save_progress=False,
    #                        total_sch=2):
    '''
    def test_regular_season_scvl_integration(self):
        from maker import make_regular_season
        sch = make_regular_season([6, 13, 14, 7], ndays=9,
                                  sch_tries=5, seed=5)
    #    self.assertEqual(sch.seed, 1)
    #    self.assertEqual(sch.sitting_fitness()[0], -62.0)
    #    self.assertEqual(sch.sitting_fitness()[1], 3)
        self.assertEqual(1, 1)
    '''

    #make_round_robin_from_csv_fall_2016()
