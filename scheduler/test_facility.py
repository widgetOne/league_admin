from unittest import TestCase
import unittest
import facility

__author__ = 'coulter'

class TestSchedulerFacility(TestCase):

    def test_league_regular_odd_not_full(self):
        team_counts = [6,11,12,7]
        count_court = 5
        day_count = 2
        league = facility.League(ndivs=4, ndays=day_count, ncourts=5, ntimes=4,
                                 team_counts=team_counts,
                                 day_type=facility.SCVL_Facility_Day)
        self.assertEqual(len(league.days), day_count)
        self.assertEqual(sum(league.games_per_div),
                         sum(team_counts) // 2 * day_count)
        for div_idx in range(len(team_counts)):
            self.assertEqual(league.games_per_div[div_idx] * 2,
                             team_counts[div_idx] * day_count)

        team_counts = [6,11,12,7]
        day_count = 9
        league9 = facility.League(ndivs=4, ndays=day_count, ncourts=5, ntimes=4,
                                 team_counts=team_counts,
                                 day_type=facility.SCVL_Facility_Day)
        self.assertEqual(len(league9.days), day_count)
        self.assertEqual(sum(league9.games_per_div * 2),
                         sum(team_counts) * day_count)
        for div_idx in range(len(team_counts)):
            self.assertAlmostEqual(league9.games_per_div[div_idx] * 2,
                                    team_counts[div_idx] * day_count, delta=1)


        team_counts = [6,13,14,7]
        day_count = 9
        league_full = facility.League(ndivs=4, ndays=day_count, ncourts=5, ntimes=4,
                                 team_counts=team_counts,
                                 day_type=facility.SCVL_Facility_Day)
        self.assertEqual(len(league_full.days), day_count)
        self.assertEqual(sum(league_full.games_per_div * 2),
                         sum(team_counts) * day_count)
        for div_idx in range(len(team_counts)):
            self.assertAlmostEqual(league_full.games_per_div[div_idx] * 2,
                                    team_counts[div_idx] * day_count, delta=1)


    #        self.assertGreaterEqual(league9.games_per_div[div_idx] * 2,
    #                                team_counts[div_idx] * day_count )

    def test_league_regular_even(self):
        team_counts = [6,14,14,6]
        count_court = 5
        day_count = 1
        league = facility.League(ndivs=4, ndays=day_count, ncourts=5, ntimes=4,
                                 team_counts=team_counts,
                                 day_type=facility.SCVL_Facility_Day)
        self.assertEqual(len(league.days), day_count)
        self.assertEqual(sum(league.games_per_div),
                         sum(team_counts) // 2 * day_count)

        day_count = 9
        league_9d = facility.League(ndivs=4, ndays=day_count, ncourts=5, ntimes=4,
                                    team_counts=team_counts,
                                    day_type=facility.SCVL_Facility_Day)
        self.assertEqual(len(league_9d.days), day_count)
        self.assertEqual(sum(league_9d.games_per_div),
                         sum(team_counts) // 2 * day_count)

    def test_regular_season_day_no_overflow(self):
        from facility import SCVL_Facility_Day
        team_counts = [6, 12, 12, 6]
        count_court = 5
        day = SCVL_Facility_Day(court_count=count_court, time_count=4,
                                team_counts=team_counts, rec_first=True)
        first_games = [day.court_divisions[icourt][0] for icourt
                       in range(count_court)]
        last_games = [day.court_divisions[icourt][3] for icourt
                      in range(count_court)]
        self.assertEqual(len(day.court_divisions), 5)
        self.assertEqual(sum(day.games_per_division) * 2, sum(team_counts))
        self.assertTrue(0 in first_games)
        self.assertTrue(0 not in last_games)
        for div_idx in range(len(team_counts)):
            self.assertEqual(day.games_per_division[div_idx] * 2,
                             team_counts[div_idx])

        day_rec_last = SCVL_Facility_Day(court_count=count_court, time_count=4,
                                         team_counts=team_counts,
                                         rec_first=False)
        first_games = [day_rec_last.court_divisions[icourt][0] for icourt
                       in range(count_court)]
        last_games = [day_rec_last.court_divisions[icourt][3] for icourt
                      in range(count_court)]
        self.assertTrue(0 not in first_games)
        self.assertTrue(0 in last_games)

    def test_regular_season_day_full(self):
        from facility import SCVL_Facility_Day
        team_counts = [6, 14, 14, 6]
        day = SCVL_Facility_Day(court_count=5, time_count=4,
                                team_counts=team_counts, rec_first=True)
        self.assertEqual(len(day.court_divisions), 5)
        self.assertEqual(sum(day.games_per_division) * 2, sum(team_counts))


    def test_regular_season_day_odd_teams(self):
        '''This test is support to give a number too low. For odd
        numbers of teams, the final games should be handled by league'''
        from facility import SCVL_Facility_Day
        team_counts = [6, 13, 14, 7]
        day = SCVL_Facility_Day(court_count=5, time_count=4,
                                team_counts=team_counts, rec_first=True)
        WRONG_GAME_COUNT = sum(team_counts) // 2 - 1
        self.assertEqual(len(day.court_divisions), 5)
        self.assertEqual(sum(day.games_per_division), WRONG_GAME_COUNT)

    def test_1_day_w_5_divisions_facility(self):
        from facility import SCVL_Advanced_Regular_Day
        team_counts = [8, 10, 4, 10, 8]
        #team_counts = [8, 10, 4, 10]
        day = SCVL_Advanced_Regular_Day(court_count=5, time_count=5,
                                team_counts=team_counts, rec_first=True)
        ##self.assertEqual(len(day.court_divisions), 5)
        print(day)

    def test_new_fac_method(self):
        new_fac_str = facility.Facility_Space([(4,5)])

if __name__ == '__main__':
    unittest.main()