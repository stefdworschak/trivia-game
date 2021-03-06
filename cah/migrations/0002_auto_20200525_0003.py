# Generated by Django 3.0.6 on 2020-05-24 23:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trivia_party', '0011_auto_20200521_2349'),
        ('cah', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blackcahcard',
            name='card_type',
        ),
        migrations.RemoveField(
            model_name='blackcahcard',
            name='deck',
        ),
        migrations.RemoveField(
            model_name='whitecahcard',
            name='card_type',
        ),
        migrations.RemoveField(
            model_name='whitecahcard',
            name='deck',
        ),
        migrations.AddField(
            model_name='whitecahcard',
            name='party',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='white_cards', to='trivia_party.Party'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='CahDeck',
        ),
    ]
