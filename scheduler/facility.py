
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

        self.games_per_div = [0 for _ in range(ndivs)]
        for day_idx in range(ndays):
            rec_first = day_idx % 2 == 1
            self.days.append(day_type(ncourts, ntimes, team_counts,
                                      rec_first, self.games_per_div))

class Facility_Day(object):
    def __init__(self, court_count, time_count, game_totals):
        self.court_count = court_count
        self.time_count = time_count
        self.refs = False
        self.court_divisions = [[-1 for _ in range(time_count)]
                       for __ in range(court_count)]
        self.div_times_locs = []
        self.day_type = -1 # tool for distinguishing types for days during mutation
        self.div_games = []
        self.set_division(game_totals)

    def set_division(self):
        raise(NotImplementedError("missing contrete implimentation of abstract set_division method"))
        # logic will be need for how these divisions are set


class SCVL_Facility_Day(Facility_Day):
    def __init__(self, court_count, time_count, team_counts,
                 rec_first, games_per_division):
        self.rec_first = rec_first
        if (rec_first):
            self.day_type = 0
        else:
            self.day_type = 1
        self.team_counts = team_counts
        self.refs = True
        super(SCVL_Facility_Day, self).__init__(court_count, time_count,
                                                games_per_division)

    def set_division(self, game_totals):
        from random import choice
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
        self.div_games = []
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
            self.div_games.append(game_slots)
            for court, time in game_slots:
                self.court_divisions[court][time] = div_idx
                self.div_times_games[div_idx].append((court, time))
                self.team_counts[div_idx] += 1
        # filling in gaps
        for div_idx in range(4):
            locs, times = self.div_times_locs[div_idx]
            alternate_idx = spare_div[div_idx]
            ave_games = game_totals[div_idx] / self.team_counts[div_idx]
            ave_alt_games = game_totals[alternate_idx] / self.team_counts[alternate_idx]
            take_slot = ave_games <= ave_alt_games
            for idx in range(self.team_counts[div_idx] // 2 -
                                             len(locs) * len(times) ):
                if len(spare_slots[div_idx]) < 1:
                    raise(Exception())
                court, time = spare_slots[div_idx][0]
                self.court_divisions[court][time] = div_idx
                self.div_times_games[div_idx].append((court, time))
                self.div_games[div_idx].append(spare_slots[div_idx][0])
                del spare_slots[div_idx][0]


class SCVL_Round_Robin(Facility_Day):
    def __init__(self, court_count, time_count, team_counts, rec_first, games_per_div):
        if (rec_first):
            self.day_type = 0
        else:
            self.day_type = 1
        self.team_counts = team_counts
        self.rec_first = True
        super(SCVL_Round_Robin, self).__init__(court_count, time_count, games_per_div)
        self.refs = False

    def set_division(self, games_per_div):
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
        inter = [1,1,1,1,1]
        pow_int = [3,1,1,1,3]
        rec_comp = [0,2,2,2,0]
        comp = [2,2,2,2,2]
        gap = [-1,-1,-1,-1,-1]
        times += [gap for _ in range(1)]
        times += [inter for _ in range(1)]
        times += [pow_int for _ in range(7)]
        times += [gap for _ in range(1)]
        times += [rec_comp for _ in range(6)]
        times += [comp for _ in range(2)]
        ntime = len(times)
        self.court_divisions = times
        for time, courts in enumerate(times):
            for court, div in enumerate(courts):
                if times[time][court] >= 0:
                    slot = deepcopy((court, time))
                    self.div_times_games[div].append(slot)
                    self.div_games[div].append(slot)
                ##    self.team_counts[times[time][court]] += 1
