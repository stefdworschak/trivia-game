import math

from django import template

register = template.Library()

@register.filter()
def all_submissions(num_players, submissions):
    #try:
    return len(submissions) == (num_players - 1)
    #except:
        #return False

@register.simple_tag()
def calculate_turn(**kwargs):
    num_rounds = kwargs['r']
    num_players = kwargs['pl']
    if isinstance(num_players, str):
        num_players = int(num_players)
    if isinstance(num_rounds, str):
        num_rounds = int(num_rounds)
    turn = (num_rounds) % num_players
    return num_players if turn == 0 else turn

@register.simple_tag()
def calculate_round(**kwargs):
    num_rounds = kwargs['r']
    current_round = kwargs['cr']
    if isinstance(num_rounds, str):
        num_rounds = int(num_rounds)
    if isinstance(current_round, str):
        current_round = int(current_round)
    
    return math.ceil(current_round / num_rounds)