from django.urls import path

from . import views

urlpatterns = [
     path('', views.new_party, name='new_party'),
     path('join/find_player', views.find_player, name='find_player'),
     path('join/create_player', views.create_player, name='create_player'),
     path('join/<str:party_id>', views.join_party, name='join_party'),
     path('join/<str:party_id>', views.join_party, name='join_party'),
     path('start/<str:party_id>', views.start_screen, name='start_screen'),
     path('finish/<str:party_id>', views.finish_screen, name='finish_screen'),
     path('waiting/<str:party_id>', views.waiting_screen, name='waiting_screen'),
     path('create_or_join_party', views.create_or_join_party,
          name='create_or_join_party'),
     path('party/<str:party_id>', views.party, name='party'),
     path('party/<str:party_id>/submission', 
               views.submit_question, name='submission'),
     path('party/<str:party_id>/correct', views.correct_submission, name='correct_submission'),
     path('party/<str:party_id>/wrong', views.wrong_submission, name='wrong_submission'),
]