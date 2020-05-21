import ast
import json
import hashlib
import os
from datetime import datetime
import random
import requests

from asgiref.sync import async_to_sync
import channels.layers

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.core import serializers
from django.db.models import Sum, Count

from .models import Party, Player, Round, TriviaQuestion, TriviaSubmission
from .game_modes.trivia import create_new_trivia_submission

import namegenerator


def new_party(request):
    gen_hash = hashlib.sha256()
    gen_hash.update(str(datetime.now()).encode('utf-8'))
    hex_digest = gen_hash.hexdigest()
    return render(request, 'new.html', 
                  {"hex_digest": namegenerator.gen() + '-' + hex_digest[-4:]})
            

def create_or_join_party(request):
    """ Checks if party exists and joins player to party or creates new party """
    #try:
    data = request.POST
    player = Player.objects.get(player_name=data.get('player'))
    party = Party.objects.filter(party_name=data.get('party_id'))
    if party.count() == 0:
        p = Party(party_name=data.get('party_id'),
                    num_players=data.get('num_players'),
                    admin=player,
                    num_rounds=data.get('num_rounds'),
                    party_type=data.get('party_type'),
                    party_subtype=data.get('trivia_category'))
        p.save()
        p.players.add(player)
        add_questions(p)
        request.session['player'] = player.id
        return redirect(f'/party/{data.get("party_id")}')
    else:
        p = Party.objects.get(party_name=data.get('party_id'))
        if len(p.players.all()) < p.num_players:
            p.players.add(player)
            request.session['player'] = player.id
            return redirect(f'/party/{data.get("party_id")}')
        elif p.players.filter(id=player.id).exists():
            request.session['player'] = player.id
            return redirect(f'/party/{data.get("party_id")}')
        else:
            return redirect('/?error=party_full')
    #except:
    #    return redirect('/party')

def party(request, party_id):
    if not request.session.get('player'):
        return redirect(f'/join/{party_id}')
    player = Player.objects.get(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
    party_round = party.rounds.filter(completed=False).first()
    current_round = len(party.rounds.filter(completed=True)) + 1
    trivia_question = party_round.question.all().first()
    answers = ast.literal_eval(trivia_question.question_answers)
    player_score = calculate_player_score(player, party)
    return render(request, 'party.html', {
                                            'party': party_to_dict(party), 
                                            'party_name': party.party_name,
                                            'round': party_round, 
                                            'question': trivia_question,
                                            'answers': answers,
                                            'current_round': current_round,
                                            'player': player,
                                            'player_score': player_score})

def create_submission(party_type, options={}):
    submission = False
    if party_type == 'trivia':
        submission = create_new_trivia_submission(
            party_round=options.get('party_round'), 
            player=options.get('player'), 
            question_id=options.get('question_id'), 
            answer=options.get('answer'))
    return submission

def check_total_submissions(party_type, party_round):
    submissions = 0
    if party_type == 'trivia':
        return TriviaSubmission.objects.filter(
            party_round=party_round)
    return submissions



def submit_question(request, party_id):
    if not request.session.get('player'):
        return redirect('/')
    score = 0
    player = Player(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
    party_round = Round.objects.get(id=request.POST.get('round_id'))
    trivia_question = TriviaQuestion.objects.get(id=request.POST.get('question_id'))
    total_submissions = check_total_submissions(party.party_type, party_round)
    submission_score = create_submission(
        party_type=party.party_type, 
        options={
            'party_round': party_round,
            'player': player,
            'question_id': request.POST.get('round_id'),
            'answer': request.POST.get('answer'),
        })
    if len(total_submissions) == party.num_players:
        Round.objects.filter(id=request.POST.get('round_id')).update(completed=True)
        channel_layer = channels.layers.get_channel_layer()
        async_to_sync(channel_layer.group_send)('chat_%s' % party_id, {
                'type': 'chat_message',
                'submission_score': submission_score,
                'message': 'round_complete'})
        return redirect('/party/%s' % party_id)    

    return render(request, 'question.html', {
        'player': player,
        'party_name': party.party_name,
    })

def join_party(request, party_id):
    data = request.POST
    pass_through = {
        'party_id': party_id,
        'party_type': data.get('party_type'),
        'trivia_category': data.get('trivia_category'),
        'num_players': data.get('num_players'),
        'num_rounds': data.get('num_rounds')
    }
    return render(request, 'join.html', pass_through)


def find_player(request):
    keyword = request.POST.get('player_name')
    player = Player.objects.filter(player_name=keyword)
    if player.count() == 0:
        return JsonResponse({'player_exists': False})
    else:
        return JsonResponse({'player_exists': True})


def create_player(request):
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

def add_questions(party):
    category = ''
    rounds = int(party.num_rounds) * 2
    print("QUESTIONS: ", rounds)
    if party.party_subtype != 'any':
        category = f'?category={party.party_subtype}'
    
    trivia_url = f'https://opentdb.com/api.php?amount={rounds}&type=multiple{category}'
    res = requests.get(trivia_url)
    if res.status_code == 200:
        questions = res.json()['results']
    print("QUESTIONS: ", len(questions))
    for question in questions:
        party_round = Round(party=party, num_submissions=0)
        party_round.save()
        trivia_question = TriviaQuestion(
            question_text=question.get('question'),
            question_answers=jumble_answers(
                question.get('incorrect_answers'),
                question.get('correct_answer')),
            correct_answer=question.get('correct_answer'),
            category=question.get('category'),
            question_type=question.get('type'),
            difficulty=question.get('difficulty'),
            party_round=party_round
        )
        trivia_question.save()
    return

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
    print(rounds)
    trivia_submissions = TriviaSubmission.objects.filter(
        party_round__in=rounds,
        player=player
    )
    return trivia_submissions.aggregate(Sum('score'), Count('score'))