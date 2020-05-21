# party/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.party_name = self.scope['url_route']['kwargs']['party_name']
        self.room_group_name = 'chat_%s' % self.party_name
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        submission_score = text_data_json['submission_score']
        player_name = text_data_json['player_name']
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'submission_score': submission_score,
                'message': message,
                'player_name': player_name,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        submission_score = event['submission_score']
        player_name = text_data_json['player_name']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'submission_score': submission_score, 
            'message': message,
            'player_name': player_name,
        }))
