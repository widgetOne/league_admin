



def check_schedule_vs_members(sch, members):
    if len(members) != len(sch.divisions):
        raise(ValueError('the members and schedule structures are inconsistent'))
    for div_idx, teams in enumerate(members):
        if len(teams) != len(sch.divisions[div_idx].teams):
            raise(ValueError('the members and schedule structures are inconsistent'))

def schedule_report():
    from schedule import load_reg_schedule
    sch = load_reg_schedule()

def load_members_and_debug():
    from schedule import load_reg_schedule
    from members import import_teams, member_debug_report
    sch = load_reg_schedule()
    members = import_teams()
    check_schedule_vs_members(sch, members)
    member_debug_report(members)

def debug_three_d(data):
    print('len D1 = {}'.format(len(data)))
    for idx_one, two_d in enumerate(data):
        print('({}) len D2 = {}'.format(idx_one,len(two_d)))
        for idx_two, one_d in enumerate(two_d):
            print('({},{}) len D3 = {}: {}'.format(idx_one,idx_two,
                                                   len(one_d),one_d))

def load_all_substitute_bins():
    import csv
    import copy
    import re
    path = ('/Users/coulter/Desktop/life_notes/2016_q2/scvl/' +
            'substitutes_2016_Spr.csv')
    bins = [[], [], []]
    sub_lists = [copy.deepcopy(bins) for _ in range(4)]
    with open(path, 'r') as sub_list_file:
        sub_reader = csv.DictReader(sub_list_file)
        divisions = ['Rec', 'Inter', 'Comp', 'Power']
        bin_names = ['Lower', 'Mid', 'Top']
        for line in sub_reader:
            for div_idx, div in enumerate(divisions):
                for bin_idx, bin in enumerate(bin_names):
                    for key, data in line.items():
                        if data and div in key and bin in key:
                            # need to filter out ratings info from names
                            name = re.sub(' \(.*\)', '', data)
                            sub_lists[div_idx][bin_idx].append(name)
    return sub_lists

def load_substitute_bins():
    import csv
    import copy
    path = ('/Users/coulter/Desktop/life_notes/2016_q2/scvl/' +
            'substitute_bins_rec_int_2016-01-Spr.csv')
    bins = [[],[],[]]
    sub_lists = [copy.deepcopy(bins), copy.deepcopy(bins)]
    with open(path, 'r') as sub_list_file:
        sub_reader = csv.reader(sub_list_file)
        for line in sub_reader:
            if line[0]:
                for idx, cell in enumerate(line[1:]):
                    if cell.strip():
                        div_idx = idx // 3
                        bin_idx = idx % 3
                        sub_lists[div_idx][bin_idx].append(cell)
    return sub_lists

def three_d_to_one_d(three_d_list):
    out = []
    for two_d in three_d_list:
        for one_d in two_d:
            out += one_d
    return out

def cross_check_sub_lists(teams, sub_lists):
    teams_one_d = three_d_to_one_d(teams[0:2])
    subs_one_d = three_d_to_one_d(sub_lists)
    teams_not_sub = [member for member in teams_one_d
                     if member not in subs_one_d]
    sub_not_teams = [member for member in subs_one_d
                     if member not in teams_one_d]
    print(teams_one_d)
    print(subs_one_d)
    print(len(teams_one_d))
    print(len(subs_one_d))
    print(teams_not_sub)
    print(sub_not_teams)
    print('\n')
    print([member for member in teams_one_d if 'Hodges' in member])
#  subs_not_teams = []

def teams_to_people(teams, specific_teams):
    people = []
    for specific in specific_teams:
        people += teams[specific[0]][specific[1]-1]
    return people

def find_subs_for_playoffs(people_missing):
    from members import import_teams
    sub_lists = load_all_substitute_bins()
    teams = import_teams()
    potential_subs = []
    for missing in people_missing:
        for div_subs in sub_lists:
            for bin in div_subs:
                if missing in bin:
                    potential_subs.append((missing,
                                           [sub for sub in bin
                                            if sub != missing]))
                    break
    busy_teams = [(1, num) for num in [11, 13, 1, 7, 5, 9]]
    best_teams = [(1, num) for num in [8, 6, 10, 3, 1]]

    all_player = three_d_to_one_d(teams)
    busy = teams_to_people(teams, busy_teams)
    best = teams_to_people(teams, best_teams)
    all_player.sort()
    busy.sort()
    best.sort()
    free = [sub for sub in all_player if (sub not in busy) and (sub not in best)]
    free.sort()
    subs = []
    for player, potentials in potential_subs:
        options = {}
        busy_subs = [sub for sub in busy if sub in potentials]
        best_subs = [sub for sub in best if sub in potentials]
        free_subs = [sub for sub in free if sub in potentials]
        options['best'] = best_subs
        options['free'] = free_subs
        options['player'] = player
        subs.append(options)
    return subs


def debug_options (subs):
    for options in subs:
        print('Player = {}'.format(options['player']))
        print('Best = {}'.format(options['best']))
        print('Free = {}'.format(options['free']),end='\n\n')


def make_league_df():
    from pandas import DataFrame
    from members import import_teams
    div_teams = import_teams()
    div_bins = load_all_substitute_bins()
    bins = sum(div_bins, [])
    targets = ['Jessica', 'Lexie']
    results = {}
    for target in targets:
        for bin_num, bin in enumerate(bins):
            #print(len(bin))
            for person in bin:
                if target in person:
                    #print(bin_num, bin)
                    break
        if target in results:
            break
    from pprint import pprint
    people = {}
    def find_team (name, teams):
        for team_idx, team in enumerate(teams):
            for person in team:
                if name in person:
                    return team_idx
        return -1
    for div_idx, (bins, teams) in enumerate(zip(div_bins, div_teams)):
        for bin_idx, bin in enumerate(bins):
            for person in bin:
                team_idx = find_team(person, teams)
                int_team = find_team(person, div_teams[1])
                people[person] = {'div': div_idx, 'bin': bin_idx,
                                  'team': team_idx, 'int_team': int_team}
    df = DataFrame(people)
    df = df.transpose()
    comp_busy = [4, 6, 7] # really, 5, 7, 8
    int_busy = [11, 9, 1] # really, 12, 10, 2

    print('\n\nbusy')
    brian_int = df.loc[df['bin'] == 0].loc[df['div'] == 2].loc[
        df['int_team'].isin(int_busy)]
    lexies = df.loc[df['bin'] == 1].loc[df['div'] == 2].loc[
        df['team'].isin(comp_busy)]
    jeses = df.loc[df['bin'] == 0].loc[df['div'] == 2].loc[
        df['team'].isin(comp_busy)]
    pprint(", ".join(brian_int.index.values))
    pprint(", ".join(lexies.index.values))
    pprint(", ".join(jeses.index.values))

    print('\n\nyes')
    brian_int = df.loc[df['bin']==0].loc[df['div']==2].loc[~df['int_team'].isin(int_busy)]
    lexies = df.loc[df['bin']==1].loc[df['div']==2].loc[~df['team'].isin(comp_busy)]
    jeses = df.loc[df['bin']==0].loc[df['div']==2].loc[~df['team'].isin(comp_busy)]
    pprint(len(brian_int))
    pprint(len(lexies))
    pprint(len(jeses))
    print(", ".join(brian_int.index.values))
    print(", ".join(lexies.index.values))
    print(", ".join(jeses.index.values))

    #pprint(len(lexies), lexies)
    #pprint(len(jeses), jeses)

def import_main_ratings_list():
    path = "/Users/coulter/Desktop/life_notes/2016_q2/scvl/master_take_2.csv"
    with open(path, "r") as ratings_file:
        for line in ratings_file:
            pass

def analyze_bin_accuracy():
    from members import import_teams
    sub_lists = load_all_substitute_bins()
    print(sub_lists)

def pandas_sub_check():
    make_league_df()

if __name__ == '__main__':
    from optimizer import get_default_potential_sch_loc, get_schedules
    canned_path = get_default_potential_sch_loc('2016-09-10')
    schedules = get_schedules(canned_path)
    #maker.summarize_canned_schedules()



