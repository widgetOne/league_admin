from pulp import LpProblem, LpVariable, LpMinimize, LpStatus, value
import itertools
from datetime import datetime

# Parameters
num_teams = 10  # teams per division
num_divisions = 3
num_days = 6
num_hours_per_day = 5
num_courts = 4

# Create an LP problem
model = LpProblem("Volleyball_League_Scheduling", LpMinimize)

# Variables
# Match variables: match[division, team1, team2, day, hour, court] = 1 if match scheduled, else 0
match = LpVariable.dicts("match", (range(num_divisions), range(num_teams), range(num_teams),
                                   range(num_days), range(num_hours_per_day), range(num_courts)),
                         cat="Binary")

print('Constraint 1 - Each team can play only once per hour per day per court.', datetime.now())
# Constraints
for div in range(num_divisions):
    for team in range(num_teams):
        for day in range(num_days):
            for hour in range(num_hours_per_day):
                model += (sum(match[div][team][opp][day][hour][court]
                              for opp in range(num_teams) if opp != team
                              for court in range(num_courts)) <= 1,
                          f"One_match_per_hour_team_{team}_div_{div}_day_{day}_hour_{hour}")

print('Constraint 2 - Each court can host only one match per hour.', datetime.now())
# 2. Each court can host only one match per hour.
for day in range(num_days):
    for hour in range(num_hours_per_day):
        for court in range(num_courts):
            model += (sum(match[div][team1][team2][day][hour][court]
                          for div in range(num_divisions)
                          for team1 in range(num_teams)
                          for team2 in range(team1+1, num_teams)) <= 1,
                      f"One_match_per_court_day_{day}_hour_{hour}_court_{court}")
print('asdf 33', datetime.now())


# 2. Each court can host only one match per hour.
for day in range(num_days):
    for div in range(num_divisions):
        for team1 in range(num_teams):
            for op in range(num_teams):
                model += (sum(match[div][team1][team2][day][hour][court]
                      for court in range(num_courts):
                      for hour in range(num_hours_per_day):
                          for team2 in range(team1+1, num_teams)) <= 1,
                      f"One_match_per_court_day_{day}_hour_{hour}_court_{court}")
print('asdf 44', datetime.now())

asdf = '''

# 3. Ensure all unique team pairs within a division have at least one match scheduled across the days.
for div in range(num_divisions):
    for team1, team2 in itertools.combinations(range(num_teams), 2):
        model += (sum(match[div][team1][team2][day][hour][court]
                      for day in range(num_days)
                      for hour in range(num_hours_per_day)
                      for court in range(num_courts)) >= 1,
                  f"Unique_match_team_{team1}_{team2}_div_{div}")
print('asdf 44', datetime.now())

# Objective: Minimize the total number of scheduled matches (or optimize any other objective, e.g., fairness)
model += sum(match[div][team1][team2][day][hour][court]
             for div in range(num_divisions)
             for team1 in range(num_teams)
             for team2 in range(team1+1, num_teams)
             for day in range(num_days)
             for hour in range(num_hours_per_day)
             for court in range(num_courts)), "Total_Matches"
print('asdf 55', datetime.now())
'''


# Solve the problem
model.solve()

print('asdf 66', datetime.now())

print(model.status)
print(LpStatus[model.status])
# Output the schedule
if LpStatus[model.status] == "Optimal":
    schedule = []
    for div in range(num_divisions):
        for team1 in range(num_teams):
            for team2 in range(num_teams):
                if team1 < team2:
                    for day in range(num_days):
                        for hour in range(num_hours_per_day):
                            for court in range(num_courts):
                                if value(match[div][team1][team2][day][hour][court]) == 1:
                                    schedule.append((div, team1, team2, day, hour, court))
    for game in schedule:
        div, team1, team2, day, hour, court = game
        print(f"Division {div + 1} - Day {day + 1} - Hour {hour + 1} - Court {court + 1} - Team {team1 + 1} vs Team {team2 + 1}")
else:
    print("No optimal solution found.")
    

if __name__ == '__main__':
    pass
