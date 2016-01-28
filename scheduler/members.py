from pprint import pprint

team_file_2016_Spr = ('/Users/coulter/Desktop/life_notes/2016_q1/' +
                     'scvl/ratings/teams_for_import_2016-Spr.csv-Sheet1.csv')

def import_teams():
    import csv
    from copy import deepcopy
    divisions = []
    with open(team_file_2016_Spr, 'r') as team_file:
        team_data = csv.reader(team_file)
        team_nums_cols = []
        for line in team_data:
            # checking for a new division and saving the previous teams
            if line[0] != '':
                if team_nums_cols != [] and len(team_nums_cols) >= 0:
                    divisions.append(deepcopy(division_teams))
                current_div = int(line[0])
                division_teams = []
            # checking for new team names
            if any(("team" in cell.lower()) for cell in line):
                team_nums_cols = collect_team_columns(line)
                # assumes that teams are read in order
                division_teams += [[] for _ in range(len(team_nums_cols))]
            else:
                # collecting team-wise data
                if team_nums_cols:
                    for team_idx, column in team_nums_cols:
                        if line[column] != '':
                            division_teams[team_idx] += [line[column]]
    return divisions

def collect_team_columns(line):
    team_nums_cols = []
    for idx, cell in enumerate(line):
        if 'team' in cell.lower():
            cell = cell.lower()
            cell = cell.replace('team','')
            cell = cell.replace(' ','')
            team_num = int(cell) - 1 # team 1 is stored internally as 0, etc
            team_nums_cols.append((team_num, idx))
    return team_nums_cols

def check_if_person_in_division(member, members):
    found = False
    for div_mem in members:
        for team_mem in div_mem:
            if member in team_mem:
                return True
    else:
        raise(ValueError('member %s in division %s could not be found in '
                         'any division' % (member)))

def translate_division(div_team_string):
    pass

def import_ratees():
    import csv
    from copy import deepcopy
    ratees_path = '/Users/coulter/Desktop/life_notes/2016_q1/scvl/'
    ratees_file = 'Mid-Season-Rerating-List.csv'
    ratees = []
    with open(ratees_path + ratees_file, 'r') as ratee_file:
        ratee_data = csv.DictReader(ratee_file)
        ratee_nums_cols = []
        for line in ratee_data:
            line['name'] = line['PLAYER']
            ratees += [line]


if __name__ == '__main__':
    divisions = import_teams()
    #pprint(divisions)
    import_ratees()