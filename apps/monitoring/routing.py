"""
WebSocket URL routing para o módulo de monitoramento
"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/monitoring/<int:trip_id>/', consumers.TripTrackingConsumer.as_asgi()),
    path('ws/monitoring/fleet/', consumers.FleetTrackingConsumer.as_asgi()),
]
