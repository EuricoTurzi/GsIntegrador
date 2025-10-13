"""
Views da API de monitoramento.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.exceptions import ValidationError

from .models import MonitoringSystem
from .serializers import (
    MonitoringSystemSerializer,
    MonitoringSystemListSerializer,
    MonitoringSystemCreateUpdateSerializer,
    MonitoringSystemDetailSerializer,
    MonitoringSystemActionSerializer
)


class MonitoringSystemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Sistemas de Monitoramento (SM).
    
    Endpoints:
    - GET /api/monitoring/ - Listar SMs
    - POST /api/monitoring/ - Criar SM (com validação de dispositivo)
    - GET /api/monitoring/{id}/ - Detalhe do SM
    - PUT /api/monitoring/{id}/ - Atualizar SM completo
    - PATCH /api/monitoring/{id}/ - Atualizar SM parcial
    - DELETE /api/monitoring/{id}/ - Deletar SM
    - GET /api/monitoring/active/ - Listar SMs ativos
    - GET /api/monitoring/in_progress/ - Listar SMs em andamento
    - GET /api/monitoring/completed/ - Listar SMs concluídos
    - POST /api/monitoring/{id}/start/ - Iniciar monitoramento
    - POST /api/monitoring/{id}/complete/ - Finalizar monitoramento
    - POST /api/monitoring/{id}/cancel/ - Cancelar monitoramento
    - GET /api/monitoring/{id}/vehicle_position/ - Posição atual do veículo
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'status',
        'is_active',
        'transportadora',
        'driver',
        'vehicle',
        'route',
        'device_was_updated'
    ]
    search_fields = [
        'identifier',
        'name',
        'driver__nome',
        'vehicle__placa',
        'route__name'
    ]
    ordering_fields = ['identifier', 'planned_start_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retorna queryset baseado no tipo de usuário.
        GR vê todos os SMs, Transportadora vê apenas seus próprios.
        """
        user = self.request.user
        
        if user.is_superuser or user.user_type == 'GR':
            return MonitoringSystem.objects.all().select_related(
                'transportadora',
                'route',
                'driver',
                'vehicle',
                'created_by'
            )
        
        if user.user_type == 'TRANSPORTADORA':
            return MonitoringSystem.objects.filter(
                transportadora=user
            ).select_related(
                'transportadora',
                'route',
                'driver',
                'vehicle',
                'created_by'
            )
        
        return MonitoringSystem.objects.none()
    
    def get_serializer_class(self):
        """
        Retorna serializer apropriado baseado na action.
        """
        if self.action == 'list':
            return MonitoringSystemListSerializer
        elif self.action == 'retrieve':
            return MonitoringSystemDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MonitoringSystemCreateUpdateSerializer
        elif self.action in ['start', 'complete', 'cancel']:
            return MonitoringSystemActionSerializer
        return MonitoringSystemSerializer
    
    def perform_create(self, serializer):
        """
        Ao criar, definir transportadora e criador automaticamente.
        A validação do dispositivo é feita no modelo.
        """
        if self.request.user.user_type == 'TRANSPORTADORA':
            serializer.save(
                transportadora=self.request.user,
                created_by=self.request.user
            )
        else:
            serializer.save(created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        Sobrescreve create para capturar ValidationError do dispositivo.
        """
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            return Response({
                'success': False,
                'errors': e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Listar apenas SMs ativos.
        GET /api/monitoring/active/
        """
        queryset = self.get_queryset().filter(is_active=True)
        serializer = MonitoringSystemListSerializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def in_progress(self, request):
        """
        Listar apenas SMs em andamento.
        GET /api/monitoring/in_progress/
        """
        queryset = self.get_queryset().filter(
            status='EM_ANDAMENTO',
            is_active=True
        )
        serializer = MonitoringSystemListSerializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """
        Listar apenas SMs concluídos.
        GET /api/monitoring/completed/
        """
        queryset = self.get_queryset().filter(status='CONCLUIDO')
        serializer = MonitoringSystemListSerializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Iniciar um monitoramento.
        POST /api/monitoring/{id}/start/
        """
        sm = self.get_object()
        
        if sm.status != 'PLANEJADO':
            return Response({
                'success': False,
                'message': f'Apenas monitoramentos com status "Planejado" podem ser iniciados. Status atual: {sm.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        sm.start_monitoring()
        
        serializer = MonitoringSystemSerializer(sm)
        return Response({
            'success': True,
            'message': 'Monitoramento iniciado com sucesso.',
            'monitoring_system': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Finalizar um monitoramento.
        POST /api/monitoring/{id}/complete/
        """
        sm = self.get_object()
        
        if sm.status != 'EM_ANDAMENTO':
            return Response({
                'success': False,
                'message': f'Apenas monitoramentos "Em Andamento" podem ser finalizados. Status atual: {sm.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        sm.complete_monitoring()
        
        serializer = MonitoringSystemSerializer(sm)
        return Response({
            'success': True,
            'message': 'Monitoramento finalizado com sucesso.',
            'monitoring_system': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancelar um monitoramento.
        POST /api/monitoring/{id}/cancel/
        Body: {"reason": "Motivo do cancelamento"} (opcional)
        """
        sm = self.get_object()
        
        if sm.status in ['CONCLUIDO', 'CANCELADO']:
            return Response({
                'success': False,
                'message': f'Monitoramentos com status "{sm.get_status_display()}" não podem ser cancelados.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason')
        sm.cancel_monitoring(reason=reason)
        
        serializer = MonitoringSystemSerializer(sm)
        return Response({
            'success': True,
            'message': 'Monitoramento cancelado com sucesso.',
            'monitoring_system': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def vehicle_position(self, request, pk=None):
        """
        Retorna a posição atual do veículo do SM.
        GET /api/monitoring/{id}/vehicle_position/
        """
        sm = self.get_object()
        
        position = sm.current_vehicle_position
        
        if position:
            return Response({
                'success': True,
                'monitoring_id': sm.id,
                'identifier': sm.identifier,
                'vehicle_placa': sm.vehicle.placa,
                'position': position
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Posição do veículo não disponível.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def check_device(self, request, pk=None):
        """
        Verifica o status atual do dispositivo do veículo.
        GET /api/monitoring/{id}/check_device/
        """
        sm = self.get_object()
        
        if not hasattr(sm.vehicle, 'device'):
            return Response({
                'success': False,
                'message': 'Veículo não possui dispositivo vinculado.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        device = sm.vehicle.device
        
        return Response({
            'success': True,
            'monitoring_id': sm.id,
            'identifier': sm.identifier,
            'vehicle_placa': sm.vehicle.placa,
            'device_id': device.suntech_device_id,
            'is_updated': device.is_updated_recently,
            'minutes_since_update': device.minutes_since_last_update,
            'last_system_date': device.last_system_date
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def position_history(self, request, pk=None):
        """
        Retorna o histórico de posições da viagem.
        GET /api/monitoring/{id}/position_history/?limit=100
        """
        sm = self.get_object()
        
        # Parâmetro opcional de limite
        limit = request.query_params.get('limit', None)
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                limit = None
        
        # Buscar histórico
        history = sm.get_position_history(limit=limit)
        
        from .serializers import VehiclePositionHistorySerializer
        serializer = VehiclePositionHistorySerializer(history, many=True)
        
        return Response({
            'success': True,
            'monitoring_id': sm.id,
            'identifier': sm.identifier,
            'total_positions': history.count(),
            'positions': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def position_history_geojson(self, request, pk=None):
        """
        Retorna o histórico de posições em formato GeoJSON.
        GET /api/monitoring/{id}/position_history_geojson/
        """
        sm = self.get_object()
        
        geojson = sm.get_position_history_geojson()
        
        if not geojson:
            return Response({
                'success': False,
                'message': 'Nenhuma posição encontrada no histórico.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'monitoring_id': sm.id,
            'identifier': sm.identifier,
            'geojson': geojson
        }, status=status.HTTP_200_OK)
