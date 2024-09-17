import json
import logging
import math
import time

from asgiref.sync import async_to_sync
from channels.consumer import AsyncConsumer, SyncConsumer
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings

from .utils import trace

log = logging.getLogger("kenny")


class OrdersSyncConsumers(WebsocketConsumer):
    def websocket_connect(self, event):
        # trace("websocket_connect()", event, self.channel_name)
        log.debug("Trying to connect to ws")
        self.accept()

    def websocket_disconnect(self, event):
        # trace("websocket_disconnect()", event)
        # Leave monitoring group
        log.debug(
            'Socket "%s" leaves group "%s"'
            % (self.channel_name, settings.ORDERS_CHANNELS_NAME)
        )
        pass

    def websocket_receive(self, event):
        log.debug("websocket_receive()", event)

    def data_received(self, event):
        log.debug("data_received()", event)
        self.send(
            text_data={
                "type": "websocket.send",
                "text": event["content"],
            }
        )


class OrdersSyncConsumer(SyncConsumer):
    def websocket_connect(self, event):
        trace("websocket_connect()", event, self.channel_name)
        log.debug("Trying to connect to ws")
        self.send({"type": "websocket.accept"})

        # Join monitoring group
        trace(
            'Socket "%s" joins group "%s"'
            % (self.channel_name, settings.ORDERS_CHANNELS_NAME)
        )

        log.debug(
            "Trying to connect to {} {} {}".format(
                self.channel_name, settings.ORDERS_CHANNELS_NAME, settings.REDIS_URL
            )
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
