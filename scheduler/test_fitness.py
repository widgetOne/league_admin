from unittest import TestCase
import fitness
__author__ = 'coulter'

def check_total_sizes(assert_true, div_totals, count):
    assert_true(len(div_totals._plays) == count)
    assert_true(len(div_totals._refs) == count)
    assert_true(len(div_totals._vs) == count)
    assert_true(len(div_totals._vs[0]) == count)
    assert_true(len(div_totals._vs[count - 1]) == count)

def basic_facilities(tries=1):
    from facility import SCVL_Facility_Day
    from facility import League
    import random
    random.seed(1)
    team_counts = [6, 13, 14, 7]
    ndays = 1
    facilities = League(ndivs=4, ndays=ndays, ncourts=5, ntimes=4,
                        team_counts=team_counts, day_type=SCVL_Facility_Day)
    return facilities

class TestFitness(TestCase):
    def test_blank_schedule_total(self):
        facilities = basic_facilities()
        blank_totals = fitness.ScheduleFitness(facilities)
        self.assertTrue(len(blank_totals._divs) == len(facilities.team_counts))
        for div_idx, count in enumerate(facilities.team_counts):
            div = blank_totals._divs[div_idx]
            self.assertTrue(sum(div._plays) == 0)
            check_total_sizes(self.assertTrue, div, count)
        sample_div_count = 45
        blank_div = fitness.ScheduleDivFitness(sample_div_count)
        self.assertTrue(sum(blank_div._plays) == 0)
        check_total_sizes(self.assertTrue, blank_div, sample_div_count)

    def test_fitness_math(self):
        facilities = basic_facilities()
        blank_totals1 = fitness.ScheduleFitness(facilities)
        blank_totals2 = fitness.ScheduleFitness(facilities)
        blank_totals1._divs[3]._plays[2] = 1
        blank_totals1._divs[1]._plays[3] = 1
        blank_totals2._divs[1]._plays[3] = 2
        blank_totals1._divs[2]._vs[4][6] = 1
        blank_totals2._divs[2]._vs[4][6] = 2
        blank_totals1._divs[0]._refs[1] = 1
        blank_totals2._divs[0]._refs[1] = 2
        local_sum = sum([blank_totals1, blank_totals2])
        local_sum += local_sum
        local_sum -= blank_totals2
        default_total = 1 + 2 + 3 - 2
        self.assertEqual(local_sum._divs[3]._plays[2], 1 + 1)
        self.assertEqual(local_sum._divs[1]._plays[3], default_total)
        self.assertEqual(local_sum._divs[2]._vs[4][6], default_total)
        self.assertEqual(local_sum._divs[0]._refs[1], default_total)
        # checking the forbidden operations
        _ = 0 + blank_totals1
        def this_plus_blank_totals(this):
            this + blank_totals1
        self.assertRaises(TypeError, this_plus_blank_totals, 2)
        self.assertRaises(TypeError, this_plus_blank_totals, 'asdf')

    def test_fitness_calc(self):
        facilities = basic_facilities()
        blank_totals = fitness.ScheduleFitness(facilities)
        self.assertEqual(blank_totals.value(), 0)
        blank_totals._divs[1]._plays[3] = 1
        self.assertEqual(blank_totals.value(), 0)
        size = len(blank_totals._divs[1]._plays)
        blank_totals._divs[1]._plays = [1] * size
        self.assertEqual(blank_totals.value(), 0)
        blank_totals._divs[1]._plays = [4] * size
        self.assertEqual(blank_totals.value(), 0)
        blank_totals._divs[1]._plays[3] = 2
        self.assertEqual(blank_totals.value(), -2)
        blank_totals._divs[1]._plays = [1] * size
        blank_totals._divs[1]._refs[3] = 2
        self.assertEqual(blank_totals.value(), -2)
        blank_totals._divs[1]._plays = [1] * size
        blank_totals._divs[1]._refs[3] = 2
        self.assertEqual(blank_totals.value(), -2)
        blank_totals._divs[1]._refs[3] = 0
        blank_totals._divs[1]._vs[2][3] = 1
        self.assertEqual(blank_totals.value(), 0)
        blank_totals._divs[1]._vs[2][3] = 2
        self.assertEqual(blank_totals.value(), -2)
        blank_totals._divs[1]._vs[2][3] = 0
        blank_totals._divs[1]._vs[3][3] += 1
        one_vs_self_fitness = -1 - 2 * fitness.default_vs_self
        self.assertEqual(blank_totals.value(), one_vs_self_fitness)
        blank_totals._divs[1]._vs[3][3] += 1
        one_vs_self_fitness = -4 - 4 * fitness.default_vs_self
        self.assertEqual(blank_totals.value(), one_vs_self_fitness)
        blank_totals._divs[1]._vs[3][3] -= 2

    def test_game_processing(self):
        from maker import make_schedule
        from model import Game
        from copy import deepcopy
        from fitness import ScheduleFitness as Fit
        facilities = basic_facilities()
        sch = make_schedule(facilities.team_counts, facilities, sch_tries=1)
        sch_days_fitness = Fit(facilities)
        reference_game_dict = {'team1': 1, 'team2': 2, 'ref': 3,
                    'div': 1, 'time': 1, 'court': 1}
        reference_game = Game(**reference_game_dict)
        other_game_dict = {'team1': 4, 'team2': 5, 'ref': 6,
                      'div': 1, 'time': 1, 'court': 2}
        other_game = Game(**other_game_dict)
        ref_conflict_dict = deepcopy(other_game_dict)
        ref_conflict_dict['ref'] = 3
        ref_conflict = Game(**ref_conflict_dict)
        team_conflict_dict = deepcopy(other_game_dict)
        team_conflict_dict['team2'] = 1
        team_conflict = Game(**team_conflict_dict)
        self_conflict_dict = deepcopy(other_game_dict)
        self_conflict_dict['team2'] = 6
        self_conflict = Game(**self_conflict_dict)
        self_vs_dict = deepcopy(other_game_dict)
        self_vs_dict['team2'] = 4
        self_vs = Game(**self_vs_dict)
        diff_time_dict = deepcopy(reference_game_dict)
        diff_time_dict['time'] = 2
        diff_time = Game(**diff_time_dict)
        self.assertEqual(0, Fit(facilities, [reference_game]).value())
        self.assertEqual(0, Fit(facilities, [reference_game,
                                             other_game]).value())
        conflict_and_double = -fitness.conflict_weight - 2
        self.assertEqual(conflict_and_double, Fit(facilities,
                                 [reference_game, ref_conflict]).value())
        self.assertEqual(conflict_and_double, Fit(facilities,
                                                  [reference_game,
                                                   team_conflict]).value())
        self.assertEqual(-fitness.conflict_weight, Fit(facilities,
                                                  [reference_game,
                                                   self_conflict]).value())
        error = -4 * fitness.default_vs_self - 4 + conflict_and_double
        self.assertEqual(error, Fit(facilities,[reference_game,
                                                self_vs]).value())
        self.assertEqual(-10, Fit(facilities,[reference_game,
                                              diff_time]).value())
        games = []
        for day in sch.days:
            games += day.games()
        self.assertEqual(-100, Fit(facilities, games).value())
        sch = make_schedule(facilities.team_counts, facilities, sch_tries=100)
        games = []
        for day in sch.days:
            games += day.games()
        self.assertEqual(0, Fit(facilities, games).value())
        sch_fitness = sum([day.fitness_str() for day in sch.days])
        self.assertEqual(0, sch_fitness.value())

if __name__ == '__main__':
    unittest.main()