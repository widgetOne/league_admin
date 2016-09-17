from optimizer import make_schedule
import facility
import unittest
import model
__author__ = 'coulter'


def make_fac_day(team_counts):
    from facility import SCVL_Facility_Day
    court_count = 5
    time_count = 4
    team_counts = team_counts
    rec_first = True
    fac_day = SCVL_Facility_Day(court_count, time_count, team_counts,
                                rec_first)
    return fac_day

'''
class TestSchedulerModel(TestCase):
    def test_simple_day_even_spares(self):
        from schedule import Schedule
        fac_day = make_fac_day([6, 12, 12, 6])
        # day = self.make_day(facs[day_idx])
'''

sample = model.Game(team1=1, team2=0, ref=2,
                    div=0, time=0, court=0)
no_ref = model.Game(team1=1, team2=0,
                    div=0, time=1, court=0)

class TestModelGame(unittest.TestCase):
    def test_game_display(self):
        print(sample.csv_str())

        self.assertEqual(1,1)


if __name__ == '__main__':
    unittest.main()