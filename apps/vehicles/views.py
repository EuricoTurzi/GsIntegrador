"""
Views da API de veículos.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Vehicle
from .serializers import (
    VehicleSerializer,
    VehicleListSerializer,
    VehicleCreateUpdateSerializer
)


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar veículos.
    
    Endpoints:
    - GET /api/vehicles/ - Listar veículos
    - POST /api/vehicles/ - Criar veículo
    - GET /api/vehicles/{id}/ - Detalhe do veículo
    - PUT /api/vehicles/{id}/ - Atualizar veículo completo
    - PATCH /api/vehicles/{id}/ - Atualizar veículo parcial
    - DELETE /api/vehicles/{id}/ - Deletar veículo
    - GET /api/vehicles/available/ - Listar veículos disponíveis
    - GET /api/vehicles/with_tracker/ - Listar veículos com rastreador
    - POST /api/vehicles/{id}/activate/ - Ativar veículo
    - POST /api/vehicles/{id}/deactivate/ - Desativar veículo
    - POST /api/vehicles/{id}/change_status/ - Alterar status do veículo
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_active', 'ano', 'cor']
    search_fields = ['placa', 'modelo', 'chassi', 'renavam', 'cor']
    ordering_fields = ['placa', 'modelo', 'ano', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retorna queryset baseado no tipo de usuário.
        GR vê todos os veículos, Transportadora vê apenas seus próprios.
        """
        user = self.request.user
        
        if user.is_superuser or user.user_type == 'GR':
            return Vehicle.objects.all().select_related('transportadora')
        
        if user.user_type == 'TRANSPORTADORA':
            return Vehicle.objects.filter(
                transportadora=user
            ).select_related('transportadora')
        
        return Vehicle.objects.none()
    
    def get_serializer_class(self):
        """
        Retorna serializer apropriado baseado na action.
        """
        if self.action == 'list':
            return VehicleListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return VehicleCreateUpdateSerializer
        return VehicleSerializer
    
    def perform_create(self, serializer):
        """
        Ao criar, se usuário for Transportadora, define automaticamente
        como transportadora do veículo.
        """
        if self.request.user.user_type == 'TRANSPORTADORA':
            serializer.save(transportadora=self.request.user)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Listar apenas veículos disponíveis.
        GET /api/vehicles/available/
        """
        queryset = self.get_queryset().filter(
            status='DISPONIVEL',
            is_active=True
        )
        serializer = VehicleListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def with_tracker(self, request):
        """
        Listar apenas veículos com rastreador ativo.
        GET /api/vehicles/with_tracker/
        """
        queryset = self.get_queryset().filter(
            device__is_active=True,
            is_active=True
        )
        serializer = VehicleListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Ativar um veículo.
        POST /api/vehicles/{id}/activate/
        """
        vehicle = self.get_object()
        vehicle.is_active = True
        vehicle.save()
        
        serializer = self.get_serializer(vehicle)
        return Response(
            {
                'message': 'Veículo ativado com sucesso.',
                'vehicle': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desativar um veículo.
        POST /api/vehicles/{id}/deactivate/
        """
        vehicle = self.get_object()
        vehicle.is_active = False
        vehicle.save()
        
        serializer = self.get_serializer(vehicle)
        return Response(
            {
                'message': 'Veículo desativado com sucesso.',
                'vehicle': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """
        Alterar status do veículo.
        POST /api/vehicles/{id}/change_status/
        Body: {"status": "EM_VIAGEM"}
        """
        vehicle = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'Status é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar status
        valid_statuses = [choice[0] for choice in Vehicle.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {
                    'error': f'Status inválido. Opções: {", ".join(valid_statuses)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vehicle.status = new_status
        vehicle.save()
        
        serializer = self.get_serializer(vehicle)
        return Response(
            {
                'message': f'Status alterado para {new_status} com sucesso.',
                'vehicle': serializer.data
            },
            status=status.HTTP_200_OK
        )
