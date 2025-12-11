"""
WebSocket URL routing.
"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/events/', consumers.RealtimeEventConsumer.as_asgi()),
]