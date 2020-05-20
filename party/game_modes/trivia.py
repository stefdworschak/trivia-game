from party.models import TriviaSubmission, TriviaQuestion


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
        return True
    return False
