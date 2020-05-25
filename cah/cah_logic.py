import json
import random

from trivia_party.models import Player, Round
from .models import WhiteCahCard, BlackCahCard

FILEPATH = 'cah/data/cah_packs.json'


def load_cards_from_file(party):
    black_cards = []
    white_cards = []
    with open(FILEPATH, 'r') as f:
        all_packs = json.load(f)

    packs = party.party_subtype.split(',')
    for pack in all_packs.get('pack_contents'):
        print(pack)
        black_cards += pack.get('black', [])
        white_cards += pack.get('white', [])
    return black_cards, white_cards


def create_new_deck(party):
    black_cards, white_cards = load_cards_from_file(party)
    # Choose the black cards
    num_white_cards = 0
    for i in party.num_rounds:
        black_card = random.choice(black_cards)
        num_white_cards += black_card.get('pick')
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