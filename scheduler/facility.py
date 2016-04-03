
from model import init_value

class League(object):
    '''This is basically all the set characteristics of the problem'''
    def __init__(self, ndivs, ndays, ncourts, ntimes, team_counts, day_type):
        self.ndivs = ndivs
        self.ndays = ndays
        self.ncourts = ncourts
        self.ntimes = ntimes
        self.team_counts = team_counts
        self.day_type = day_type
        self.days = []
        if (ncourts * ntimes * 2 < sum(team_counts)):
            raise(ValueError("This schedule has too many teams for its courts"))
        self.games_per_div = [0] * 4
        for day_idx in range(ndays):
            rec_first = day_idx % 2 == 1
            day = SCVL_Facility_Day(court_count=ncourts, time_count=ntimes,
                                    team_counts=team_counts,
                                    rec_first=rec_first)
            self.days.append(day)
            for div_idx in range(ndivs):
                self.games_per_div[div_idx] += day.games_per_division[div_idx]
        odd_division = [count % 2 == 1 for count in team_counts]
        if (not any(odd_division)):
            return
            # handling odd divisions
        div_missing_games = self.div_missing_games_list()
        if len(div_missing_games) % 2 == 1:
            raise(NotImplemented("This code not designed for a odd " +
                                 "total number of teams, only odd teams " +
                                 'per division.'))
        self.odd_team_game_per_day = len(div_missing_games) // 2
        for day in self.days:
            div_missing_games = self.div_missing_games_list()
            self.games_per_div = day.add_odd_games(div_missing_games,
                                                   self.games_per_div,
                                                   self.odd_team_game_per_day)

        return

    def div_missing_game_count(self, div_idx):
        expected = self.ndays * self.team_counts[div_idx]
        if self.games_per_div == None:
            asdf = 5
        has = self.games_per_div[div_idx] * 2
        return expected - has

    def div_missing_games_list(self):
        out = [div_idx for div_idx in range(self.ndivs)
               if self.div_missing_game_count(div_idx) > 0]
        out.sort(key=lambda x: self.div_missing_game_count(x))
        return out

    def debug_deltas(self):
        print('deltas for each division')
        print('games per div * 2 = %s' % ','.join(
              [str(num * 2) for num in self.games_per_div]))
        print('games need for team_counts = %s' % ','.join(
              [str(num * self.ndays) for num in self.team_counts]))
        for div_idx in range(self.ndivs):
            print('Division %s ', end='')
            delta = self.div_missing_game_count(div_idx)
            if (delta < 0):
                print('has %s too FEW games.' % delta)
            elif (delta == 0):
                print('is good.')
            elif (delta > 0):
                print('has %s EXTRA games.' % delta)

    def debug_print(self):
        debug_params = [
            (self.ndivs, "self.ndivs"), (self.ndays, "self.ndays"),
            (self.ncourts, "self.ncourts"),
         ]
        for value, name in debug_params:
            print("Parameter %s has a value of %s" % (name, value))
        print("day summary:")
        for day_idx, day in enumerate(self.days):
            print("summary of facility day %s" % day_idx)
            day.debug_print()
        self.debug_deltas()

class Facility_Day(object):
    def __init__(self, court_count, time_count):
        self.court_count = court_count
        self.time_count = time_count
        self.refs = False
        self.court_divisions = [[init_value for _ in range(time_count)]
                       for __ in range(court_count)]
        self.div_times_locs = []
        self.day_type = init_value # tool for distinguishing types for days during mutation
        self.div_games = []
        self.set_division()

    def set_division(self):
        raise(NotImplementedError("missing contrete implimentation of abstract set_division method"))
        # logic will be need for how these divisions are set

    def debug_print(self):
        print("rec first = %s" % self.rec_first)
        for time in range(len(self.court_divisions[0])):
            for court in range(len(self.court_divisions)):
                print(self.court_divisions[court][time], end='')
            print("")

    def add_game(self, court, time, div_idx):
        self.court_divisions[court][time] = div_idx
        self.div_times_games[div_idx].append((court, time))
        self.games_per_division[div_idx] += 1
        self.div_games[div_idx].append((court, time))

    def add_odd_games(self, div_missing_games, games_per_div, days_to_add):
        for court, time in self.open_slots():
            for div_idx in div_missing_games:
                times = self.div_times_locs[div_idx][1] # array of (courts, locs)
                if time in times:
                    self.add_game(court, time, div_idx)
                    games_per_div[div_idx] += 1
                    days_to_add -= 1
                    if days_to_add == 0:
                        return games_per_div
                    break
        raise(Exception('This should never happen.'))

    def open_slots(self):
        out = []
        for court, times in enumerate(self.court_divisions):
            for time, div_idx in enumerate(times):
                if div_idx <= -1:
                    out.append((court,time))
        return out

class SCVL_Facility_Day(Facility_Day):
    def __init__(self, court_count, time_count, team_counts,
                 rec_first):
        self.rec_first = rec_first
        if (rec_first):
            self.day_type = 0
        else:
            self.day_type = 1
        self.team_counts = team_counts
        self.rec_first = rec_first
        self.games_per_division = [0] * 4
        super(SCVL_Facility_Day, self).__init__(court_count, time_count)
        self.refs = True

    def set_division(self):
        from random import choice
        inner = [1,2,3]
        outer = [0,4]
        first_slots = [0,1]
        later_slots = [2,3]

        if self.rec_first:
            rec_comp_times = first_slots
            inter_power_times = later_slots
        else:
            rec_comp_times = later_slots
            inter_power_times = first_slots

        self.div_times_locs = [
                            (outer, rec_comp_times),
                            (inner, inter_power_times),
                            (inner, rec_comp_times),
                            (outer, inter_power_times),
                             ]
        self.alternate_div_loc = [inner, outer, outer, inner]
        self.div_games = [[] for _ in range(4)]
        self.div_times_games = [[] for _ in range(4)]
        spares_rc_ip = [[] for _ in range(2)] # note rec and comp share slots, etc
        spare_slots = spares_rc_ip + spares_rc_ip
        spare_div = [2,3,0,1]

        # eventually, odd numbers of teams will be dealt with here

        # first pass
        for div_idx in range(4):
            games = self.team_counts[div_idx] // 2
            locs, times = self.div_times_locs[div_idx]
            game_slots = [(x,y) for x in locs for y in times]
            for _ in range(len(game_slots) > games): # save off any extra games
                rm_loc = choice(range(games))
                spare_slots[spare_div[div_idx]].append(game_slots[rm_loc])
                del game_slots[rm_loc]
            for court, time in game_slots:
                self.add_game(court, time, div_idx)
        # filling in gaps

        for div_idx in range(4):
            locs, times = self.div_times_locs[div_idx]
            alternate_idx = spare_div[div_idx]
        #    ave_games = self.games_per_division[div_idx] / self.team_counts[div_idx]
        #    ave_alt_games = self.games_per_division[alternate_idx] / self.team_counts[alternate_idx]
        #    take_slot = ave_games <= ave_alt_games
            for idx in range(self.team_counts[div_idx] // 2 -
                                             len(locs) * len(times) ):
                if len(spare_slots[div_idx]) < 1:
                    break
                court, time = spare_slots[div_idx][0]
                self.add_game(court, time, div_idx)
                del spare_slots[div_idx][0]


class SCVL_Round_Robin(Facility_Day):
    def __init__(self, court_count, time_count, team_counts, rec_first, games_per_div):
        if (rec_first):
            self.day_type = 0
        else:
            self.day_type = 1
        self.team_counts = team_counts
        self.rec_first = True
        super(SCVL_Round_Robin, self).__init__(court_count, time_count)
        self.refs = False

    def set_division(self):
        from copy import deepcopy
        inner = [1,2,3]
        outer = [0,4]
        first_slots = [0,1]
        later_slots = [2,3]
        if self.rec_first:
            rec_comp_times = first_slots
            inter_power_times = later_slots
        else:
            rec_comp_times = first_slots
            inter_power_times = later_slots
        self.div_times_locs = [
                            (outer, rec_comp_times),
                            (inner, inter_power_times),
                            (inner, rec_comp_times),
                            (outer, inter_power_times),
                             ]
        self.alternate_div_loc = [inner, outer, outer, inner]
        self.div_times_games = [[] for _ in range(4)]
        self.div_games = [[] for _ in range(4)]

        times = []
        gap = [init_value] * 5
        comp = [2,2,2,2,2]
        comp_r = [0,2,2,2,2]
        rec_comp = [0,2,2,2,0]
        pow_int = [3,1,1,1,3]
        inter_p = [3,1,1,1,1]
        int_gap = [1] + ([init_value] * 4)
        times += [gap for _ in range(1)]
        times += [comp for _ in range(1)]
        times += [comp_r for _ in range(1)]
        times += [rec_comp for _ in range(4)]
        times += [gap for _ in range(2)]
        times += [pow_int for _ in range(5)]
        times += [inter_p for _ in range(1)]
        times += [int_gap for _ in range(1)]
        ntime = len(times)
        temp_div_games = [0] * 4
        self.court_divisions = times
        for time, courts in enumerate(times):
            for court, div_idx in enumerate(courts):
                if times[time][court] >= 0:
                    temp_div_games[div_idx] += 1
                    slot = deepcopy((court, time))
                    self.div_times_games[div_idx].append(slot)
                    self.div_games[div_idx].append(slot)
                ##    self.team_counts[times[time][court]] += 1
        from pprint import pprint
        print("games for each division")
        pprint(temp_div_games)