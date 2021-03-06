# Generated by Django 3.0.6 on 2020-05-20 22:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trivia_party', '0007_triviasubmission_trivia_question'),
    ]

    operations = [
        migrations.RenameField(
            model_name='triviaquestion',
            old_name='trivia_round',
            new_name='party_round',
        ),
        migrations.RemoveField(
            model_name='triviasubmission',
            name='trivia_round',
        ),
        migrations.AddField(
            model_name='round',
            name='num_submissions',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='round',
            name='skip_votes',
            field=models.ManyToManyField(blank=True, to='trivia_party.Player'),
        ),
        migrations.AddField(
            model_name='triviasubmission',
            name='party_round',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='trivia_party.Round'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='triviasubmission',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='trivia_party.Player'),
        ),
        migrations.AlterField(
            model_name='triviasubmission',
            name='trivia_question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='trivia_party.TriviaQuestion'),
        ),
    ]
