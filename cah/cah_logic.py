import json
from operator import itemgetter
import random

from trivia_party.models import Player, Round
from .models import WhiteCahCard, BlackCahCard, CahSubmission

FILEPATH = 'cah/data/cah_packs.json'


def load_cards_from_file(party):
    black_cards = []
    white_cards = []
    with open(FILEPATH, 'r') as f:
        all_packs = json.load(f)

    packs = party.party_subtype.split(',')
    for pack in all_packs.get('pack_contents'):
        black_cards += pack.get('black', [])
        white_cards += pack.get('white', [])
    return black_cards, white_cards


def create_new_deck(party):
    black_cards, white_cards = load_cards_from_file(party)
    # Choose the black cards
    num_white_cards = 0
    for i in range(int(party.num_rounds) * int(party.num_players)):
        black_card = random.choice(black_cards)
        num_white_cards += (black_card.get('pick') * int(party.num_players))
        party_round = Round(party=party, num_submissions=0)
        party_round.save()
        black_cah_card = BlackCahCard(
            card_text=black_card.get('content'),
            pick=black_card.get('pick'),
            draw=black_card.get('draw'),
            party_round=party_round,
        )
        black_cah_card.save()

    for j in range(num_white_cards + 20):
        white_card = random.choice(white_cards)
        white_cah_card = WhiteCahCard(
            card_text=white_card,
            party=party,
        )
        white_cah_card.save()
    return

def pick_cards(player):
    num_cards_in_hand = len(player.white_cards.filter(in_hand=True))
    if num_cards_in_hand < 7:
        print(f"{player.player_name} needs {7 - num_cards_in_hand} more cards.")
        white_cards = WhiteCahCard.objects.filter(dealt=False)
        white_ids = [card.id for card in white_cards]
        for i in range(7 - num_cards_in_hand):
            white_cards = WhiteCahCard.objects.filter(dealt=False)
            white_ids = [card.id for card in white_cards]
            picked_card_id = random.choice(white_ids)
            white_card = WhiteCahCard.objects.get(id=picked_card_id)
            player.white_cards.add(white_card)
            card_to_be_updated = WhiteCahCard.objects.filter(id=picked_card_id)
            card_to_be_updated.update(dealt=True, in_hand=True)
            pass
    print(f"{player.player_name} does not need new cards")
    return

def distribute_black_cards(party):
    players = party.players.all()
    for p in players:
        print(p.player_name)
    count = 0
    print("DISTRIBUTING BLACK CARDS")
    for r in party.rounds.all():
        num = count % int(party.num_players)
        print(num)
        black_card = r.black_card
        next_player = players[num]
        print(next_player.player_name)
        black_card.update(owner=next_player)
        count += 1
    return

def create_new_cah_submission(party, options):
    print(options)
    cah_submission = CahSubmission(
        player=options.get('player'),
        cah_round=options.get('party_round'),
        black_cah_card=options.get('black_card'),
    )
    cah_submission.save()
    for card in options.get('white_cards'):
        cah_submission.picked_cards.add(card)
        WhiteCahCard.objects.filter(id=card.id).update(in_hand=False)
    return True


def check_player_submissions(party_round, player):
    player_submission = CahSubmission.objects.filter(
        cah_round=party_round,
        player=player)
    return len(player_submission)


def check_total_submissions(party_round):
    total_submissions = CahSubmission.objects.filter(cah_round=party_round)
    return len(total_submissions)

def calculate_player_score(player, party):
    rounds = party.rounds.filter(completed=True).all()
    cah_wins = BlackCahCard.objects.filter(
        party_round__in=rounds,
        winner=player)
    player_score = {
        'score__sum': len(cah_wins),
        'score__count': len(rounds),
    }
    return player_score

def create_cah_scores(party):
    """ Create a new trivia submission for a player for a round"""
    player_scores = []
    print("Cah_scores")
    for player in party.players.all():
        player_score = calculate_player_score(player, party).get('score__sum')
        print(player_score)
        player_scores.append({'player_name': player.player_name, 
                              'score': player_score})
    print(player_scores)
    player_scores = sorted(player_scores, key=itemgetter('score'), reverse=True)
    max_score = player_scores[0].get('score')
    winners = []
    other_players = []
    for s in player_scores:
        if s.get('score') == max_score:
            winners.append(s)
        else:
            other_players.append(s)
    return {'winners': winners, 'other_players': other_players}
