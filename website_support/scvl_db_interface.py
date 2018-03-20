import bunch
import records
import os
from pprint import pprint
import import_team_csv


def get_max_id(table, id_name):
    with records.Database(os.environ['SCVL_DB_AUTH']) as conn:
        sql = 'SELECT MAX({}) as max FROM {};'.format(id_name, table)
        rows = conn.query(sql).as_dict()
    return rows[0]['max']

def get_current_season_indexes():
    # 2018-01-20: numbers from Spring 2018
    raise Exception('dont rerun this until all hardcoded indexes have been updated')
    return bunch.Bunch({'season': 54, 'div': [134, 135, 136, 137, 138]})

def tag(div_idx, team_idx):
    return '{}-{}'.format(div_idx, team_idx)

def add_teams_to_db(league):
    db_idx = get_current_season_indexes()
    team_id = get_max_id('teams', 'team_id') + 1
    team_cypher = {}
    with records.Database(os.environ['SCVL_DB_AUTH']) as conn:
        delete_sql = 'DELETE FROM teams WHERE season_id = {};'.format(db_idx.season)
        with conn.transaction() as t:
            conn.query(delete_sql)

        for div_idx, div in enumerate(league):
            for team_idx, team in enumerate(div):
                    sql = '''INSERT INTO `teams` (`team_id`, `team_name`, `team_num`, `div_id`, `season_id`)
                             VALUES ({}, '', {}, {}, {});'''.format(team_id, team_idx + 1,
                                                                    db_idx.div[div_idx], db_idx.season)
                    conn.query(sql)
                    team_cypher[tag(div_idx, team_idx)] = team_id
                    team_id += 1
    pprint(team_cypher)
    return team_cypher

#' (PT)'
def add_players_to_db(league, team_cypher):
    db_idx = get_current_season_indexes()
    player_id = get_max_id('players', 'player_id') + 1
    with records.Database(os.environ['SCVL_DB_AUTH']) as conn:
        delete_sql = 'DELETE FROM players WHERE season_id = {};'.format(db_idx.season)
        with conn.transaction() as t:
            conn.query(delete_sql)
        for div_idx, div in enumerate(league):
            for team_idx, team in enumerate(div):
                for p_idx, name in enumerate(team):
                    team_id = team_cypher[tag(div_idx, team_idx)]
                    captain = 0  # We don't know until the teams meet. Can't be filled here
                    part_time_tag = ' (PT)'
                    if part_time_tag in name:
                        part_time = 1
                    else:
                        part_time = 0
                    name = name.replace(part_time_tag, '')
                    sql = '''INSERT INTO `players` 
                                (`player_id`, `team_id`, `season_id`, `player_name`, `captain`, `part_time`)
                            VALUES ({}, {}, {}, '{}', {}, {}); 
                            '''.format(player_id, team_id, db_idx.season, name, captain, part_time)
                    conn.query(sql)
                    player_id += 1


def import_teams_to_db():
    team_path = '/Users/bcoulter/PycharmProjects/league_admin/website_support/input/2018-1-spring/SCVL - Information  League Status - Spring 2018 - Website Import (1).csv'
    league = import_team_csv.import_team_scvl(team_path)
    team_cypher = add_teams_to_db(league)
    add_players_to_db(league, team_cypher)


if __name__ == '__main__':
    import_teams_to_db()