"""
URLs para Sistema de Monitoramento (Template Views)
"""
from django.urls import path
from apps.monitoring import template_views

urlpatterns = [
    # Lista e dashboard
    path('', template_views.monitoring_list, name='monitoring_list'),
    
    # CRUD
    path('<int:pk>/', template_views.monitoring_detail, name='monitoring_detail'),
    path('create/', template_views.monitoring_create, name='monitoring_create'),
    path('<int:pk>/edit/', template_views.monitoring_edit, name='monitoring_edit'),
    path('<int:pk>/delete/', template_views.monitoring_delete, name='monitoring_delete'),
    
    # Ações de controle
    path('<int:pk>/start/', template_views.monitoring_start, name='monitoring_start'),
    path('<int:pk>/complete/', template_views.monitoring_complete, name='monitoring_complete'),
    path('<int:pk>/cancel/', template_views.monitoring_cancel, name='monitoring_cancel'),
    
    # Mapa e API
    path('map/', template_views.monitoring_map, name='monitoring_map'),
    path('<int:pk>/refresh-position/', template_views.monitoring_refresh_position, name='monitoring_refresh_position'),
]
