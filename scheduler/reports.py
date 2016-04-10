



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

def find_subs_for_playoffs():
    from members import import_teams, member_debug_report
    people_missing = ['Amy Buzzard', 'Christine Chedwick']
    sub_lists = load_substitute_bins()
    teams = import_teams()
    potential_subs = []
    for missing in people_missing:
        for bin in sub_lists[1]:
            if missing in bin:
                potential_subs.append((missing,
                                       [sub for sub in bin if sub != missing]))
                break
    busy_teams = [(1, 11), (1, 13), (1, 8), (1, 6), (1, 10), (1, 3), (1, 2)]
    best_teams = [(1, 1), (1, 7), (1, 5), (1, 9)]
    intermediate = three_d_to_one_d([teams[1]])
    busy = teams_to_people(teams, busy_teams)
    best = teams_to_people(teams, best_teams)
    free = [sub for sub in intermediate if sub not in busy and sub not in best]

    subs = []
    for player, potentials in potential_subs:
        options = {}
        best_subs = [sub for sub in best if sub in potentials]
        free_subs = [sub for sub in free if sub in potentials]
        options['best'] = best_subs
        options['free'] = free_subs
        options['player'] = player
        print('Player = {}'.format(player))
        print('Best = {}'.format(best_subs))
        print('Free = {}'.format(free_subs),end='\n\n')
        subs.append(options)

if __name__ == '__main__':
    find_subs_for_playoffs()
