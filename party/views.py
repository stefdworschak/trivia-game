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
from .game_modes.trivia import create_new_trivia_submission

import namegenerator

logger = logging.getLogger(__name__)


def new_party(request):
    gen_hash = hashlib.sha256()
    gen_hash.update(str(datetime.now()).encode('utf-8'))
    hex_digest = gen_hash.hexdigest()
    return render(request, 'new.html', 
                  {"hex_digest": namegenerator.gen() + '-' + hex_digest[-4:]})

def correct_submission(request, party_id):
    return render(request, 'correct_display.html', {'party_name': party_id})

def wrong_submission(request, party_id):
    return render(request, 'wrong_display.html', {'party_name': party_id})

def waiting_screen(request, party_id):
    party = Party.objects.get(party_name=party_id)
    player = Player.objects.get(id=request.session.get('player'))
    return render(request, 'waiting_screen.html', {
        'party': party,
        'player': player,
    })

def start_screen(request, party_id):
    party = Party.objects.get(party_name=party_id)
    players = party.players.all()
    #if party.status == 1:
    #    return redirect(f'/party/{party_id}')
    if party.status == 2:
        return redirect(f'/finish/{party_id}')
    return render(request, 'start_screen.html', {
        'party': party })


def finish_screen(request, party_id):
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

def recreate_party(request):
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
    add_questions(p)
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
    """ Checks if party exists and joins player to party or creates new party """
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
        add_questions(p)
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

def party(request, party_id):
    if not request.session.get('player'):
        return redirect(f'/join/{party_id}')
    player = Player.objects.get(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
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
        party=party, 
        player=player)
    print("ROUNDS", current_round - 1)
    print("SUBMISSIONS", player_submissions)
    if current_round == player_submissions:
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

def create_submission(party_type, options={}):
    submission = 0
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

def check_party_player_submissions(party, player):
    submissions = 0
    if party.party_type == 'trivia':
        rounds = party.rounds.filter().all()
        trivia_submissions = TriviaSubmission.objects.filter(
            party_round__in=rounds,
            player=player
        )
        return len(trivia_submissions)
    return submissions


def submit_question(request, party_id):
    print("REDIS URL")
    print(os.environ.get('REDIS_URL'))
    if not request.session.get('player'):
        return redirect('/')
    if not request.POST:
        return redirect('/party/%s' % party_id)
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

    logger.debug("TOTAL SUBMISSIONS", len(total_submissions))
    logger.debug("TOTAL SUBMISSIONS", party.num_players)
    if len(total_submissions) == party.num_players:
        Round.objects.filter(id=request.POST.get('round_id')).update(completed=True)
        submission_scores = create_submission_scores(party_round)
        channel_layer = channels.layers.get_channel_layer()
        async_to_sync(channel_layer.group_send)('chat_%s' % party_id, {
                'type': 'chat_message',
                'submission_score': json.dumps(submission_scores),
                'message': 'round_complete',
                'player_name': player.player_name,
                })
        return redirect(f'/waiting/{party_id}?submission={int(submission_score)}&correct_answer={trivia_question.correct_answer}')    

    return redirect(f'/waiting/{party_id}')


def create_submission_scores(party_round):
    submission_scores = {}
    submissions = {}
    trivia_submissions = party_round.submissions.all()
    trivia_question = TriviaQuestion.objects.get(party_round=party_round)
    submission_scores['correct_answer'] = trivia_question.correct_answer
    for submission in trivia_submissions:
        player_name = submission.player.player_name
        score = submission.score
        submissions[player_name] = score
    submission_scores['submissions'] = submissions
    return submission_scores



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

def add_questions(party, remove_duplicates=True):
    num_count = 0
    category = ''
    rounds = int(party.num_rounds) * 4
    if party.party_subtype != 'any':
        category = f'&category={party.party_subtype}'
    trivia_url = f'https://opentdb.com/api.php?amount={rounds}&type=multiple{category}'
    res = requests.get(trivia_url)
    if res.status_code == 200:
        questions = res.json()['results']
    for question in questions:
        if num_count > int(party.num_rounds):
            print("COUNT", str(num_count))
            return
        # TODO: Check that this is working once there is more data
        two_weeks_ago = timezone.now() - timedelta(days=14)
        duplicate_questions = len(TriviaQuestion.objects.filter(
            question_text=question.get('question'),
            created_at__gt=two_weeks_ago))
        if duplicate_questions > 0 and remove_duplicates:
            continue
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
        num_count += 1
    
    if num_count < int(party.num_rounds):
        add_questions(party, remove_duplicates=False)
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
    trivia_submissions = TriviaSubmission.objects.filter(
        party_round__in=rounds,
        player=player
    )
    return trivia_submissions.aggregate(Sum('score'), Count('score'))