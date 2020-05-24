import json
import random

from trivia_party.models import Player
from .models import CahDeck, WhiteCahCard, BlackCahCard, Round

FILEPATH = 'cah/data/cah_packs.json'

def load_cards_from_file(party):
    black_cards = []
    white_cards = []
    with open(FILEPATH, 'r') as f:
        all_packs = json.load(f)

    packs = party.party_subtype.split(',')
    for pack in all_packs:
        pack_id = pack.get('pack', {}).get('id')
        if pack_id in packs:
            black_cards += pack.get('black', [])
            white_cards += pack.get('white', [])
    return black_cards, white_cards

def create_new_deck(party):
    black_cards, white_cards = load_cards_from_file(party)
    # Choose the black cards
    for r in party.num_rounds:
        black_card = random.choice(black_cards)
        

    return