from channels.generic.websocket import AsyncWebsocketConsumer
import json

class StockConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("stock_notifications", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("stock_notifications", self.channel_name)

    async def stock_notification(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'stock_notification',
            'message': message
        })) 