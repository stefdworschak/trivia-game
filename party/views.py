import ast
import json
import hashlib
from datetime import datetime
import random
import requests

from asgiref.sync import async_to_sync
import channels.layers

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.core import serializers

from .models import Party, Player, Round, TriviaQuestion, TriviaSubmission

import namegenerator


def new_party(request):
    gen_hash = hashlib.sha256()
    gen_hash.update(str(datetime.now()).encode('utf-8'))
    hex_digest = gen_hash.hexdigest()
    return render(request, 'new.html', 
                  {"hex_digest": namegenerator.gen() + '-' + hex_digest[-4:]})
            

def create_join_party(request):
    #try:
    data = request.POST
    player = Player.objects.get(player_name=data.get('player'))
    party = Party.objects.filter(party_name=data.get('party_id'))
    if party.count() == 0:
        print(data.get('party_type'))
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
        #return JsonResponse({'party_exists': False, 'data': data, 'party': party_to_dict(p)})
        return redirect(f'/party/{data.get("party_id")}')
    else:
        p = Party.objects.get(party_name=data.get('party_id'))
        if len(p.players.all()) < p.num_players:
            p.players.add(player)
            request.session['player'] = player.id
            #return JsonResponse({'party_exists': True, 'data': data, 'party': party_to_dict(p)})
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
    player = Player(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
    trivia_round = party.rounds.filter(completed=False).first()
    print(trivia_round.id)
    print(trivia_round.completed)
    current_round = len(party.rounds.filter(completed=True)) + 1
    trivia_question = trivia_round.question.all().first()
    answers = ast.literal_eval(trivia_question.question_answers)
    return render(request, 'party.html', {
                                            'party': party_to_dict(party), 
                                            'round': trivia_round, 
                                            'question': trivia_question,
                                            'answers': answers,
                                            'current_round': current_round,
                                            'player': player})


def submit_question(request, party_id):
    if not request.session.get('player'):
        return redirect('/')
    score = 0
    player = Player(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
    trivia_round = Round.objects.get(id=request.POST.get('round_id'))
    trivia_question = TriviaQuestion.objects.get(id=request.POST.get('question_id'))
    total_submissions = TriviaSubmission.objects.filter(
        trivia_round=trivia_round)
    player_submission = TriviaSubmission.objects.filter(
        trivia_round=trivia_round, player=player)
    if len(player_submission) == 0:
        if trivia_question.correct_answer == request.POST.get('answer'):
            score = 1
        trivia_submission = TriviaSubmission(
            player=player,
            trivia_round=trivia_round,
            trivia_question=trivia_question,
            submitted_answer=request.POST.get('answer'),
            score=score)
        trivia_submission.save()
    if len(total_submissions) == party.num_players:
        Round.objects.filter(id=request.POST.get('round_id')).update(completed=True)
        channel_layer = channels.layers.get_channel_layer()
        async_to_sync(channel_layer.group_send)('chat_%s' % party_id, {
                'type': 'chat_message',
                'message': 'round_complete'})
        return redirect('/party/%s' % party_id)    

    return render(request, 'question.html', {
        'player': player,
        'party_name': party.party_name,
    })

def join_party(request, party_id):
    data = request.POST
    print(data)
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
    rounds = party.num_rounds * 2
    if party.party_subtype != 'any':
        category = f'?category={party.party_subtype}'
    
    trivia_url = f'https://opentdb.com/api.php?amount={rounds}&type=multiple{category}'
    res = requests.get(trivia_url)
    if res.status_code == 200:
        questions = res.json()['results']
    for question in questions:
        print(1)
        trivia_round = Round(party=party)
        trivia_round.save()
        trivia_question = TriviaQuestion(
            question_text=question.get('question'),
            question_answers=jumble_answers(
                question.get('incorrect_answers'),
                question.get('correct_answer')),
            correct_answer=question.get('correct_answer'),
            category=question.get('category'),
            question_type=question.get('type'),
            difficulty=question.get('difficulty'),
            trivia_round=trivia_round
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
