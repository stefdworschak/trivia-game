from django.urls import path

from . import views

urlpatterns = [
    path('', views.new_party, name='new_party'),
    path('create', views.create_party, name='create_party'),
    path('join/find_player', views.find_player, name='find_player'),
    path('join/<str:party_id>', views.join_party, name='join_party'),
]