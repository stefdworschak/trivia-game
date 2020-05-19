from django.db import models, close_old_connections

import json

# Create you
class Player(models.Model):
    player_name = models.CharField(max_length=30, unique=True)
    score = models.FloatField()
    is_admin = models.BooleanField()
    close_old_connections()

class Party(models.Model):
    party_name = models.CharField(max_length=30, unique=True)
    admin = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="admin_id")
    players = models.ManyToManyField(Player, blank=True)
    num_players = models.IntegerField()
    num_rounds = models.IntegerField()
    party_type = models.CharField(max_length=255, blank=True)
    party_subtype = models.CharField(max_length=255, blank=True)
    close_old_connections()

    def __str__(self):
        return self.party_name + f" ({self.players.count()} of {self.num_players} players)"


class Round(models.Model):
    completed = models.BooleanField(default=False)
    party = models.ForeignKey(Party, related_name='rounds', on_delete=models.CASCADE)
    close_old_connections()

class TriviaQuestion(models.Model):
    question_text = models.CharField(max_length=1048, blank=True)
    question_answers = models.CharField(max_length=1048, blank=True)
    correct_answer = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=255, blank=True)
    question_type = models.CharField(max_length=255, blank=True)
    difficulty = models.CharField(max_length=255, blank=True)
    trivia_round = models.ForeignKey(Round, related_name='question', on_delete=models.CASCADE)
    def set_answers(self, answers):
        self.question_answers = json.dumps(answers)

    def get_answers(self):
        return self.question_answers

    def get_all(self):
        return {
            'question_text': self.question_text,
            'question_answers': self.question_answers,
            'correct_answer': self.correct_answer,
            'category': self.category,
            'question_type': self.question_type,
            'difficulty': self.difficulty
        }


class TriviaSubmission(models.Model):
    player = models.ForeignKey(Player, related_name='submission', on_delete=models.CASCADE)
    submitted_answer = models.CharField(max_length=255, blank=True)
    score = models.IntegerField()
    trivia_round = models.ForeignKey(Round, related_name='submission', on_delete=models.CASCADE)
    trivia_question = models.ForeignKey(TriviaQuestion, related_name='question', on_delete=models.CASCADE)
    close_old_connections()