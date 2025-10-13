from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_view(request):
    """View para renderizar o dashboard principal"""
    
    # TODO: Buscar estatísticas reais do banco
    context = {
        'active_trips': 0,
        'in_progress_trips': 0,
        'total_drivers': 0,
        'active_drivers': 0,
        'total_vehicles': 0,
        'available_vehicles': 0,
        'vehicles_in_trip': 0,
        'active_devices': 0,
        'updated_devices': 0,
        'outdated_devices': 0,
        'recent_trips': [],
    }
    
    return render(request, 'dashboard.html', context)
