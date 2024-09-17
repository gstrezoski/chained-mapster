"""
ASGI config for mapster project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os, django
from django.urls import path
from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter
from django.core.asgi import get_asgi_application
from orders.consumers import OrdersSyncConsumer

settings_module =  'orders.production' if "WEBSITE_HOSTNAME" in os.environ else 'orders.settings'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter([path("ws/orders/", OrdersSyncConsumer.as_asgi())]),
})
