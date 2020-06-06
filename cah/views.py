import json

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse

from asgiref.sync import async_to_sync
import channels.layers

from .models import BlackCahCard, WhiteCahCard, CahSubmission
from trivia_party.models import Player, Party, Round
from trivia_party.helpers import (party_to_dict,
                                  jumble_answers)
from .cah_logic import (pick_cards, create_new_cah_submission,
                        check_total_submissions, check_player_submissions,
                        calculate_player_score, create_cah_scores)


def cah_party(request, party_id):
    """ Displays the Black Card and the Player's hand for the current party"""
    if request.session.get('player') is None:
        return redirect(f'/join/{party_id}?party_type=cah')
    player = Player.objects.get(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
    if party.status == 0:
        return redirect(f'/start/{party_id}')
    if party.status == 2:
        return redirect(f'/cah/{party_id}/finish')
    party_round = party.rounds.filter(completed=False).first()
    current_round = len(party.rounds.filter(completed=True)) + 1
    if current_round > (int(party.num_rounds) * int(party.num_players)):
        return redirect(f'/cah/{party_id}/finish')
    black_card = party_round.black_card.all().first()
    if black_card.owner == player:
        return redirect(f'/cah/{party_id}/choose')
    if check_player_submissions(party_round, player) == 1:
        return redirect(f'/cah/{party_id}/waiting')
    black_card = party_round.black_card.all().first()
    pick_cards(player)
    player_score = calculate_player_score(player, party)
    current_hand = player.white_cards.filter(in_hand=True)
    cah_scores = create_cah_scores(party)
    # Check player score
    # Get num player submission
    #if player_submissions > 0:
    #    return redirect(f'/cah/{party_id}/waiting')
    return render(request, 'cah_party.html',{
        'party': party_to_dict(party),
        'player': player, 
        'player_score': player_score,
        'party_name': party.party_name,
        'round': party_round,
        'current_round': current_round,
        'black_card': black_card,
        'current_hand': current_hand,
    })


def submit_card(request, party_id):
    if not request.session.get('player'):
        return redirect('/')
    if not request.POST:
        return redirect(f'/cah/{party_id}/party')
    score = 0
    white_cards = []
    player = Player(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
    party_round = Round.objects.get(id=request.POST.get('round_id'))
    if check_player_submissions(party_round, player) == 1:
        return redirect(f'/cah/{party_id}/waiting')
    black_card = BlackCahCard.objects.get(id=request.POST.get('black_card_id'))
    white_card1 = WhiteCahCard.objects.get(id=request.POST.get('white_card1'))
    white_cards.append(white_card1)
    if request.POST.get('white_card2') != '-1':
        white_card2 = WhiteCahCard.objects.get(id=request.POST.get('white_card2'))
        white_cards.append(white_card2)
    if request.POST.get('white_card3') != '-1':
        white_card3 = WhiteCahCard.objects.get(id=request.POST.get('white_card3'))
        white_cards.append(white_card3)
    player_submission = create_new_cah_submission(
        party=party,
        options={
            "white_cards": white_cards,
            "player": player,
            "party_round": party_round,
            "black_card": black_card,
        }
    )
    total_submissions = check_total_submissions(party_round)
    if total_submissions == int(party.num_players) - 1:
        channel_layer = channels.layers.get_channel_layer()
        async_to_sync(channel_layer.group_send)('chat_%s' % party_id, {
                'type': 'chat_message',
                'submission_score': "",
                'message': 'white_cards_complete',
                'player_name': player.player_name,
                })
        return redirect(f'/cah/{party_id}/choose')
    return redirect(f'/cah/{party_id}/waiting')

def finish_screen(request, party_id):
    party = Party.objects.get(party_name=party_id)
    finished_rounds = Round.objects.filter(party=party, completed=True)
    if len(finished_rounds) < (int(party.num_rounds) * int(party.num_players)):
        return redirect(f'/cah/{party_id}/party')
    Party.objects.filter(party_name=party_id).update(status=2)
    game_scores = create_cah_scores(party)
    return render(request, 'cah_finish_screen.html', {
        'party': party, 
        'winners': game_scores.get('winners'), 
        'other_players': game_scores.get('other_players'),
        'ws_protocol': settings.WS_PROTOCOL,
        })


def waiting_screen(request, party_id):
    party = Party.objects.get(party_name=party_id)
    party_round = party.rounds.filter(completed=False).first()
    player = Player.objects.get(id=request.session.get('player'))
    total_submissions = check_total_submissions(party_round)
    if total_submissions < int(party.num_players) - 1:
        return redirect(f'/cah/{party.party_name}/party')
    return render(request, 'cah_waiting_screen.html',{
        'party': party,
        'ws_protocol': settings.WS_PROTOCOL
    })

def choose_screen(request, party_id):
    party = Party.objects.get(party_name=party_id)
    party_round = party.rounds.filter(completed=False).first()
    current_round = len(party.rounds.filter(completed=True)) + 1
    if current_round > (int(party.num_rounds) * int(party.num_players)):
        return redirect(f'/cah/{party_id}/finish')
    if request.session.get('player') is None:
        return redirect(f'/join/{party_id}?party_type=cah')
    player = Player.objects.get(id=request.session.get('player'))
    black_card = party_round.black_card.all().first()
    white_card_submissions = CahSubmission.objects.filter(black_cah_card=black_card).all()
    submissions = []
    for s in white_card_submissions:
        sub = {}
        sub['player'] = s.player.player_name
        cards = []
        for picked_card in s.picked_cards.all().order_by('updated_at'):
            card = {}
            card['card_id'] = picked_card.id
            card['card_text'] = picked_card.card_text
            card['revealed'] = picked_card.revealed
            cards.append(card)
        sub['white_cards'] = cards
        sub['revealed'] = s.revealed
        submissions.append(sub)
    submissions = jumble_answers(submissions)
    
    if black_card.owner != player and check_player_submissions(party_round, player) == 0:
        return redirect(f'/cah/{party_id}/party')
    player_score = calculate_player_score(player, party)
    return render(request, 'choose_screen.html',{
        'party': party,
        'player': player,
        'player_score': player_score,
        'party_round': party_round,
        'current_round': current_round,
        'black_card': black_card,
        'white_card_submissions': submissions,
        'ws_protocol': settings.WS_PROTOCOL
    })

def submit_winner(request, party_id):
    data = request.POST
    party = Party.objects.get(party_name=party_id)
    party_round = party.rounds.filter(id=data.get('round_id'))
    player = Player.objects.get(id=request.session.get('player'))
    black_card = BlackCahCard.objects.filter(id=data.get('black_card_id'))
    winner = Player.objects.get(player_name=data.get('player_name'))
    if black_card.first().owner == player:
        black_card.update(winner=winner)
        party_round.update(completed=True)
        channel_layer = channels.layers.get_channel_layer()
        async_to_sync(channel_layer.group_send)('chat_%s' % party_id, {
                'type': 'chat_message',
                'submission_score': winner.player_name,
                'message': 'cah_round_complete',
                'player_name': player.player_name,
                })
    finished_rounds = Round.objects.filter(party=party, completed=True)
    if len(finished_rounds) < (int(party.num_rounds) * int(party.num_players)):
        redirect(f'/cah/{party.party_name}/finish')
    return redirect(f'/cah/{party.party_name}/waiting?picked={winner.player_name}')

def mark_revealed(request, party_id):
    data = request.POST

    print(data.get('player_name'))
    if data:
        player = Player.objects.get(player_name=data.get('player_name'))
        if data.get('type') == 'submission':
            black_card = BlackCahCard.objects.get(id=data.get('card_id'))
            submission = CahSubmission.objects.filter(
                player=player, black_cah_card=black_card)
            submission.update(revealed=True)
        elif data.get('type') == 'card':
            white_card = WhiteCahCard.objects.filter(id=data.get('card_id'))
            white_card.update(revealed=True)
        return JsonResponse({'status': 200})
    return JsonResponse({'status': 404})
