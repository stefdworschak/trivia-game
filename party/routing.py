from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/party/<str:party_name>/', consumers.ChatConsumer),
]