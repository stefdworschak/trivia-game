# Generated by Django 3.0.6 on 2020-05-24 23:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cah', '0002_auto_20200525_0003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blackcahcard',
            name='card_text',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='whitecahcard',
            name='card_text',
            field=models.CharField(max_length=255),
        ),
    ]
