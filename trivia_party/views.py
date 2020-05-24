import ast
import json
import hashlib
import logging
from operator import itemgetter
import os
from datetime import datetime, timedelta
import random
import requests

from asgiref.sync import async_to_sync
import channels.layers

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.core import serializers
from django.db.models import Sum, Count
from django.utils import timezone
from django.conf import settings

from .models import Party, Player, Round, TriviaQuestion, TriviaSubmission
from .trivia import (create_new_trivia_submission,
                                add_trivia_questions,
                                create_trivia_submission_scores)
from .helpers import jumble_answers, calculate_player_score, party_to_dict
from general.helpers import add_party_content

import namegenerator

logger = logging.getLogger(__name__)


########################################
############ VIEW FUNCTIONS ############
########################################
def waiting_screen(request, party_id):
    """ Shows the waiting screen when waiting for all players to submit their
    answers. Also shows correct or wrong answer screen. """
    party = Party.objects.get(party_name=party_id)
    player = Player.objects.get(id=request.session.get('player'))
    party_round = party.rounds.filter(completed=False).first()
    total_submissions = check_total_submissions(party.party_type, party_round)
    print("WAITING SCREEN")
    print("TOTAL SUBMISSIONS", total_submissions)
    print("NUM PLAYERS", party.num_players)
    if total_submissions == party.num_players:
        return redirect(f'/trivia/{party.party_name}/party')
    return render(request, 'waiting_screen.html', {
        'party': party,
        'player': player,
        'ws_protocol': settings.WS_PROTOCOL,
        })


def trivia_party(request, party_id):
    """ Displays the question and answers for the current party"""
    if request.session.get('player') is None:
        return redirect(f'/join/{party_id}')
    player = Player.objects.get(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
    print(request.session.get('player') is None)
    if party.status == 0:
        return redirect(f'/start/{party_id}')
    if party.status == 2:
        return redirect(f'/trivia/{party_id}/finish')
    party_round = party.rounds.filter(completed=False).first()
    current_round = len(party.rounds.filter(completed=True)) + 1
    if current_round > party.num_rounds:
        return redirect(f'/trivia/{party_id}/finish')
    trivia_question = party_round.question.all().first()
    answers = ast.literal_eval(trivia_question.question_answers)
    player_score = calculate_player_score(player, party)
    player_submissions = check_party_player_submissions( 
        party_type=party.party_type,
        party_round=party_round, 
        player=player)
    print("ROUNDS", current_round)
    print("SUBMISSIONS", player_submissions)
    if player_submissions > 0:
        return redirect(f'/trivia/{party_id}/waiting')
    return render(request, 'party.html', {
                                            'party': party_to_dict(party), 
                                            'party_name': party.party_name,
                                            'round': party_round, 
                                            'question': trivia_question,
                                            'answers': answers,
                                            'current_round': current_round,
                                            'player': player,
                                            'player_score': player_score})
                            

def finish_screen(request, party_id):
    """ Shows the final scores, winners and ranking """
    party = Party.objects.get(party_name=party_id)
    finished_rounds = Round.objects.filter(party=party, completed=True)
    if len(finished_rounds) < party.num_rounds:
        return redirect(f'/trivia/{party_id}/party')
    Party.objects.filter(party_name=party_id).update(status=2)
    players = party.players.all()
    player_scores = []
    for player in players:
        score = {}
        score['player_name'] = player.player_name
        score['score'] = calculate_player_score(player, party).get('score__sum')
        player_scores.append(score)
    player_scores = sorted(player_scores, key=itemgetter('score'), reverse=True)
    max_score = player_scores[0].get('score')
    winners = []
    other_players = []
    for s in player_scores:
        if s.get('score') == max_score:
            winners.append(s)
        else:
            other_players.append(s)

    return render(request, 'finish_screen.html', {
        'party': party, 
        'winners': winners, 
        'other_players': other_players,
        'ws_protocol': settings.WS_PROTOCOL,
        })


########################################
########## NON-VIEW FUNCTIONS ##########
########################################
def create_submission(party_type, options={}):
    """ (non-view) Creates a new player submission based on the game type """
    submission = 0
    if party_type == 'trivia':
        submission = create_new_trivia_submission(
            party_round=options.get('party_round'), 
            player=options.get('player'), 
            question_id=options.get('question_id'), 
            answer=options.get('answer'))
    return submission


def check_total_submissions(party_type, party_round):
    """ Get the number of total submissions based on the game type """
    submissions = 0
    if party_type == 'trivia':
        trivia_submissions = TriviaSubmission.objects.filter(
            party_round=party_round)
        return len(trivia_submissions)
    return submissions


def check_party_player_submissions(party_type, party_round, player):
    """ Get the number of submissions for a player based on the game type """
    submissions = 0
    if party_type == 'trivia':
        return len(TriviaSubmission.objects.filter(
            party_round=party_round,
            player=player
        ))
    return submissions


def submit_question(request, party_id):
    """ (non-view) Create a new submission for a question for a player """
    if not request.session.get('player'):
        return redirect('/')
    if not request.POST:
        return redirect(f'/trivia/{party_id}/party')
    score = 0
    player = Player(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
    party_round = Round.objects.get(id=request.POST.get('round_id'))
    trivia_question = TriviaQuestion.objects.get(id=request.POST.get('question_id'))
    submission_score = create_submission(
        party_type=party.party_type, 
        options={
            'party_round': party_round,
            'player': player,
            'question_id': request.POST.get('round_id'),
            'answer': request.POST.get('answer'),
        })
    total_submissions = check_total_submissions(party.party_type, party_round)
    if total_submissions is None:
        print("TOTAL SUBMISSIONS NONE")
    else:
        print("TOTAL SUBMISSIONS", str(total_submissions))
    print("NUM PLAYERS", str(party.num_players))
    if total_submissions == party.num_players:
        Round.objects.filter(id=request.POST.get('round_id')).update(completed=True)
        submission_scores = create_submission_scores(party_round, party.party_type)
        channel_layer = channels.layers.get_channel_layer()
        async_to_sync(channel_layer.group_send)('chat_%s' % party_id, {
                'type': 'chat_message',
                'submission_score': json.dumps(submission_scores),
                'message': 'round_complete',
                'player_name': player.player_name,
                })
        return redirect(f'/trivia/{party_id}/waiting?submission={int(submission_score)}&correct_answer={trivia_question.correct_answer}')    

    return redirect(f'/trivia/{party_id}/waiting')


def create_submission_scores(party_round, party_type):
    """ Create the submission scores for a round for all players """
    if party_type == 'trivia':
        return create_trivia_submission_scores(party_round)
    return {}
