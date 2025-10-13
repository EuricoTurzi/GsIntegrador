"""
Configuração do Django Admin para Sistema de Monitoramento.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import MonitoringSystem


@admin.register(MonitoringSystem)
class MonitoringSystemAdmin(admin.ModelAdmin):
    """
    Configuração do admin para o modelo MonitoringSystem.
    """
    list_display = [
        'identifier',
        'name',
        'status_badge',
        'driver_info',
        'vehicle_info',
        'route_info',
        'device_status_badge',
        'planned_start_date',
        'transportadora'
    ]
    
    list_filter = [
        'status',
        'is_active',
        'transportadora',
        'device_was_updated',
        'planned_start_date',
        'created_at'
    ]
    
    search_fields = [
        'identifier',
        'name',
        'driver__nome',
        'vehicle__placa',
        'route__name',
        'transportadora__company_name'
    ]
    
    readonly_fields = [
        'identifier',
        'device_validated_at',
        'device_was_updated',
        'duration_days',
        'device_status',
        'current_vehicle_position',
        'created_at',
        'updated_at',
        'created_by'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('identifier', 'transportadora', 'name', 'description')
        }),
        ('Componentes do Monitoramento', {
            'fields': ('route', 'driver', 'vehicle')
        }),
        ('Datas Planejadas', {
            'fields': ('planned_start_date', 'planned_end_date', 'duration_days')
        }),
        ('Datas Reais', {
            'fields': ('actual_start_date', 'actual_end_date'),
            'classes': ('collapse',)
        }),
        ('Validação do Dispositivo', {
            'fields': (
                'device_validated_at',
                'device_was_updated',
                'device_status',
                'current_vehicle_position'
            ),
            'classes': ('collapse',)
        }),
        ('Carga', {
            'fields': ('cargo_description', 'cargo_value'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Observações', {
            'fields': ('observations',),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'start_monitoring_action',
        'complete_monitoring_action',
        'cancel_monitoring_action',
        'activate_sm',
        'deactivate_sm'
    ]
    
    def status_badge(self, obj):
        """Exibe badge de status colorido."""
        colors = {
            'PLANEJADO': '#0066cc',
            'EM_ANDAMENTO': '#28a745',
            'CONCLUIDO': '#6c757d',
            'CANCELADO': '#dc3545'
        }
        color = colors.get(obj.status, '#000')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def driver_info(self, obj):
        """Exibe informações do motorista com link."""
        if obj.driver:
            url = reverse('admin:drivers_driver_change', args=[obj.driver.pk])
            return format_html('<a href="{}">{}</a>', url, obj.driver.nome)
        return '-'
    driver_info.short_description = 'Motorista'
    
    def vehicle_info(self, obj):
        """Exibe informações do veículo com link."""
        if obj.vehicle:
            url = reverse('admin:vehicles_vehicle_change', args=[obj.vehicle.pk])
            return format_html(
                '<a href="{}">{} - {}</a>',
                url,
                obj.vehicle.placa,
                obj.vehicle.modelo
            )
        return '-'
    vehicle_info.short_description = 'Veículo'
    
    def route_info(self, obj):
        """Exibe informações da rota com link."""
        if obj.route:
            url = reverse('admin:routes_route_change', args=[obj.route.pk])
            return format_html('<a href="{}">{}</a>', url, obj.route.name)
        return '-'
    route_info.short_description = 'Rota'
    
    def device_status_badge(self, obj):
        """Exibe status do dispositivo."""
        if obj.device_status:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Atualizado</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Desatualizado</span>'
            )
    device_status_badge.short_description = 'Status Dispositivo'
    
    def start_monitoring_action(self, request, queryset):
        """Action para iniciar monitoramentos."""
        count = 0
        for sm in queryset.filter(status='PLANEJADO'):
            sm.start_monitoring()
            count += 1
        
        self.message_user(request, f'{count} monitoramento(s) iniciado(s).')
    start_monitoring_action.short_description = 'Iniciar monitoramentos selecionados'
    
    def complete_monitoring_action(self, request, queryset):
        """Action para finalizar monitoramentos."""
        count = 0
        for sm in queryset.filter(status='EM_ANDAMENTO'):
            sm.complete_monitoring()
            count += 1
        
        self.message_user(request, f'{count} monitoramento(s) finalizado(s).')
    complete_monitoring_action.short_description = 'Finalizar monitoramentos selecionados'
    
    def cancel_monitoring_action(self, request, queryset):
        """Action para cancelar monitoramentos."""
        count = 0
        for sm in queryset.exclude(status__in=['CONCLUIDO', 'CANCELADO']):
            sm.cancel_monitoring(reason='Cancelado via admin')
            count += 1
        
        self.message_user(request, f'{count} monitoramento(s) cancelado(s).')
    cancel_monitoring_action.short_description = 'Cancelar monitoramentos selecionados'
    
    def activate_sm(self, request, queryset):
        """Action para ativar SMs."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} SM(s) ativado(s).')
    activate_sm.short_description = 'Ativar SMs selecionados'
    
    def deactivate_sm(self, request, queryset):
        """Action para desativar SMs."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} SM(s) desativado(s).')
    deactivate_sm.short_description = 'Desativar SMs selecionados'
    
    def get_queryset(self, request):
        """
        Filtrar SMs baseado no tipo de usuário.
        """
        qs = super().get_queryset(request).select_related(
            'transportadora',
            'route',
            'driver',
            'vehicle',
            'created_by'
        )
        
        if request.user.is_superuser or (hasattr(request.user, 'user_type') and request.user.user_type == 'GR'):
            return qs
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'TRANSPORTADORA':
            return qs.filter(transportadora=request.user)
        
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """
        Ao salvar, definir automaticamente a transportadora e criador.
        """
        if not change:
            if hasattr(request.user, 'user_type') and request.user.user_type == 'TRANSPORTADORA':
                obj.transportadora = request.user
            obj.created_by = request.user
        
        super().save_model(request, obj, form, change)
