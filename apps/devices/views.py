"""
Views da API de dispositivos.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.conf import settings

from .models import Device
from .serializers import (
    DeviceSerializer,
    DeviceListSerializer,
    DeviceCreateUpdateSerializer,
    DeviceSyncSerializer,
    DeviceStatusSerializer
)


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar dispositivos/rastreadores.
    
    Endpoints:
    - GET /api/devices/ - Listar dispositivos
    - POST /api/devices/ - Criar dispositivo
    - GET /api/devices/{id}/ - Detalhe do dispositivo
    - PUT /api/devices/{id}/ - Atualizar dispositivo completo
    - PATCH /api/devices/{id}/ - Atualizar dispositivo parcial
    - DELETE /api/devices/{id}/ - Deletar dispositivo
    - GET /api/devices/updated/ - Listar dispositivos atualizados
    - GET /api/devices/outdated/ - Listar dispositivos desatualizados
    - POST /api/devices/{id}/sync/ - Sincronizar com Suntech
    - GET /api/devices/{id}/status/ - Verificar status de atualização
    - POST /api/devices/{id}/activate/ - Ativar dispositivo
    - POST /api/devices/{id}/deactivate/ - Desativar dispositivo
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'last_ignition_status', 'vehicle__transportadora']
    search_fields = [
        'suntech_device_id',
        'imei',
        'label',
        'vehicle__placa',
        'vehicle__modelo'
    ]
    ordering_fields = ['suntech_device_id', 'last_system_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retorna queryset baseado no tipo de usuário.
        GR vê todos os dispositivos, Transportadora vê apenas seus próprios.
        """
        user = self.request.user
        
        if user.is_superuser or user.user_type == 'GR':
            return Device.objects.all().select_related('vehicle', 'vehicle__transportadora')
        
        if user.user_type == 'TRANSPORTADORA':
            return Device.objects.filter(
                vehicle__transportadora=user
            ).select_related('vehicle', 'vehicle__transportadora')
        
        return Device.objects.none()
    
    def get_serializer_class(self):
        """
        Retorna serializer apropriado baseado na action.
        """
        if self.action == 'list':
            return DeviceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DeviceCreateUpdateSerializer
        elif self.action == 'sync':
            return DeviceSyncSerializer
        elif self.action == 'status':
            return DeviceStatusSerializer
        return DeviceSerializer
    
    @action(detail=False, methods=['get'])
    def updated(self, request):
        """
        Listar apenas dispositivos atualizados recentemente.
        GET /api/devices/updated/
        """
        queryset = self.get_queryset().filter(is_active=True)
        updated_devices = [
            device for device in queryset
            if device.is_updated_recently
        ]
        
        serializer = DeviceListSerializer(updated_devices, many=True)
        return Response({
            'count': len(updated_devices),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def outdated(self, request):
        """
        Listar apenas dispositivos desatualizados.
        GET /api/devices/outdated/
        """
        queryset = self.get_queryset().filter(is_active=True)
        outdated_devices = [
            device for device in queryset
            if not device.is_updated_recently
        ]
        
        serializer = DeviceListSerializer(outdated_devices, many=True)
        return Response({
            'count': len(outdated_devices),
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Sincronizar dispositivo com a API Suntech.
        POST /api/devices/{id}/sync/
        """
        device = self.get_object()
        
        success = device.sync_with_suntech()
        
        if success:
            serializer = DeviceSerializer(device)
            return Response({
                'success': True,
                'message': 'Dispositivo sincronizado com sucesso.',
                'device': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Erro ao sincronizar dispositivo com Suntech.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Verificar status de atualização do dispositivo.
        GET /api/devices/{id}/status/
        """
        device = self.get_object()
        
        return Response({
            'device_id': device.id,
            'suntech_device_id': device.suntech_device_id,
            'vehicle_placa': device.vehicle.placa,
            'is_updated': device.is_updated_recently,
            'minutes_since_update': device.minutes_since_last_update,
            'threshold_minutes': settings.DEVICE_UPDATE_THRESHOLD_MINUTES,
            'last_system_date': device.last_system_date
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Ativar um dispositivo.
        POST /api/devices/{id}/activate/
        """
        device = self.get_object()
        device.is_active = True
        device.save()
        
        serializer = self.get_serializer(device)
        return Response({
            'message': 'Dispositivo ativado com sucesso.',
            'device': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desativar um dispositivo.
        POST /api/devices/{id}/deactivate/
        """
        device = self.get_object()
        device.is_active = False
        device.save()
        
        serializer = self.get_serializer(device)
        return Response({
            'message': 'Dispositivo desativado com sucesso.',
            'device': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def sync_all(self, request):
        """
        Sincronizar todos os dispositivos com Suntech.
        POST /api/devices/sync_all/
        
        Apenas para usuários GR ou staff.
        """
        user = request.user
        
        if not (user.is_staff or user.is_superuser or user.user_type == 'GR'):
            return Response({
                'success': False,
                'error': 'Permissão negada'
            }, status=status.HTTP_403_FORBIDDEN)
        
        devices = self.get_queryset()
        success_count = 0
        
        for device in devices:
            if device.sync_with_suntech():
                success_count += 1
        
        return Response({
            'success': True,
            'message': f'{success_count} de {devices.count()} dispositivos sincronizados.',
            'total': devices.count(),
            'synced': success_count
        }, status=status.HTTP_200_OK)
