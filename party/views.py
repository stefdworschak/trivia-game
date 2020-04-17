import hashlib
from datetime import datetime

from django.shortcuts import render
from django.http import JsonResponse

from .models import Party, Player

import namegenerator


def new_party(request):
    gen_hash = hashlib.sha256()
    gen_hash.update(str(datetime.now()).encode('utf-8'))
    hex_digest = gen_hash.hexdigest()
    return render(request, 'new.html', 
                  {"hex_digest": namegenerator.gen() + '-' + hex_digest[-4:]})
            

def create_party(request):
    data = request.POST
    print(data.get('party_type'))
    party = {}
    
    return render(request, 'join.html', {'party': party})

def join_party(request, party_id):
    return render(request, 'join.html', {'party_id': party_id})

def find_player(request):
    keyword = request.POST.get('player_name')
    player = Player.objects.filter(player_name=keyword)
    return JsonResponse({'player_exists': True})
    #if player.player_name:
    #    return JsonResponse({'player_exists': True})
    #else:
    #    return JsonResponse({'player_exists': False
    #    })