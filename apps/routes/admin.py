"""
Configuração do Django Admin para Rotas.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    """
    Configuração do admin para o modelo Route.
    """
    list_display = [
        'name',
        'origin_destination',
        'distance_display',
        'duration_display',
        'transportadora',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'transportadora',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'origin_name',
        'destination_name',
        'origin_address',
        'destination_address',
        'transportadora__company_name'
    ]
    
    readonly_fields = [
        'distance_km',
        'estimated_duration_hours',
        'estimated_duration_formatted',
        'created_at',
        'updated_at',
        'last_calculated_at'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('transportadora', 'name', 'description', 'is_active')
        }),
        ('Origem (Ponto A)', {
            'fields': (
                'origin_name',
                'origin_address',
                'origin_latitude',
                'origin_longitude'
            )
        }),
        ('Destino (Ponto B)', {
            'fields': (
                'destination_name',
                'destination_address',
                'destination_latitude',
                'destination_longitude'
            )
        }),
        ('Dados Calculados', {
            'fields': (
                'distance_meters',
                'distance_km',
                'estimated_duration_seconds',
                'estimated_duration_hours',
                'estimated_duration_formatted',
                'last_calculated_at'
            ),
            'classes': ('collapse',)
        }),
        ('Geometria da Rota', {
            'fields': ('route_geometry',),
            'classes': ('collapse',)
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
    
    actions = ['calculate_routes', 'activate_routes', 'deactivate_routes']
    
    def origin_destination(self, obj):
        """Exibe origem e destino de forma compacta."""
        return f"{obj.origin_name} → {obj.destination_name}"
    origin_destination.short_description = 'Origem → Destino'
    
    def distance_display(self, obj):
        """Exibe a distância formatada."""
        if obj.distance_km:
            return format_html(
                '<span style="font-weight: bold;">{} km</span>',
                obj.distance_km
            )
        return '-'
    distance_display.short_description = 'Distância'
    
    def duration_display(self, obj):
        """Exibe a duração formatada."""
        if obj.estimated_duration_formatted:
            return format_html(
                '<span style="color: #0066cc;">{}</span>',
                obj.estimated_duration_formatted
            )
        return '-'
    duration_display.short_description = 'Duração'
    
    def calculate_routes(self, request, queryset):
        """Action para calcular/recalcular rotas selecionadas."""
        success_count = 0
        
        for route in queryset:
            if route.calculate_route():
                success_count += 1
        
        self.message_user(
            request,
            f'{success_count} rota(s) calculada(s) com sucesso.'
        )
    calculate_routes.short_description = 'Calcular rotas com OpenStreetMap'
    
    def activate_routes(self, request, queryset):
        """Action para ativar rotas."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} rota(s) ativada(s).')
    activate_routes.short_description = 'Ativar rotas selecionadas'
    
    def deactivate_routes(self, request, queryset):
        """Action para desativar rotas."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} rota(s) desativada(s).')
    deactivate_routes.short_description = 'Desativar rotas selecionadas'
    
    def get_queryset(self, request):
        """
        Filtrar rotas baseado no tipo de usuário.
        """
        qs = super().get_queryset(request).select_related('transportadora')
        
        if request.user.is_superuser or (hasattr(request.user, 'user_type') and request.user.user_type == 'GR'):
            return qs
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'TRANSPORTADORA':
            return qs.filter(transportadora=request.user)
        
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """
        Ao salvar, se o usuário for Transportadora, definir automaticamente.
        Se dados mudaram, recalcular rota.
        """
        if not change and hasattr(request.user, 'user_type') and request.user.user_type == 'TRANSPORTADORA':
            obj.transportadora = request.user
        
        super().save_model(request, obj, form, change)
        
        # Calcular rota se for nova ou se coordenadas mudaram
        if not change or any(field in form.changed_data for field in [
            'origin_latitude', 'origin_longitude',
            'destination_latitude', 'destination_longitude'
        ]):
            obj.calculate_route()
