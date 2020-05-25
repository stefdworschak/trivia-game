from django.shortcuts import render, redirect

from trivia_party.models import Player, Party
from trivia_party.helpers import calculate_player_score, party_to_dict


def cah_party(request, party_id):
    """ Displays the Black Card and the Player's hand for the current party"""
    if request.session.get('player') is None:
        return redirect(f'/join/{party_id}')
    player = Player.objects.get(id=request.session.get('player'))
    party = Party.objects.get(party_name=party_id)
    print(request.session.get('player') is None)
    if party.status == 0:
        return redirect(f'/start/{party_id}')
    if party.status == 2:
        return redirect(f'/cah/{party_id}/finish')
    party_round = party.rounds.filter(completed=False).first()
    current_round = len(party.rounds.filter(completed=True)) + 1
    if current_round > party.num_rounds:
        return redirect(f'/cah/{party_id}/finish')
    black_card = party_round.black_card.all().first()
    # Check player score
    # Get num player submission
    #if player_submissions > 0:
    #    return redirect(f'/cah/{party_id}/waiting')
    return render(request, 'cah_party.html',{
        'party': party_to_dict(party),
        'player': player, 
        'party_name': party.party_name,
        'round': party_round,
        'current_round': current_round,
        'black_card': black_card
    })


def finish_screen(request):
    return render(request, 'cah_finish_screen.html')


def waiting_screen(request):
    return render(request, 'cah_waiting_screen.html')