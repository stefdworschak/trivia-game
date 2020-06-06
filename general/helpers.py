from trivia_party.trivia import add_trivia_questions
from cah.cah_logic import create_new_deck, distribute_black_cards

def add_party_content(party):
    """ Applies logic specific to party type when creating new party """
    if party.party_type == 'trivia':
        add_trivia_questions(party)
    elif party.party_type == 'cah':
        create_new_deck(party)
    return

def add_extra_party_content(party):
    """ Applies logic specific to party type after all players have joined """
    if party.party_type == 'trivia':
        return
    elif party.party_type == 'cah':
        distribute_black_cards(party)
    return