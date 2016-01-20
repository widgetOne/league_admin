from unittest import TestCase
from maker import make_schedule
import facility

__author__ = 'coulter'

def make_fac_day(self, team_counts):
    from facility import SCVL_Facility_Day
    court_count = 5
    time_count = 4
    team_counts = team_counts
    rec_first = True
    fac_day = SCVL_Facility_Day(court_count, time_count, team_counts,
             rec_first)
    return fac_day

class TestSchedulerModel(TestCase):
    from schedule import Schedule
    def test_simple_day_even_spares(self):
        fac_day = make_fac_day([6,12,12,6])

    # day = self.make_day(facs[day_idx])