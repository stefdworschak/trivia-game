from trivia_party.models import Player, Round, Party
from django.db import models


class WhiteCahCard(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    card_text = models.CharField(max_length=255)
    party = models.ForeignKey(Party, related_name='white_cards', on_delete=models.CASCADE)
    player = models.ForeignKey(Player, related_name='white_cards', null=True, blank=True, on_delete=models.CASCADE)
    in_hand = models.BooleanField(default=False)

class BlackCahCard(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    card_text = models.CharField(max_length=255)
    pick = models.IntegerField()
    draw = models.IntegerField()
    party_round = models.ForeignKey(Round, related_name='black_card', null=True, blank=True, on_delete=models.CASCADE)
    winner = models.ForeignKey(Player, related_name='black_cards', null=True, blank=True, on_delete=models.CASCADE)

class CahSubmission(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    player = models.ForeignKey(Player, related_name='cah_submissions', on_delete=models.CASCADE)
    picked_cards = models.ManyToManyField(WhiteCahCard, blank=True)
    cah_round = models.ForeignKey(Round, related_name='cah_submissions', on_delete=models.CASCADE)
    black_cah_card = models.ForeignKey(BlackCahCard, related_name='cah_submissions', on_delete=models.CASCADE)
