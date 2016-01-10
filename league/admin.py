from django.contrib import admin

from .models import Team, League, Game

class TeamAdmin(admin.ModelAdmin):
    list_display = ['division', 'number', 'name']

admin.site.register(Team, TeamAdmin)

class LeagueAdmin(admin.ModelAdmin):
    list_display = ['divisions', 'courts']

admin.site.register(League, LeagueAdmin)

class GameAdmin(admin.ModelAdmin):
    list_display = ['day', 'court', 'time', 'team1', 'team2', 'ref']

admin.site.register(Game, GameAdmin)
