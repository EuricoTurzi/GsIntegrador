"""
URLs para a aplicação de integrações.
"""
from django.urls import path
from .views import (
    SuntechVehiclesListView,
    SuntechVehicleDetailView,
    SuntechVehiclePositionsView,
    SuntechDeviceStatusView,
    SuntechDevicePositionView,
    SuntechSendCommandView,
    SuntechClearCacheView
)

urlpatterns = [
    # Listar todos os veículos da API Suntech
    path('suntech/vehicles/', SuntechVehiclesListView.as_view(), name='suntech-vehicles-list'),
    
    # Detalhes de um veículo específico
    path('suntech/vehicles/<int:device_id>/', SuntechVehicleDetailView.as_view(), name='suntech-vehicle-detail'),
    
    # Histórico de posições
    path('suntech/vehicles/<int:vehicle_id>/positions/', SuntechVehiclePositionsView.as_view(), name='suntech-vehicle-positions'),
    
    # Status de atualização do dispositivo
    path('suntech/devices/<int:device_id>/status/', SuntechDeviceStatusView.as_view(), name='suntech-device-status'),
    
    # Última posição do dispositivo
    path('suntech/devices/<int:device_id>/position/', SuntechDevicePositionView.as_view(), name='suntech-device-position'),
    
    # Enviar comando para veículo
    path('suntech/vehicles/<int:vehicle_id>/command/', SuntechSendCommandView.as_view(), name='suntech-send-command'),
    
    # Limpar cache
    path('suntech/cache/clear/', SuntechClearCacheView.as_view(), name='suntech-clear-cache'),
]
