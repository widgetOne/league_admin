from django.shortcuts import render

from django.http import Http404

from league.models import Team

def index(request):
    teams = Team.objects.exclude(name='13451345134')
    return render(request, 'league/index.html', {'teams' : teams})

def team(request, id):
    try:
        team = Team.objects.get(id=id)
    except Item.DoesNotExist:
        raise Http404('This item does not exist')
    return render(request, 'league/team.html',
                  {'team' : team})
