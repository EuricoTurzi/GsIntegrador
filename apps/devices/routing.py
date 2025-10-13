"""
WebSocket URL routing para Devices
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Dashboard com todos os dispositivos
    re_path(r'ws/devices/$', consumers.DeviceTrackingConsumer.as_asgi()),
    
    # Dispositivo específico
    re_path(r'ws/devices/(?P<device_id>\d+)/$', consumers.DeviceTrackingConsumer.as_asgi()),
]
