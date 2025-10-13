from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Driver
from .serializers import (
    DriverSerializer,
    DriverListSerializer,
    DriverCreateUpdateSerializer
)


class DriverViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de motoristas.
    
    Endpoints:
    - GET    /api/drivers/          - Listar motoristas
    - POST   /api/drivers/          - Criar motorista
    - GET    /api/drivers/{id}/     - Detalhes do motorista
    - PUT    /api/drivers/{id}/     - Atualizar motorista (completo)
    - PATCH  /api/drivers/{id}/     - Atualizar motorista (parcial)
    - DELETE /api/drivers/{id}/     - Deletar motorista
    - GET    /api/drivers/active/   - Listar apenas motoristas ativos
    - POST   /api/drivers/{id}/activate/   - Ativar motorista
    - POST   /api/drivers/{id}/deactivate/ - Desativar motorista
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtros
    filterset_fields = ['is_active', 'tipo_de_veiculo']
    search_fields = ['nome', 'cpf', 'cnh', 'rg', 'telefone', 'email']
    ordering_fields = ['nome', 'created_at', 'cpf']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retorna motoristas baseado no tipo de usuário:
        - GR: vê todos os motoristas
        - Transportadora: vê apenas seus motoristas
        """
        user = self.request.user
        
        if user.is_staff or user.is_gr:
            return Driver.objects.all()
        
        if user.is_transportadora:
            return Driver.objects.filter(transportadora=user)
        
        return Driver.objects.none()
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na action"""
        if self.action == 'list':
            return DriverListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DriverCreateUpdateSerializer
        return DriverSerializer
    
    def perform_create(self, serializer):
        """Atribui automaticamente a transportadora ao criar motorista"""
        user = self.request.user
        
        # GR pode especificar a transportadora, se não, usa a própria conta
        if user.is_gr or user.is_staff:
            transportadora = serializer.validated_data.get('transportadora', user)
        else:
            transportadora = user
        
        serializer.save(transportadora=transportadora)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        GET /api/drivers/active/
        
        Retorna apenas motoristas ativos
        """
        queryset = self.get_queryset().filter(is_active=True)
        serializer = DriverListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        POST /api/drivers/{id}/activate/
        
        Ativa um motorista
        """
        driver = self.get_object()
        driver.is_active = True
        driver.save()
        
        serializer = self.get_serializer(driver)
        return Response({
            'message': f'Motorista {driver.nome} ativado com sucesso!',
            'driver': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        POST /api/drivers/{id}/deactivate/
        
        Desativa um motorista
        """
        driver = self.get_object()
        driver.is_active = False
        driver.save()
        
        serializer = self.get_serializer(driver)
        return Response({
            'message': f'Motorista {driver.nome} desativado com sucesso!',
            'driver': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """DELETE personalizado com mensagem"""
        instance = self.get_object()
        nome = instance.nome
        self.perform_destroy(instance)
        return Response({
            'message': f'Motorista {nome} deletado com sucesso!'
        }, status=status.HTTP_200_OK)
