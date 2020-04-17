from django.db import models

# Create you
class Player(models.Model):
    player_name = models.CharField(max_length=30, unique=True)
    score = models.FloatField()
    is_admin = models.BooleanField()

class Party(models.Model):
    party_name = models.CharField(max_length=30, unique=True)
    players = models.ManyToManyField(Player)
    num_players = models.IntegerField()