"""
ASGI config for mapster project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

settings_module =  'mapster.production' if "PRODUCTION" in os.environ else 'mapster.settings'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

import django
django.setup()

from django.urls import path
from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter
from django.core.asgi import get_asgi_application
from orders.consumers import OrdersSyncConsumer

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter([path("ws/orders/", OrdersSyncConsumer.as_asgi())]),
})
