from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    """Admin para o modelo Driver"""
    
    list_display = (
        'nome_curto', 'cpf', 'cnh', 'tipo_de_veiculo',
        'transportadora', 'is_active', 'created_at'
    )
    
    list_filter = (
        'is_active', 'tipo_de_veiculo', 'transportadora', 'created_at'
    )
    
    search_fields = (
        'nome', 'cpf', 'cnh', 'rg', 'nome_do_pai', 'nome_da_mae',
        'transportadora__company_name', 'telefone', 'email'
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Transportadora'), {
            'fields': ('transportadora',)
        }),
        (_('Dados Pessoais'), {
            'fields': ('nome', 'cpf', 'rg', 'cnh', 'data_nascimento')
        }),
        (_('Filiação'), {
            'fields': ('nome_do_pai', 'nome_da_mae')
        }),
        (_('Tipo de Veículo'), {
            'fields': ('tipo_de_veiculo',)
        }),
        (_('Contato'), {
            'fields': ('telefone', 'email', 'endereco')
        }),
        (_('Status e Observações'), {
            'fields': ('is_active', 'observacoes')
        }),
        (_('Informações do Sistema'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        """Filtrar motoristas por transportadora"""
        qs = super().get_queryset(request)
        
        # Superuser e GR veem todos
        if request.user.is_superuser or request.user.is_gr:
            return qs
        
        # Transportadora vê apenas seus motoristas
        if request.user.is_transportadora:
            return qs.filter(transportadora=request.user)
        
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """Auto-atribuir transportadora se não for superuser/GR"""
        if not change and not request.user.is_superuser and not request.user.is_gr:
            obj.transportadora = request.user
        super().save_model(request, obj, form, change)
