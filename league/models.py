from django.db import models


class Game(models.Model):
    day = models.IntegerField(default=0)
    court = models.IntegerField(default=0)
    time = models.IntegerField(default=0)
    team1 = models.IntegerField(default=0)
    team2 = models.IntegerField(default=0)
    ref = models.IntegerField(default=0)

class League(models.Model):
    courts = models.IntegerField(default=5)
    divisions = models.IntegerField(default=4)

class Team(models.Model):
    number = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    division = models.IntegerField(default='') # 1 = rec, 4 = power
    members = models.TextField(default='')
    member_count = models.IntegerField(default=0)

    def __repr__(self):
        return str(self.title)