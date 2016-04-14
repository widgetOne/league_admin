from unittest import TestCase
import fitness
__author__ = 'coulter'

def check_total_sizes(assert_true, div_totals, count):
    assert_true(len(div_totals._plays) == count)
    assert_true(len(div_totals._refs) == count)
    assert_true(len(div_totals._vs) == count)
    assert_true(len(div_totals._vs[0]) == count)
    assert_true(len(div_totals._vs[count - 1]) == count)

def basic_facilities():
    from facility import SCVL_Facility_Day
    from facility import League
    team_counts = [6, 13, 14, 7]
    ndays = 1
    facilities = League(ndivs=4, ndays=ndays, ncourts=5, ntimes=4,
                        team_counts=team_counts, day_type=SCVL_Facility_Day)
    blank_totals = fitness.ScheduleFitness(facilities)
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
        print('asdf')
        print(local_sum.fitness())