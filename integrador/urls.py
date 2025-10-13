"""
URL configuration for integrador project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from core.views import dashboard_view

# Import template views
from apps.drivers import template_views as driver_views
from apps.vehicles import template_views as vehicle_views
from apps.devices import template_views as device_views
from apps.routes import template_views as route_views
from apps.monitoring import template_views as monitoring_views

# Temporary placeholder view
def coming_soon(request):
    from django.shortcuts import render
    return render(request, 'coming_soon.html')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Dashboard
    path('', dashboard_view, name='dashboard'),
    
    # Template views
    path('auth/', include('apps.authentication.urls')),
    
    # Drivers (Motoristas)
    path('drivers/', driver_views.driver_list, name='drivers-list'),
    path('drivers/create/', driver_views.driver_create, name='drivers-create'),
    path('drivers/<int:pk>/', driver_views.driver_detail, name='drivers-detail'),
    path('drivers/<int:pk>/edit/', driver_views.driver_edit, name='drivers-edit'),
    path('drivers/<int:pk>/activate/', driver_views.driver_activate, name='drivers-activate'),
    path('drivers/<int:pk>/deactivate/', driver_views.driver_deactivate, name='drivers-deactivate'),
    
    # Vehicles (Veículos)
    path('vehicles/', vehicle_views.vehicle_list, name='vehicles-list'),
    path('vehicles/create/', vehicle_views.vehicle_create, name='vehicles-create'),
    path('vehicles/<int:pk>/', vehicle_views.vehicle_detail, name='vehicles-detail'),
    path('vehicles/<int:pk>/edit/', vehicle_views.vehicle_edit, name='vehicles-edit'),
    path('vehicles/<int:pk>/change-status/', vehicle_views.vehicle_change_status, name='vehicles-change-status'),
    
    # Devices (Rastreadores)
    path('devices/', device_views.device_list, name='devices-list'),
    path('devices/create/', device_views.device_create, name='devices-create'),
    path('devices/<int:pk>/', device_views.device_detail, name='devices-detail'),
    path('devices/<int:pk>/edit/', device_views.device_edit, name='devices-edit'),
    path('devices/<int:pk>/sync/', device_views.device_sync, name='devices-sync'),
    path('devices/sync-all/', device_views.device_sync_all, name='devices-sync-all'),
    
    # Routes (Rotas)
    path('routes/', route_views.route_list, name='routes-list'),
    path('routes/create/', route_views.route_create, name='routes-create'),
    path('routes/<int:pk>/', route_views.route_detail, name='routes-detail'),
    path('routes/<int:pk>/edit/', route_views.route_edit, name='routes-edit'),
    path('routes/<int:pk>/delete/', route_views.route_delete, name='routes-delete'),
    
    # Monitoring (Sistema de Monitoramento)
    path('monitoring/', include('apps.monitoring.template_urls')),
    
    # Integrations - temporário
    path('integrations/', coming_soon, name='integrations-status'),
    
    # API endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/drivers/', include('apps.drivers.urls')),
    path('api/vehicles/', include('apps.vehicles.urls')),
    path('api/integrations/', include('apps.integrations.urls')),
    path('api/devices/', include('apps.devices.urls')),
    path('api/routes/', include('apps.routes.urls')),
    path('api/monitoring/', include('apps.monitoring.urls')),
]

# Servir arquivos de media e static em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
