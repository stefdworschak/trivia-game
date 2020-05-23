from django.urls import path

from . import views

urlpatterns = [
     path('', views.new_party, name='new_party'),
     path('join/find_player', views.find_player, name='find_player'),
     path('join/create_player', views.create_player, name='create_player'),
     path('join/<str:party_id>', views.join_party, name='join_party'),
     path('start/<str:party_id>', views.start_screen, name='start_screen'),
     path('create_or_join_party', views.create_or_join_party,
          name='create_or_join_party'),
     path('recreate_party', views.recreate_party,
          name='recreate_party'),
]