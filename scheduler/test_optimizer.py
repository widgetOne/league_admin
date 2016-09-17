from unittest import TestCase
import optimizer
__author__ = 'coulter'


class TestOptimizer(TestCase):

    def test_round_robin(self):
        from optimizer import make_round_robin_game
        team_counts = [6, 10, 11, 10, 6]
        sch_template_path = 'test/Fall-2016-scrap-round_robin_csv_e.csv'
        canned_path = 'test/scratch/'
        total_schedules = 2
        canned_path = 'test_' + optimizer.get_default_potential_sch_loc()
        summary, schedules = make_round_robin_game(team_counts, sch_template_path, total_schedules,
                                                   canned_path=canned_path)
        self.assertEqual(len(schedules), total_schedules)

    def test_regular_season(self):
        import facility
        from optimizer import make_schedule, save_schedules, get_default_potential_sch_loc
        team_counts = [6, 10, 11, 10, 6]
        canned_path = get_default_potential_sch_loc('2016-09-10')
        sch_template_path = 'test/reg_season/draft_fac_a.csv'
        sch_tries = 4
        fac = facility.sch_template_path_to_fac(sch_template_path, team_counts)
        seed = 1
        print('\nMaking schedule %s.' % seed)
        try:
            sch = make_schedule(team_counts, fac,
                                sch_tries=sch_tries, seed=seed, debug=True)
        except optimizer.FailedToConverge:
            assert (True)
        except:
            assert (False)
        #self.assertRaises(optimizer.FailedToConverge, make_schedule, [],
        #                  {'team_counts': team_counts, 'league': fac,
        #                      'sch_tries': sch_tries, 'seed': seed, 'debug': True})

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

if __name__ == '__main__':
    unittest.main()