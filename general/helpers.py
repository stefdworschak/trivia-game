from trivia_party.trivia import add_trivia_questions


def add_party_content(party):
    if party.party_type == 'trivia':
        add_trivia_questions(party)
    return