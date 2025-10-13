"""
Configuração do Django Admin para Dispositivos.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """
    Configuração do admin para o modelo Device.
    """
    list_display = [
        'suntech_device_id',
        'vehicle_info',
        'label',
        'status_badge',
        'minutes_since_update',
        'last_ignition_status',
        'is_active',
        'last_sync_at'
    ]
    
    list_filter = [
        'is_active',
        'last_ignition_status',
        'vehicle__transportadora',
        'created_at'
    ]
    
    search_fields = [
        'suntech_device_id',
        'suntech_vehicle_id',
        'imei',
        'label',
        'vehicle__placa',
        'vehicle__modelo',
        'vehicle__transportadora__company_name'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'last_sync_at',
        'is_updated_recently',
        'minutes_since_last_update',
        'odometer_km'
    ]
    
    fieldsets = (
        ('Veículo', {
            'fields': ('vehicle',)
        }),
        ('Dados Suntech', {
            'fields': (
                'suntech_device_id',
                'suntech_vehicle_id',
                'imei',
                'label'
            )
        }),
        ('Última Posição', {
            'fields': (
                'last_position_date',
                'last_system_date',
                'last_latitude',
                'last_longitude',
                'last_address',
                'last_speed',
                'last_ignition_status',
                'odometer',
                'odometer_km'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': (
                'is_active',
                'is_updated_recently',
                'minutes_since_last_update'
            )
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': ('created_at', 'updated_at', 'last_sync_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['sync_devices_with_suntech', 'activate_devices', 'deactivate_devices']
    
    def vehicle_info(self, obj):
        """Exibe informações do veículo."""
        return f"{obj.vehicle.placa} - {obj.vehicle.modelo}"
    vehicle_info.short_description = 'Veículo'
    
    def status_badge(self, obj):
        """Exibe badge de status colorido."""
        if obj.is_updated_recently:
            color = 'green'
            text = '✓ Atualizado'
        else:
            color = 'red'
            text = '✗ Desatualizado'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            text
        )
    status_badge.short_description = 'Status'
    
    def minutes_since_update(self, obj):
        """Exibe minutos desde última atualização."""
        minutes = obj.minutes_since_last_update
        if minutes is None:
            return '-'
        
        if minutes < 30:
            color = 'green'
        elif minutes < 60:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{} min</span>',
            color,
            minutes
        )
    minutes_since_update.short_description = 'Últ. Atualização'
    
    def sync_devices_with_suntech(self, request, queryset):
        """Action para sincronizar dispositivos selecionados com Suntech."""
        success_count = 0
        
        for device in queryset:
            if device.sync_with_suntech():
                success_count += 1
        
        self.message_user(
            request,
            f'{success_count} dispositivo(s) sincronizado(s) com sucesso.'
        )
    sync_devices_with_suntech.short_description = 'Sincronizar com Suntech'
    
    def activate_devices(self, request, queryset):
        """Action para ativar dispositivos."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} dispositivo(s) ativado(s).')
    activate_devices.short_description = 'Ativar dispositivos selecionados'
    
    def deactivate_devices(self, request, queryset):
        """Action para desativar dispositivos."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} dispositivo(s) desativado(s).')
    deactivate_devices.short_description = 'Desativar dispositivos selecionados'
    
    def get_queryset(self, request):
        """
        Filtrar dispositivos baseado no tipo de usuário.
        """
        qs = super().get_queryset(request).select_related('vehicle', 'vehicle__transportadora')
        
        if request.user.is_superuser or (hasattr(request.user, 'user_type') and request.user.user_type == 'GR'):
            return qs
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'TRANSPORTADORA':
            return qs.filter(vehicle__transportadora=request.user)
        
        return qs.none()
