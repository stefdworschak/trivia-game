from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/trivia/<str:party_name>/', consumers.TriviaConsumer),
    path('ws/cah/<str:party_name>/', consumers.TriviaConsumer),
]