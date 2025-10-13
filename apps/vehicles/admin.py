"""
Configuração do Django Admin para Veículos.
"""
from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """
    Configuração do admin para o modelo Vehicle.
    """
    list_display = [
        'placa',
        'modelo',
        'ano',
        'cor',
        'status',
        'transportadora',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'is_active',
        'transportadora',
        'ano',
        'created_at'
    ]
    
    search_fields = [
        'placa',
        'modelo',
        'chassi',
        'renavam',
        'transportadora__company_name',
        'transportadora__username'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações da Transportadora', {
            'fields': ('transportadora',)
        }),
        ('Dados do Veículo', {
            'fields': ('placa', 'modelo', 'ano', 'cor', 'chassi', 'renavam')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Filtrar veículos baseado no tipo de usuário.
        GR vê todos os veículos, Transportadora vê apenas seus próprios.
        """
        qs = super().get_queryset(request)
        
        if request.user.is_superuser or (hasattr(request.user, 'user_type') and request.user.user_type == 'GR'):
            return qs
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'TRANSPORTADORA':
            return qs.filter(transportadora=request.user)
        
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """
        Ao salvar, se o usuário for Transportadora, definir automaticamente
        como transportadora do veículo.
        """
        if not change and hasattr(request.user, 'user_type') and request.user.user_type == 'TRANSPORTADORA':
            obj.transportadora = request.user
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        """
        Transportadora só pode editar seus próprios veículos.
        """
        if obj is None:
            return True
        
        if request.user.is_superuser or (hasattr(request.user, 'user_type') and request.user.user_type == 'GR'):
            return True
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'TRANSPORTADORA':
            return obj.transportadora == request.user
        
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Transportadora só pode deletar seus próprios veículos.
        """
        return self.has_change_permission(request, obj)
