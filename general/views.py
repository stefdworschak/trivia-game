from datetime import datetime

from asgiref.sync import async_to_sync
import channels.layers
from django.conf import settings
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.shortcuts import render, redirect
import hashlib
import namegenerator

from trivia_party.models import Player, Party
from .helpers import add_party_content


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
    #    return redirect(f'/trivia/{party_id}')
    if party.status == 2:
        return redirect(f'/finish/{party_id}')
    return render(request, 'start_screen.html', {
        'party': party,
        'ws_protocol': settings.WS_PROTOCOL,
        })
    

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
        add_party_content(p)
        request.session['player'] = player.id
        return redirect(f'/trivia/{data.get("party_id")}/party')
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
            return redirect(f'/trivia/{data.get("party_id")}/party')
        else:
            return redirect('/?error=party_full')
    #except:
    #    return redirect('/party')


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
    add_party_content(p)
    Party.objects.filter(party_name=new_party_id).update(status=1)
    msg="party_recreated"
    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)('chat_%s' % party_id, {
        'type': 'chat_message',
        'submission_score': new_party_id,
        'message': msg,
        'player_name': '',
        })
    return redirect(f'/start/{new_party_id}')