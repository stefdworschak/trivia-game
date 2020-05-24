import requests
from datetime import timedelta

from django.utils import timezone

from .models import TriviaSubmission, TriviaQuestion, Round
from .helpers import jumble_answers


def add_trivia_questions(party, remove_duplicates=True):
    num_count = 0
    category = ''
    rounds = int(party.num_rounds) * 4
    if party.party_subtype != 'any':
        category = f'&category={party.party_subtype}'
    trivia_url = f'https://opentdb.com/api.php?amount={rounds}&type=multiple{category}'
    res = requests.get(trivia_url)
    if res.status_code == 200:
        questions = res.json()['results']
    for question in questions:
        if num_count > int(party.num_rounds):
            print("COUNT", str(num_count))
            return
        # TODO: Check that this is working once there is more data
        two_weeks_ago = timezone.now() - timedelta(days=14)
        duplicate_questions = len(TriviaQuestion.objects.filter(
            question_text=question.get('question'),
            created_at__gt=two_weeks_ago))
        if duplicate_questions > 0 and remove_duplicates:
            continue
        party_round = Round(party=party, num_submissions=0)
        party_round.save()
        trivia_question = TriviaQuestion(
            question_text=question.get('question'),
            question_answers=jumble_answers(
                question.get('incorrect_answers'),
                question.get('correct_answer')),
            correct_answer=question.get('correct_answer'),
            category=question.get('category'),
            question_type=question.get('type'),
            difficulty=question.get('difficulty'),
            party_round=party_round
        )
        trivia_question.save()
        num_count += 1
    
    if num_count < int(party.num_rounds):
        add_trivia_questions(party, remove_duplicates=False)
    return


def create_new_trivia_submission(party_round, player, question_id, answer):
    score = 0
    trivia_question = TriviaQuestion.objects.get(id=question_id)
    player_submission = TriviaSubmission.objects.filter(
        party_round=party_round, player=player)
    if len(player_submission) == 0:
        if trivia_question.correct_answer == answer:
            score = 1
        trivia_submission = TriviaSubmission(
            player=player,
            party_round=party_round,
            trivia_question=trivia_question,
            submitted_answer=answer,
            score=score)
        trivia_submission.save()
    return score


def create_trivia_submission_scores(party_round):
    """ Create a new trivia submission for a player for a round"""
    submission_scores = {}
    submissions = {}
    trivia_submissions = party_round.submissions.all()
    trivia_question = TriviaQuestion.objects.get(party_round=party_round)
    submission_scores['correct_answer'] = trivia_question.correct_answer
    for submission in trivia_submissions:
        player_name = submission.player.player_name
        score = submission.score
        submissions[player_name] = score
    submission_scores['submissions'] = submissions
    return submission_scores
