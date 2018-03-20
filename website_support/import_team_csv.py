from pprint import pprint
import re


def import_team_scvl(team_path):
    with open(team_path, 'r') as team_file:
        lines = team_file.read()
    lines = lines.replace('\r', '')
    div = 0
    league = [[], [], [], [], []]
    no_letters = re.compile('^[^a-zA-Z]+$')
    gap = True
    for line in lines.split('\n'):
        debug = False
        if debug:
            print('qwer' + '-' * 80)
            print(line)
            print('asdf'+line+'asdf')
            print(div)
            print('gap = {}'.format(gap))
            print(bool(re.match(no_letters, line)))
            print('wert' + '-' * 80)
        if re.match(no_letters, line):
            if not gap:
                div += 1
            gap = True
            continue
        gap = False
        team = -1
        for team_idx, name in enumerate(line.split(',')):
            if name:
                team = team_idx - 1
                if team == len(league[div]):
                    league[div].append([])
                league[div][team].append(name)
    pprint(league, width=120)
    return league


if __name__ == '__main__':
    team_path = '/Users/bcoulter/PycharmProjects/league_admin/website_support/input/2018-1-spring/Spring 2018 Teams_clean.csv'
    import_team_scvl(team_path)






