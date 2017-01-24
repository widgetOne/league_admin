from model import init_value
#
# Day Design:
# The process will proceed in two waves:
#    1. All days will be populated with As or Bs for the groups
#           This will establish open play and the A/B dividers
#    2. A second sweep will the change the letter blocks to league games slots
#           This will ensure each league has the slots it needs for each div
#
def csv_file_to_list_list(csv_path):
    pass

def make_league_from_csv(team_counts, csv):
    ndivs = len(team_counts)
    ndays = len(csv)
    ncourts = len(csv[0])
    ntimes = len(csv[0][0])
    day_type = Facility_Day
    return Facility(ndivs, ndays, ncourts, ntimes, team_counts, day_type, csv)

class Facility(object):
    '''This is basically all the set characteristics of the problem'''
    def __init__(self, ndivs, ndays, ncourts, ntimes, team_counts, day_type,
                 csv=None):
        self.ndivs = ndivs
        self.ndays = ndays
        self.ncourts = ncourts
        self.ntimes = ntimes
        self.team_counts = team_counts
        self.day_type = day_type
        self.days = []
        self.games_per_div = [0] * len(self.team_counts)

        if csv:
            for day_idx, day_csv in enumerate(csv):
                day = Facility_Day(team_counts, day_idx, csv_obj=day_csv)
                self.days.append(day)
                for div_idx in range(ndivs):
                    self.games_per_div[div_idx] += day.games_per_division[div_idx]
        else:
            for day_idx in range(ndays):
                rec_first = day_idx % 2 == 1
                day = SCVL_Facility_Day(court_count=ncourts, time_count=ntimes,
                                        team_counts=team_counts,
                                        rec_first=rec_first, day_idx=day_idx)
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

    def game_count(self):
        return sum((day.game_count() for day in self.days))

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
        print('games per div * 2 = %s' % ', '.join(
              [str(num * 2) for num in self.games_per_div]))
        print('games need for team_counts = %s' % ', '.join(
              [str(num * self.ndays) for num in self.team_counts]))
        for div_idx in range(self.ndivs):
            print('Division %s ' % div_idx, end='')
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
            print(day)
        self.debug_deltas()

    def csv(self):
        filler = '\n' + ',' * self.ncourts + '\n'
        return filler.join([day.csv() for day in self.days])

    def __repr__(self):
        return self.csv()

    def get_bye_target(self):
        bye_targets = [0] * len(self.team_counts)
        for day in self.days:
            games_per_division = day.get_games_per_division()
            for div_idx, (games, teams) in enumerate(zip(games_per_division, self.team_counts)):
                byes_needed = max(teams - games * 2, 0)
                bye_targets[div_idx] += byes_needed
        return bye_targets

def sch_template_path_to_fac(template_path, team_counts):
    with open(template_path, 'r') as template_file:
        sch_template_csv = template_file.read()
    sch_template_lists = csv_str_to_fac_list_list(sch_template_csv)
    fac = make_league_from_csv(team_counts, sch_template_lists)
    return fac

def transpose_2d_list_of_lists(list_of_lists):
    return list(map(list, zip(*list_of_lists)))

def csv_str_to_fac_list_list(csv_str):
    '''this takes in a string for a csv file and returns an object of the
    the followings structure: list days[courts[times[]]] '''
    rows = csv_str.split('\n')
    rows = [row.split(',') for row in rows]
    day = []
    days = []
    for row in rows:
        there_are_no_games_in_row = not(any(row)) or all((div == '-1' for div in row))
        if there_are_no_games_in_row:
            if day:
                days += [day]
                day = []
            continue
        day += [row]
    if day:
        days += [day]
    return [transpose_2d_list_of_lists(day) for day in days]


def are_games_rec_first(csv_obj):
    for court in csv_obj:
        if '0' in court[0:1]:
            return True
    return False

class Facility_Day(object):
    def __init__(self, team_counts, day_idx, court_count=None, time_count=None,
                 csv_obj=None):
        self.day_idx = day_idx
        self.team_counts = team_counts
        self.games_per_division = [0] * len(team_counts)
        self.div_times_games = [[] for _ in range(len(self.team_counts))]
        self.div_games = [[] for _ in range(len(self.team_counts))]
        if csv_obj:
            self.rec_first = are_games_rec_first(csv_obj)
            self.set_div_times_locs()
            self.court_count = len(csv_obj)
            self.time_count = len(csv_obj[0])
            self.refs = True  # todo: HACK, remove once fitness class is used
            def str_to_game_div(game):
                if game == 'X' or game == '-1':
                    return init_value
                else:
                    return int(game)
            self.court_divisions = csv_obj
            for court, row in enumerate(csv_obj):
                for time, game_str in enumerate(row):
                    game_div = str_to_game_div(game_str)
                    self.court_divisions[court][time] = game_div
                    if game_div != init_value:
                        self.add_game(court, time, game_div)
        elif court_count and time_count:
            self.court_count = court_count
            self.time_count = time_count
            self.court_divisions = [[init_value for _ in range(time_count)]
                           for __ in range(court_count)]
            self.set_division()
        else:
            raise (ValueError("no arguements were passed to Facility_Day, " +
                              "which expects at least one"))

    def set_division(self):
        raise(NotImplementedError("missing contrete implimentation " +
                                  "of abstract set_division method"))
        # logic will be need for how these divisions are set

    def game_count(self):
        return self.court_count * self.time_count

    def csv(self):
        rows = []
        for time in range(len(self.court_divisions[0])):
            def game_div_to_str(game):
                if game == init_value:
                    return 'X'
                else:
                    return str(game)
            games = [game_div_to_str(self.court_divisions[court][time]) for
                     court in range(len(self.court_divisions))]
            rows += [','.join(games)]
        return '\n'.join(rows)

    def __repr__(self):
        return self.csv()

    def add_game(self, court, time, div_idx):
        if div_idx != init_value:
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
                    out.append((court, time))
        return out

    def set_div_times_locs(self):
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

    def get_games_per_division(self):
        games_per_division = [0] * len(self.team_counts)
        for court in self.court_divisions:
            for game_div in court:
                if game_div > -1:
                    games_per_division[game_div] += 1
        return games_per_division

class SCVL_Facility_Day(Facility_Day):
    def __init__(self, court_count, time_count, team_counts, rec_first, day_idx):
        self.rec_first = rec_first
        super(SCVL_Facility_Day, self).__init__(team_counts, day_idx, court_count,
                                                time_count)
        self.refs = True

    def set_division(self):
        from random import choice
        self.set_div_times_locs()
        spares_rc_ip = [[] for _ in range(2)] # note rec and comp share slots, etc
        spare_slots = spares_rc_ip + spares_rc_ip
        spare_div = [2,3,0,1]

        # eventually, odd numbers of teams will be dealt with here

        # first pass
        for div_idx in range(len(self.team_counts)):
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

        for div_idx in range(len(self.team_counts)):
            locs, times = self.div_times_locs[div_idx]
            for idx in range(self.team_counts[div_idx] // 2 -
                                             len(locs) * len(times) ):
                if len(spare_slots[div_idx]) < 1:
                    break
                court, time = spare_slots[div_idx][0]
                self.add_game(court, time, div_idx)
                del spare_slots[div_idx][0]


class SCVL_Round_Robin(Facility_Day):
    def __init__(self, court_count, time_count, team_counts,
                 rec_first, games_per_div):
        self.rec_first = True
        super(SCVL_Round_Robin, self).__init__(team_counts, court_count,
                                               time_count)
        self.refs = False

class SCVL_Advanced_Regular_Day(Facility_Day):
    def __init__(self, court_count, time_count, team_counts, rec_first):
        self.team_type_counts[0:1] = [sum(team_counts[0::2]),
                                      sum(team_counts[1::2])]
        self.rec_first = True
        super(SCVL_Advanced_Regular_Day, self).__init__(team_counts,
                                                        court_count, time_count)
        self.refs = False

    def set_division(self):
        pass

'''
class Facility_Space(object):
    def __init__(self, time_court_days=None, time_court_array_of_days=None):
        self.time_court_
        if time_court_array_of_days:
            pass
        elif time_court_days:
            pass
        else:
            raise(Exception('unknown init method for {}'.format(type(self))))

'''