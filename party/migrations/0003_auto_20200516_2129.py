# Generated by Django 3.0.5 on 2020-05-16 20:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('party', '0002_auto_20200424_1925'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='party_type',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='player',
            name='sub_type',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
