from django.contrib import admin

from .models import Player, Party, Round, TriviaQuestion, TriviaSubmission

# Register your models here.
admin.site.register(Player)
admin.site.register(Party)
admin.site.register(Round)
admin.site.register(TriviaQuestion)
admin.site.register(TriviaSubmission)