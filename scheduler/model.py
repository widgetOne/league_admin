


class Game(object):
    def __init__(self):
        self.team1 = -1
        self.team2 = -1
        self.ref = -1
        self.div = -1

class Day(object):
    def __init__(self):
        from copy import deepcopy
        court = [Game() for _ in range(4)]
        self.courts = [deepcopy(court) for _ in range(5)]

    def fitness(self, divisions):
        fitness = 0
        for court in self.courts:
            for game in court:
                team1 = divisions[game.div].teams[game.team1]
                team2 = divisions[game.div].teams[game.team2]
                old_count1 = team1.times_team_played[team2.team_idx]
                old_count2 = team2.times_team_played[team1.team_idx]
                fitness -= (old_count1 + old_count2) * 2 + 2
        return fitness

class Division(object):
    def __init__(self, team_count):
        self.teams = []
        self.team_count = team_count
        for team_idx in range(team_count):
            self.teams.append(Team(team_idx, team_count))

    def teams_w_least_ref(self):
        min_plays = min([team.refs for team in self.teams])
        return [team_num for team_num, team in enumerate(self.teams)
                if team.refs == min_plays]

    def teams_w_most_play(self):
        max_plays = max([team.games for team in self.teams])
        return [team_num for team_num, team in enumerate(self.teams)
                if team.games == max_plays]

    def teams_w_least_play(self):
        min_plays = min((team.games for team in self.teams))
        return [team_num for team_num, team in enumerate(self.teams)
                if team.games == min_plays]

    def fitness(self):
        fitness = 0
        for team in self.teams:
            pass

class Team(object):
    def __init__(self, team_idx, teams_in_division):
        time_slots = 4
        self.games = 0
        self.refs = 0
        self.team_idx = team_idx
        self.days_comma_games = []
        self.time_slot_count = [0 for _ in range(time_slots)]
        self.times_team_played = [0 for _ in range(teams_in_division)]
        self.times_team_played[team_idx] = 1000

    def add_game(self, court, time, team1, team2, ref):
        self.games.append(Game(court, team1, team2, ref))

    def teams_least_played(self):
        min_plays = min((played for played in self.times_team_played))
        return [team_idx for team_idx, played in enumerate(self.times_team_played)
                if played == min_plays]
