"""
WebSocket Consumers para tracking em tempo real
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class TripTrackingConsumer(AsyncWebsocketConsumer):
    """
    Consumer para tracking de uma viagem específica em tempo real.
    URL: ws/monitoring/<trip_id>/
    """
    
    async def connect(self):
        """Conexão do WebSocket"""
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.room_group_name = f'trip_{self.trip_id}'
        
        # Verificar autenticação
        user = self.scope.get('user')
        if isinstance(user, AnonymousUser):
            await self.close()
            return
        
        # Verificar permissões
        has_permission = await self.check_trip_permission(user, self.trip_id)
        if not has_permission:
            await self.close()
            return
        
        # Adicionar ao grupo do canal
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar posição inicial
        initial_position = await self.get_current_position(self.trip_id)
        if initial_position:
            await self.send(text_data=json.dumps({
                'type': 'position_update',
                'data': initial_position
            }))
    
    async def disconnect(self, close_code):
        """Desconexão do WebSocket"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Receber mensagem do cliente"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'request_position':
                # Cliente solicitou atualização de posição
                position = await self.get_current_position(self.trip_id)
                if position:
                    await self.send(text_data=json.dumps({
                        'type': 'position_update',
                        'data': position
                    }))
        except json.JSONDecodeError:
            pass
    
    async def position_update(self, event):
        """Receber atualização de posição do grupo e enviar ao cliente"""
        await self.send(text_data=json.dumps({
            'type': 'position_update',
            'data': event['data']
        }))
    
    async def trip_status_change(self, event):
        """Receber mudança de status da viagem"""
        await self.send(text_data=json.dumps({
            'type': 'status_change',
            'data': event['data']
        }))
    
    async def device_sync_update(self, event):
        """Receber notificação de sincronização do dispositivo"""
        await self.send(text_data=json.dumps({
            'type': 'device_sync',
            'data': event['data']
        }))
    
    async def trip_alert(self, event):
        """🆕 Receber alertas da viagem (desvio de rota, paradas, etc)"""
        await self.send(text_data=json.dumps({
            'type': 'trip_alert',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def check_trip_permission(self, user, trip_id):
        """Verifica se usuário tem permissão para ver a viagem"""
        from apps.monitoring.models import MonitoringSystem
        
        try:
            if user.is_superuser or user.user_type == 'GR':
                trip = MonitoringSystem.objects.filter(pk=trip_id).exists()
                return trip
            else:
                trip = MonitoringSystem.objects.filter(
                    pk=trip_id,
                    transportadora=user
                ).exists()
                return trip
        except Exception:
            return False
    
    @database_sync_to_async
    def get_current_position(self, trip_id):
        """Busca posição atual do veículo"""
        from apps.monitoring.models import MonitoringSystem
        
        try:
            trip = MonitoringSystem.objects.select_related(
                'vehicle', 'vehicle__device', 'route', 'driver'
            ).get(pk=trip_id)
            
            position = trip.current_vehicle_position
            if position:
                return {
                    'trip_id': trip.id,
                    'identifier': trip.identifier,
                    'status': trip.status,
                    'latitude': position['latitude'],
                    'longitude': position['longitude'],
                    'speed': position['speed'],
                    'address': position['address'],
                    'last_update': position['last_update'].isoformat() if position['last_update'] else None,
                    'driver': trip.driver.nome,
                    'vehicle': trip.vehicle.placa,
                }
            return None
        except Exception:
            return None


class FleetTrackingConsumer(AsyncWebsocketConsumer):
    """
    Consumer para tracking de toda a frota em tempo real.
    URL: ws/monitoring/fleet/
    """
    
    async def connect(self):
        """Conexão do WebSocket"""
        user = self.scope.get('user')
        
        # Verificar autenticação
        if isinstance(user, AnonymousUser):
            await self.close()
            return
        
        # Determinar grupo baseado no tipo de usuário
        if user.is_superuser or user.user_type == 'GR':
            self.room_group_name = 'fleet_all'
        else:
            self.room_group_name = f'fleet_transportadora_{user.pk}'
        
        # Adicionar ao grupo do canal
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar posições iniciais de todas viagens ativas
        initial_positions = await self.get_active_trips_positions(user)
        if initial_positions:
            await self.send(text_data=json.dumps({
                'type': 'fleet_update',
                'data': initial_positions
            }))
    
    async def disconnect(self, close_code):
        """Desconexão do WebSocket"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Receber mensagem do cliente"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'request_fleet_update':
                # Cliente solicitou atualização da frota
                user = self.scope.get('user')
                positions = await self.get_active_trips_positions(user)
                if positions:
                    await self.send(text_data=json.dumps({
                        'type': 'fleet_update',
                        'data': positions
                    }))
        except json.JSONDecodeError:
            pass
    
    async def fleet_update(self, event):
        """Receber atualização da frota do grupo e enviar ao cliente"""
        await self.send(text_data=json.dumps({
            'type': 'fleet_update',
            'data': event['data']
        }))
    
    async def position_update(self, event):
        """Receber atualização de posição individual"""
        await self.send(text_data=json.dumps({
            'type': 'position_update',
            'data': event['data']
        }))
    
    async def device_sync_update(self, event):
        """Receber notificação de sincronização do dispositivo"""
        await self.send(text_data=json.dumps({
            'type': 'device_sync',
            'data': event['data']
        }))
    
    async def trip_alert(self, event):
        """🆕 Receber alertas das viagens (desvio de rota, paradas, etc)"""
        await self.send(text_data=json.dumps({
            'type': 'trip_alert',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_active_trips_positions(self, user):
        """Busca posições de todas viagens ativas"""
        from apps.monitoring.models import MonitoringSystem
        
        try:
            # Filtrar viagens baseado no usuário
            if user.is_superuser or user.user_type == 'GR':
                trips = MonitoringSystem.objects.filter(status='EM_ANDAMENTO')
            else:
                trips = MonitoringSystem.objects.filter(
                    status='EM_ANDAMENTO',
                    transportadora=user
                )
            
            trips = trips.select_related('vehicle', 'vehicle__device', 'driver', 'route')
            
            positions = []
            for trip in trips:
                position = trip.current_vehicle_position
                if position:
                    positions.append({
                        'trip_id': trip.id,
                        'identifier': trip.identifier,
                        'name': trip.name,
                        'status': trip.status,
                        'latitude': position['latitude'],
                        'longitude': position['longitude'],
                        'speed': position['speed'],
                        'address': position['address'],
                        'last_update': position['last_update'].isoformat() if position['last_update'] else None,
                        'driver': trip.driver.nome,
                        'vehicle': trip.vehicle.placa,
                        'device_status': trip.device_status,  # 🆕 Status do dispositivo
                    })
            
            return positions
        except Exception as e:
            print(f"Erro ao buscar posições: {e}")
            return []
