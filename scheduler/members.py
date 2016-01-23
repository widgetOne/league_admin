



team_file_2016_Spr = ('/Users/coulter/Desktop/life_notes/2016_q1/' +
                     'scvl/ratings/teams_for_import_2016-Spr.csv-Sheet1.csv')

print(team_file_2016_Spr)

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

if __name__ == '__main__':
    from pprint import pprint
    divisions = import_teams()
    #pprint(divisions)