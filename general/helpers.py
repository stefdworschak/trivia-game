from trivia_party.trivia import add_trivia_questions
from cah.cah_logic import create_new_deck

def add_party_content(party):
    if party.party_type == 'trivia':
        add_trivia_questions(party)
    elif party.party_type == 'cah':
        create_new_deck(party)
    return