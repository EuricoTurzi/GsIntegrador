"""
Views da API de rotas.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Route
from .serializers import (
    RouteSerializer,
    RouteListSerializer,
    RouteCreateUpdateSerializer,
    RouteCalculateSerializer,
    GeocodeSerializer,
    GeocodeResultSerializer,
    ReverseGeocodeSerializer,
    ReverseGeocodeResultSerializer
)
from .osm_service import geocode_address, reverse_geocode, OSMServiceError


class RouteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar rotas.
    
    Endpoints:
    - GET /api/routes/ - Listar rotas
    - POST /api/routes/ - Criar rota
    - GET /api/routes/{id}/ - Detalhe da rota
    - PUT /api/routes/{id}/ - Atualizar rota completa
    - PATCH /api/routes/{id}/ - Atualizar rota parcial
    - DELETE /api/routes/{id}/ - Deletar rota
    - GET /api/routes/active/ - Listar rotas ativas
    - POST /api/routes/{id}/calculate/ - Recalcular rota
    - POST /api/routes/{id}/activate/ - Ativar rota
    - POST /api/routes/{id}/deactivate/ - Desativar rota
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'transportadora']
    search_fields = [
        'name',
        'origin_name',
        'destination_name',
        'origin_address',
        'destination_address'
    ]
    ordering_fields = ['name', 'distance_meters', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retorna queryset baseado no tipo de usuário.
        GR vê todas as rotas, Transportadora vê apenas suas próprias.
        """
        user = self.request.user
        
        if user.is_superuser or user.user_type == 'GR':
            return Route.objects.all().select_related('transportadora')
        
        if user.user_type == 'TRANSPORTADORA':
            return Route.objects.filter(
                transportadora=user
            ).select_related('transportadora')
        
        return Route.objects.none()
    
    def get_serializer_class(self):
        """
        Retorna serializer apropriado baseado na action.
        """
        if self.action == 'list':
            return RouteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RouteCreateUpdateSerializer
        elif self.action == 'calculate':
            return RouteCalculateSerializer
        return RouteSerializer
    
    def perform_create(self, serializer):
        """
        Ao criar, se usuário for Transportadora, define automaticamente.
        """
        if self.request.user.user_type == 'TRANSPORTADORA':
            serializer.save(transportadora=self.request.user)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Listar apenas rotas ativas.
        GET /api/routes/active/
        """
        queryset = self.get_queryset().filter(is_active=True)
        serializer = RouteListSerializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """
        Recalcular a rota usando OpenStreetMap.
        POST /api/routes/{id}/calculate/
        """
        route = self.get_object()
        
        success = route.calculate_route()
        
        if success:
            serializer = RouteSerializer(route)
            return Response({
                'success': True,
                'message': 'Rota calculada com sucesso.',
                'route': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Erro ao calcular rota.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Ativar uma rota.
        POST /api/routes/{id}/activate/
        """
        route = self.get_object()
        route.is_active = True
        route.save()
        
        serializer = self.get_serializer(route)
        return Response({
            'message': 'Rota ativada com sucesso.',
            'route': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desativar uma rota.
        POST /api/routes/{id}/deactivate/
        """
        route = self.get_object()
        route.is_active = False
        route.save()
        
        serializer = self.get_serializer(route)
        return Response({
            'message': 'Rota desativada com sucesso.',
            'route': serializer.data
        }, status=status.HTTP_200_OK)


class GeocodeView(APIView):
    """
    Converte endereço em coordenadas geográficas.
    
    POST /api/routes/geocode/
    Body: {"address": "Avenida Paulista, 1578, São Paulo, SP"}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Geocodificar um endereço.
        """
        serializer = GeocodeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        address = serializer.validated_data['address']
        
        try:
            coordinates = geocode_address(address)
            
            if coordinates:
                return Response({
                    'success': True,
                    'address': address,
                    'latitude': coordinates[0],
                    'longitude': coordinates[1]
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Endereço não encontrado.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        except OSMServiceError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ReverseGeocodeView(APIView):
    """
    Converte coordenadas em endereço (reverse geocoding).
    
    POST /api/routes/reverse-geocode/
    Body: {"latitude": -23.5505, "longitude": -46.6333}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Reverse geocoding de coordenadas.
        """
        serializer = ReverseGeocodeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        latitude = serializer.validated_data['latitude']
        longitude = serializer.validated_data['longitude']
        
        try:
            address = reverse_geocode(latitude, longitude)
            
            if address:
                return Response({
                    'success': True,
                    'latitude': latitude,
                    'longitude': longitude,
                    'address': address
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Endereço não encontrado para essas coordenadas.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        except OSMServiceError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
