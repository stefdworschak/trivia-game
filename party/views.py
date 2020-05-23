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

from .models import Party, Player, Round, TriviaQuestion, TriviaSubmission
from .game_modes.trivia import (create_new_trivia_submission,
                                add_trivia_questions,
                                create_trivia_submission_scores)
from .helpers import jumble_answers, calculate_player_score, party_to_dict

import namegenerator

logger = logging.getLogger(__name__)


########################################
############ VIEW FUNCTIONS ############
########################################


def new_party(request):
    """ Shows form to create a new party and generates the party name """
    gen_hash = hashlib.sha256()
    gen_hash.update(str(datetime.now()).encode('utf-8'))
    hex_digest = gen_hash.hexdigest()
    return render(request, 'new.html', 
                  {"hex_digest": namegenerator.gen() + '-' + hex_digest[-4:]})


def join_party(request, party_id):
    """ Shows form to find or create new player and join or create a party """
    data = request.POST
    pass_through = {
        'party_id': party_id,
        'party_type': data.get('party_type'),
        'trivia_category': data.get('trivia_category'),
        'num_players': data.get('num_players'),
        'num_rounds': data.get('num_rounds')
    }
    return render(request, 'join.html', pass_through)


def start_screen(request, party_id):
    """ Shows the start screen until all players have joined """
    party = Party.objects.get(party_name=party_id)
    players = party.players.all()
    #if party.status == 1:
    #    return redirect(f'/party/{party_id}')
    if party.status == 2:
        return redirect(f'/finish/{party_id}')
    return render(request, 'start_screen.html', {
        'party': party })


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
        return redirect(f'/party/{party.party_name}')
    return render(request, 'waiting_screen.html', {
        'party': party,
        'player': player,
    })


def party(request, party_id):
    """ Displays the question and answers for the current party"""
    if request.session.get('player') is None:
        return redirect(f'/join/{party_id}')
    player = Player.objects.get(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
    print(request.session.get('player') is None)
    if party.status == 0:
        return redirect(f'/start/{party_id}')
    if party.status == 2:
        return redirect(f'/finish/{party_id}')
    party_round = party.rounds.filter(completed=False).first()
    current_round = len(party.rounds.filter(completed=True)) + 1
    if current_round > party.num_rounds:
        return redirect('/finish/'+party.party_name)
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
        return redirect(f'/waiting/{party_id}')
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
        return redirect(f'/party/{party_id}')
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
        'party': party, 'winners': winners, 'other_players': other_players })


def find_player(request):
    """ AJAX endpoint to find an existing player """
    keyword = request.POST.get('player_name')
    player = Player.objects.filter(player_name=keyword)
    if player.count() == 0:
        return JsonResponse({'player_exists': False})
    else:
        return JsonResponse({'player_exists': True})


def create_player(request):
    """ AJAX endpoint to create a new player """
    keyword = request.POST.get('player_name')
    try:
        player = Player.objects.create(player_name=keyword, score=0, 
                                       is_admin=False)
        new_player = Player.objects.get(player_name=keyword)
        if not player:
            return JsonResponse({'player_exists': False, 'player': {}})
        else:
            return JsonResponse({'player_exists': True, 
                                 'player': model_to_dict(new_player)})
    except:
        return JsonResponse({'player_exists': False, 'player': {}})


########################################
########## NON-VIEW FUNCTIONS ##########
########################################


def recreate_party(request):
    """ (not a view) creates a copy of the last party's settings with a new
    party name and the same players """ 
    if not request.POST:
        return redirect('/')
    party_id = request.POST.get('party_id')
    party = Party.objects.get(party_name=party_id)
    gen_hash = hashlib.sha256()
    gen_hash.update(str(datetime.now()).encode('utf-8'))
    hex_digest = gen_hash.hexdigest()
    new_party_id = namegenerator.gen() + '-' + hex_digest[-4:]
    p = Party(party_name=new_party_id,
                num_players=party.num_players,
                admin=party.admin,
                num_rounds=party.num_rounds,
                party_type=party.party_type,
                party_subtype=party.party_subtype)
    p.save()
    for player in party.players.all():
        print(player.player_name)
        pl = Player.objects.get(player_name=player.player_name)
        p.players.add(pl)
    add_trivia_questions(p)
    Party.objects.filter(party_name=new_party_id).update(status=1)
    msg="party_recreated"
    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)('chat_%s' % party_id, {
        'type': 'chat_message',
        'submission_score': new_party_id,
        'message': msg,
        'player_name': '',
        })
    return redirect(f'/party/{new_party_id}')


def create_or_join_party(request):
    """ (not a view) Checks if party exists and joins player to party 
    or creates new party """
    #try:
    data = request.POST
    party_id = data.get('party_id')
    player = Player.objects.get(player_name=data.get('player'))
    party = Party.objects.filter(party_name=party_id)
    
    if party.count() == 0:
        p = Party(party_name=party_id,
                    num_players=data.get('num_players'),
                    admin=player,
                    num_rounds=data.get('num_rounds'),
                    party_type=data.get('party_type'),
                    party_subtype=data.get('trivia_category'))
        p.save()
        p.players.add(player)
        add_trivia_questions(p)
        request.session['player'] = player.id
        return redirect(f'/party/{data.get("party_id")}')
    else:
        p = Party.objects.get(party_name=party_id)
        msg = ''
        if len(p.players.all()) < p.num_players:
            p.players.add(player)
            request.session['player'] = player.id
            p = Party.objects.get(party_name=party_id)
            if len(p.players.all()) == p.num_players:
                p_upate = Party.objects.filter(party_name=party_id)
                p_upate.update(status=1)
                msg = 'game_starts'
            channel_layer = channels.layers.get_channel_layer()
            async_to_sync(channel_layer.group_send)('chat_%s' % party_id, {
                'type': 'chat_message',
                'submission_score': None,
                'message': msg,
                'player_name': player.player_name,
                })
            return redirect(f'/start/{data.get("party_id")}')
        elif p.players.filter(id=player.id).exists():
            request.session['player'] = player.id
            return redirect(f'/party/{data.get("party_id")}')
        else:
            return redirect('/?error=party_full')
    #except:
    #    return redirect('/party')



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
        return redirect('/party/%s' % party_id)
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
        return redirect(f'/waiting/{party_id}?submission={int(submission_score)}&correct_answer={trivia_question.correct_answer}')    

    return redirect(f'/waiting/{party_id}')


def create_submission_scores(party_round, party_type):
    """ Create the submission scores for a round for all players """
    if party_type == 'trivia':
        return create_trivia_submission_scores(party_round)
    return {}
