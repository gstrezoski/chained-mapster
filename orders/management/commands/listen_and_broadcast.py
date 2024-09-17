import signal
import sys
import traceback
import time
import logging
import json
import redis
import channels.layers
from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand
from django.conf import settings
from orders.utils import get_redis_connection


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Listen to incoming requests from EVA, and broadcasting it to websocket clients'

    def add_arguments(self, parser):
        parser.add_argument('-c', '--channel', default='logins')

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(0))
        self.logger = logger or logging.getLogger(__name__)

    def handle(self, *args, **options):
        self.set_logger(options.get('verbosity'))
        self.channel = options.get('channel')
        self.logger.debug('Initializing Redis listener... [subscribing channel: "%s"]' % self.channel)
        self.redis = None
        self.pubsub = None
        self.logger.info('Initializing Redis listener... [subscribing channel: "%s"]' % self.channel)
        self.loop()

    def set_logger(self, verbosity):
        """
        Set logger level based on verbosity option
        """
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(module)s| %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if verbosity == 0:
            self.logger.setLevel(logging.WARN)
        elif verbosity == 1:  # default
            self.logger.setLevel(logging.INFO)
        elif verbosity > 1:
            self.logger.setLevel(logging.DEBUG)

        if verbosity > 2:
            logging.getLogger().setLevel(logging.DEBUG)

    def connect_and_subscribe(self):
        while True:
            self.logger.debug('Trying to connect to redis at "%s" ...' % settings.REDIS_URL)
            try:
                self.redis = get_redis_connection()
                self.redis.ping()
            except (redis.exceptions.ConnectionError, redis.exceptions.ResponseError):
                time.sleep(1)
            else:
                break
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(self.channel)
        self.logger.info('Connected to redis at "%s".' % settings.REDIS_URL)

    def loop(self):
        self.connect_and_subscribe()
        self.logger.info("Connected and subscirbed and in loop.")
        while True:
            try:
                for item in self.pubsub.listen():
                    if item['type'] == 'message':
                        # Sample item:
                        # {'type': 'message', 'pattern': None, 'channel': 'orders', 'data': 'XXXXXXXX'}
                        self.on_data_received(item['channel'], item['data'])
            except (redis.exceptions.ConnectionError, redis.exceptions.ResponseError):
                self.logger.error('Lost connections to redis.')
                self.connect_and_subscribe()
            except Exception as e:
                self.logger.error(str(e))
                self.logger.debug(traceback.format_exc())
                time.sleep(1)

    def on_data_received(self, channel, data):
        self.logger.debug('Data received on channel "%s"' % channel)
        self.logger.debug(data)

        # Broadcast process message to subscribers
        channel_layer = channels.layers.get_channel_layer()
        group = channel
        self.logger.info('Send "%s" to group "%s"' % (data, group))
        async_to_sync(channel_layer.group_send)(
            group, {
                "type": 'data_received',
                "content": data,
            })

