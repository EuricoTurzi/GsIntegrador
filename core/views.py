from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.drivers.models import Driver
from apps.vehicles.models import Vehicle
from apps.devices.models import Device
from apps.monitoring.models import MonitoringSystem


@login_required
def dashboard_view(request):
    """View para renderizar o dashboard principal"""
    
    # Determinar permissões baseado no tipo de usuário
    if request.user.is_superuser or request.user.user_type == 'GR':
        # GR vê todos os dados
        drivers = Driver.objects.all()
        vehicles = Vehicle.objects.all()
        devices = Device.objects.all()
        trips = MonitoringSystem.objects.all()
    else:
        # Transportadora vê apenas seus dados
        drivers = Driver.objects.filter(transportadora=request.user)
        vehicles = Vehicle.objects.filter(transportadora=request.user)
        devices = Device.objects.filter(transportadora=request.user)
        trips = MonitoringSystem.objects.filter(transportadora=request.user)
    
    # Buscar viagens recentes (últimas 5, ordenadas por data de criação)
    recent_trips = trips.select_related(
        'route', 'driver', 'vehicle'
    ).order_by('-created_at')[:5]
    
    # Calcular estatísticas
    context = {
        'active_trips': trips.filter(status__in=['PLANEJADO', 'EM_ANDAMENTO']).count(),
        'in_progress_trips': trips.filter(status='EM_ANDAMENTO').count(),
        'total_drivers': drivers.count(),
        'active_drivers': drivers.filter(is_active=True).count(),
        'total_vehicles': vehicles.count(),
        'available_vehicles': vehicles.filter(status='DISPONIVEL').count(),
        'vehicles_in_trip': vehicles.filter(status='EM_VIAGEM').count(),
        'active_devices': devices.filter(is_active=True).count(),
        'updated_devices': devices.filter(is_active=True).count(),  # TODO: refinar lógica
        'outdated_devices': devices.filter(is_active=False).count(),
        'recent_trips': recent_trips,
    }
    
    return render(request, 'dashboard.html', context)
