
class Facility_Day(object):
    def __init__(self, court_count, time_count):
        self.court_count = court_count
        self.time_count = time_count
        self.refs = False
        self.court_divisions = [[-1 for _ in range(time_count)]
                       for __ in range(court_count)]
        self.div_times_locs = []
        self.day_type = -1 # tool for distinguishing types for days during mutation
        self.div_games = []
        self.set_division()

    def set_division(self):
        raise(NotImplementedError("missing contrete implimentation of abstract set_division method"))
        # logic will be need for how these divisions are set


class SCVL_Facility_Day(Facility_Day):
    def __init__(self, court_count, time_count, team_counts, rec_first):
        self.rec_first = rec_first
        if (rec_first):
            self.day_type = 0
        else:
            self.day_type = 1
        self.team_counts = team_counts
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
        spare_slots = [[] for _ in range(4)]
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
        # filling in gaps
        for div_idx in range(4):
            locs, times = self.div_times_locs[div_idx]
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
    def __init__(self, court_count, time_count, team_counts, rec_first):
        if (rec_first):
            self.day_type = 0
        else:
            self.day_type = 1
        self.team_counts = team_counts
        super(SCVL_Facility_Day, self).__init__(court_count, time_count)
        self.refs = False

    def set_division(self):
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
        spare_slots = [[] for _ in range(4)]
        spare_div = [2,3,0,1]
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
        # filling in gaps
        for div_idx in range(4):
            locs, times = self.div_times_locs[div_idx]
            for idx in range(self.team_counts[div_idx] // 2 -
                                             len(locs) * len(times) ):
                if len(spare_slots[div_idx]) < 1:
                    raise(Exception())
                court, time = spare_slots[div_idx][0]
                self.court_divisions[court][time] = div_idx
                self.div_times_games[div_idx].append((court, time))
                self.div_games[div_idx].append(spare_slots[div_idx][0])
                del spare_slots[div_idx][0]
