"""
WebSocket Consumers para Device Tracking

Gerencia conexões WebSocket para atualização em tempo real de dispositivos.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class DeviceTrackingConsumer(AsyncWebsocketConsumer):
    """
    Consumer para rastreamento de dispositivos em tempo real.
    
    Rotas:
    - ws/devices/ -> Todos os dispositivos (dashboard)
    - ws/devices/<device_id>/ -> Dispositivo específico
    """
    
    async def connect(self):
        """Conecta ao WebSocket e ao grupo apropriado"""
        self.user = self.scope["user"]
        
        # Pega o device_id da URL, se existir
        self.device_id = self.scope['url_route']['kwargs'].get('device_id')
        
        if self.device_id:
            # Conecta ao grupo de um dispositivo específico
            self.group_name = f'device_{self.device_id}'
        else:
            # Conecta ao grupo geral de todos os dispositivos
            self.group_name = 'all_devices'
        
        # Adiciona ao grupo
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envia mensagem de confirmação
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Conectado ao grupo: {self.group_name}'
        }))
    
    async def disconnect(self, close_code):
        """Remove do grupo ao desconectar"""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    # Handlers para diferentes tipos de mensagens
    
    async def device_sync(self, event):
        """
        Handler para notificações de sincronização de dispositivo.
        Chamado pelo notify_device_sync task.
        """
        await self.send(text_data=json.dumps({
            'type': 'device_sync',
            'data': event['data']
        }))
    
    async def device_position_update(self, event):
        """
        Handler para atualização de posição de dispositivo.
        """
        await self.send(text_data=json.dumps({
            'type': 'position_update',
            'data': event['data']
        }))
    
    async def device_status_change(self, event):
        """
        Handler para mudança de status de dispositivo.
        """
        await self.send(text_data=json.dumps({
            'type': 'status_change',
            'data': event['data']
        }))
