import random

from django.db.models import Sum, Count
from django.forms.models import model_to_dict

from .models import TriviaSubmission


def party_to_dict(m):
    _party = {}
    _p = model_to_dict(m)
    for key, val in _p.items():
        if key =='players':
            _party['players'] = [
                model_to_dict(player)
                for player in val
            ]
        else:
            _party[key] = val
    return _party


def jumble_answers(incorrect, correct):
    new_answers = []
    incorrect.append(correct)
    for i in range(len(incorrect)):
        choice = random.choice(incorrect)
        incorrect.remove(choice)
        new_answers.append(choice)
    return new_answers


def calculate_player_score(player, party):
    rounds = party.rounds.filter(completed=True).all()
    trivia_submissions = TriviaSubmission.objects.filter(
        party_round__in=rounds,
        player=player)
    return trivia_submissions.aggregate(Sum('score'), Count('score'))
