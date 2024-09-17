import json
import logging
import math
import time

from asgiref.sync import async_to_sync
from channels.consumer import AsyncConsumer, SyncConsumer
from django.conf import settings

from .utils import trace


class OrdersSyncConsumer(SyncConsumer):
    def websocket_connect(self, event):
        trace("websocket_connect()", event, self.channel_name)
        self.send({"type": "websocket.accept"})

        # Join monitoring group
        trace(
            'Socket "%s" joins group "%s"'
            % (self.channel_name, settings.ORDERS_CHANNELS_NAME)
        )
        async_to_sync(self.channel_layer.group_add)(
            settings.ORDERS_CHANNELS_NAME, self.channel_name
        )

    def websocket_disconnect(self, event):
        trace("websocket_disconnect()", event)
        # Leave monitoring group
        trace(
            'Socket "%s" leaves group "%s"'
            % (self.channel_name, settings.ORDERS_CHANNELS_NAME)
        )
        async_to_sync(self.channel_layer.group_discard)(
            settings.ORDERS_CHANNELS_NAME, self.channel_name
        )

    def websocket_receive(self, event):
        trace("websocket_receive()", event)

    def data_received(self, event):
        trace("data_received()", event)
        self.send(
            {
                "type": "websocket.send",
                "text": event["content"],
            }
        )


class OrderAsyncConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        trace("websocket_connect()", event)
        await self.send({"type": "websocket.accept"})
        # Join monitoring group
        await self.channel_layer.group_add(
            settings.ORDERS_CHANNELS_NAME, self.channel_name
        )

    async def websocket_disconnect(self, event):
        trace("websocket_disconnect()", event)
        # Leave monitoring group
        await self.channel_layer.group_discard(
            settings.ORDERS_CHANNELS_NAME, self.channel_name
        )

    async def websocket_receive(self, event):
        trace("websocket_receive()", event)

    async def data_received(self, event):
        trace("data_received()", event)
        await self.send(
            {
                "type": "websocket.send",
                "text": event["content"],
            }
        )
