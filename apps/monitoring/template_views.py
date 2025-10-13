"""
Views baseadas em templates para Sistema de Monitoramento (SM)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
import json

from apps.monitoring.models import MonitoringSystem
from apps.drivers.models import Driver
from apps.vehicles.models import Vehicle
from apps.devices.models import Device
from apps.routes.models import Route
from apps.authentication.models import User


@login_required
def monitoring_list(request):
    """Dashboard de viagens/monitoramentos"""
    
    # Filtrar por transportadora se não for admin/GR
    if request.user.is_superuser or request.user.user_type == 'GR':
        trips = MonitoringSystem.objects.all()
        transportadoras = User.objects.filter(user_type='TRANSPORTADORA', is_active=True)
    else:
        trips = MonitoringSystem.objects.filter(transportadora=request.user)
        transportadoras = None
    
    # Aplicar filtros
    status_filter = request.GET.get('status', '')
    driver_filter = request.GET.get('driver', '')
    vehicle_filter = request.GET.get('vehicle', '')
    transportadora_filter = request.GET.get('transportadora', '')
    search = request.GET.get('search', '')
    
    if status_filter:
        trips = trips.filter(status=status_filter)
    
    if driver_filter:
        trips = trips.filter(driver_id=driver_filter)
    
    if vehicle_filter:
        trips = trips.filter(vehicle_id=vehicle_filter)
    
    if transportadora_filter:
        trips = trips.filter(transportadora_id=transportadora_filter)
    
    if search:
        trips = trips.filter(
            Q(identifier__icontains=search) |
            Q(name__icontains=search) |
            Q(driver__name__icontains=search) |
            Q(vehicle__plate__icontains=search)
        )
    
    # Ordenar
    trips = trips.select_related(
        'transportadora', 'route', 'driver', 'vehicle', 'vehicle__device'
    ).order_by('-created_at')
    
    # Estatísticas
    today = timezone.now().date()
    stats = {
        'total': trips.count(),
        'em_andamento': trips.filter(status='EM_ANDAMENTO').count(),
        'planejadas': trips.filter(status='PLANEJADO').count(),
        'concluidas_hoje': trips.filter(
            status='CONCLUIDO',
            actual_end_date__date=today
        ).count(),
        'canceladas': trips.filter(status='CANCELADO').count(),
    }
    
    # Viagens ativas (para o mapa)
    active_trips = trips.filter(status='EM_ANDAMENTO')
    
    # Preparar dados para o mapa
    map_data = []
    for trip in active_trips:
        position = trip.current_vehicle_position
        if position:
            map_data.append({
                'id': trip.id,
                'identifier': trip.identifier,
                'name': trip.name,
                'driver': trip.driver.nome,
                'vehicle': trip.vehicle.placa,
                'latitude': position['latitude'],
                'longitude': position['longitude'],
                'speed': position['speed'],
                'last_update': position['last_update'].isoformat() if position['last_update'] else None,
            })
    
    # Listas para filtros
    if request.user.is_superuser or request.user.user_type == 'GR':
        drivers = Driver.objects.filter(is_active=True)
        vehicles = Vehicle.objects.filter(is_active=True)
    else:
        drivers = Driver.objects.filter(transportadora=request.user, is_active=True)
        vehicles = Vehicle.objects.filter(transportadora=request.user, is_active=True)
    
    context = {
        'trips': trips[:50],  # Limitar a 50 para performance
        'stats': stats,
        'map_data': json.dumps(map_data),
        'drivers': drivers,
        'vehicles': vehicles,
        'transportadoras': transportadoras,
        'filters': {
            'status': status_filter,
            'driver': driver_filter,
            'vehicle': vehicle_filter,
            'transportadora': transportadora_filter,
            'search': search,
        },
        'status_choices': MonitoringSystem.STATUS_CHOICES,
    }
    
    return render(request, 'monitoring/monitoring_list.html', context)


@login_required
def monitoring_detail(request, pk):
    """Detalhes da viagem/monitoramento com tracking"""
    
    # Verificar permissões
    if request.user.is_superuser or request.user.user_type == 'GR':
        trip = get_object_or_404(MonitoringSystem, pk=pk)
    else:
        trip = get_object_or_404(MonitoringSystem, pk=pk, transportadora=request.user)
    
    # Posição atual do veículo
    current_position = trip.current_vehicle_position
    
    # Preparar coordenadas para JavaScript
    if current_position:
        current_lat = current_position['latitude']
        current_lng = current_position['longitude']
    else:
        current_lat = float(trip.route.origin_latitude) if trip.route.origin_latitude else 0
        current_lng = float(trip.route.origin_longitude) if trip.route.origin_longitude else 0
    
    # Coordenadas da rota
    origin_lat = float(trip.route.origin_latitude) if trip.route.origin_latitude else 0
    origin_lng = float(trip.route.origin_longitude) if trip.route.origin_longitude else 0
    dest_lat = float(trip.route.destination_latitude) if trip.route.destination_latitude else 0
    dest_lng = float(trip.route.destination_longitude) if trip.route.destination_longitude else 0
    
    context = {
        'trip': trip,
        'current_position': current_position,
        'current_lat': current_lat,
        'current_lng': current_lng,
        'origin_lat': origin_lat,
        'origin_lng': origin_lng,
        'dest_lat': dest_lat,
        'dest_lng': dest_lng,
    }
    
    return render(request, 'monitoring/monitoring_detail.html', context)


@login_required
def monitoring_create(request):
    """Criar nova viagem/monitoramento"""
    
    # Listas para selects
    if request.user.is_superuser or request.user.user_type == 'GR':
        transportadoras = User.objects.filter(user_type='TRANSPORTADORA', is_active=True)
        # Por padrão, pegar primeira transportadora ou vazio
        selected_transp_id = request.GET.get('transportadora')
        if selected_transp_id:
            drivers = Driver.objects.filter(transportadora_id=selected_transp_id, is_active=True)
            vehicles = Vehicle.objects.filter(transportadora_id=selected_transp_id, is_active=True, status='DISPONIVEL')
            routes = Route.objects.filter(transportadora_id=selected_transp_id, is_active=True)
        elif transportadoras.exists():
            # Selecionar primeira transportadora por padrão
            first_transp = transportadoras.first()
            drivers = Driver.objects.filter(transportadora=first_transp, is_active=True)
            vehicles = Vehicle.objects.filter(transportadora=first_transp, is_active=True, status='DISPONIVEL')
            routes = Route.objects.filter(transportadora=first_transp, is_active=True)
        else:
            drivers = Driver.objects.none()
            vehicles = Vehicle.objects.none()
            routes = Route.objects.none()
    else:
        transportadoras = None
        drivers = Driver.objects.filter(transportadora=request.user, is_active=True)
        vehicles = Vehicle.objects.filter(transportadora=request.user, is_active=True, status='DISPONIVEL')
        routes = Route.objects.filter(transportadora=request.user, is_active=True)
    
    if request.method == 'POST':
        try:
            # Coletar dados do formulário
            transportadora_id = request.POST.get('transportadora')
            route_id = request.POST.get('route')
            driver_id = request.POST.get('driver')
            vehicle_id = request.POST.get('vehicle')
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            planned_start_date = request.POST.get('planned_start_date')
            planned_end_date = request.POST.get('planned_end_date')
            cargo_description = request.POST.get('cargo_description', '')
            cargo_value = request.POST.get('cargo_value', None)
            observations = request.POST.get('observations', '')
            
            # Validações
            if request.user.is_superuser or request.user.user_type == 'GR':
                if not transportadora_id:
                    messages.error(request, 'Selecione uma transportadora!')
                    raise ValueError('Transportadora obrigatória')
                transportadora = User.objects.get(pk=transportadora_id)
            else:
                transportadora = request.user
            
            route = Route.objects.get(pk=route_id)
            driver = Driver.objects.get(pk=driver_id)
            vehicle = Vehicle.objects.get(pk=vehicle_id)
            
            # Criar o monitoramento
            trip = MonitoringSystem.objects.create(
                transportadora=transportadora,
                route=route,
                driver=driver,
                vehicle=vehicle,
                name=name,
                description=description,
                planned_start_date=planned_start_date,
                planned_end_date=planned_end_date,
                cargo_description=cargo_description,
                cargo_value=cargo_value if cargo_value else None,
                observations=observations,
                created_by=request.user,
            )
            
            messages.success(request, f'Viagem "{trip.identifier}" criada com sucesso!')
            return redirect('monitoring_detail', pk=trip.pk)
            
        except Exception as e:
            messages.error(request, f'Erro ao criar viagem: {str(e)}')
    
    context = {
        'transportadoras': transportadoras,
        'drivers': drivers,
        'vehicles': vehicles,
        'routes': routes,
    }
    
    return render(request, 'monitoring/monitoring_form.html', context)


@login_required
def monitoring_edit(request, pk):
    """Editar viagem/monitoramento"""
    
    # Verificar permissões
    if request.user.is_superuser or request.user.user_type == 'GR':
        trip = get_object_or_404(MonitoringSystem, pk=pk)
        transportadoras = User.objects.filter(user_type='TRANSPORTADORA', is_active=True)
        drivers = Driver.objects.filter(is_active=True)
        vehicles = Vehicle.objects.filter(is_active=True)
        routes = Route.objects.filter(is_active=True)
    else:
        trip = get_object_or_404(MonitoringSystem, pk=pk, transportadora=request.user)
        transportadoras = None
        drivers = Driver.objects.filter(transportadora=request.user, is_active=True)
        vehicles = Vehicle.objects.filter(transportadora=request.user, is_active=True)
        routes = Route.objects.filter(transportadora=request.user, is_active=True)
    
    if request.method == 'POST':
        try:
            # Atualizar campos
            if transportadoras:
                trip.transportadora = User.objects.get(pk=request.POST.get('transportadora'))
            
            trip.route = Route.objects.get(pk=request.POST.get('route'))
            trip.driver = Driver.objects.get(pk=request.POST.get('driver'))
            trip.vehicle = Vehicle.objects.get(pk=request.POST.get('vehicle'))
            trip.name = request.POST.get('name')
            trip.description = request.POST.get('description', '')
            trip.planned_start_date = request.POST.get('planned_start_date')
            trip.planned_end_date = request.POST.get('planned_end_date')
            trip.cargo_description = request.POST.get('cargo_description', '')
            cargo_value = request.POST.get('cargo_value', None)
            trip.cargo_value = cargo_value if cargo_value else None
            trip.observations = request.POST.get('observations', '')
            trip.is_active = 'is_active' in request.POST
            
            trip.save()
            
            messages.success(request, 'Viagem atualizada com sucesso!')
            return redirect('monitoring_detail', pk=trip.pk)
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar viagem: {str(e)}')
    
    context = {
        'trip': trip,
        'transportadoras': transportadoras,
        'drivers': drivers,
        'vehicles': vehicles,
        'routes': routes,
        'is_edit': True,
    }
    
    return render(request, 'monitoring/monitoring_form.html', context)


@login_required
def monitoring_delete(request, pk):
    """Deletar viagem/monitoramento"""
    
    # Verificar permissões
    if request.user.is_superuser or request.user.user_type == 'GR':
        trip = get_object_or_404(MonitoringSystem, pk=pk)
    else:
        trip = get_object_or_404(MonitoringSystem, pk=pk, transportadora=request.user)
    
    if request.method == 'POST':
        identifier = trip.identifier
        trip.delete()
        messages.success(request, f'Viagem "{identifier}" deletada com sucesso!')
        return redirect('monitoring_list')
    
    context = {'trip': trip}
    return render(request, 'monitoring/monitoring_confirm_delete.html', context)


@login_required
def monitoring_start(request, pk):
    """Iniciar viagem"""
    
    if request.user.is_superuser or request.user.user_type == 'GR':
        trip = get_object_or_404(MonitoringSystem, pk=pk)
    else:
        trip = get_object_or_404(MonitoringSystem, pk=pk, transportadora=request.user)
    
    if request.method == 'POST':
        try:
            trip.start_monitoring()
            messages.success(request, f'Viagem "{trip.identifier}" iniciada!')
            return redirect('monitoring_detail', pk=trip.pk)
        except Exception as e:
            messages.error(request, f'Erro ao iniciar viagem: {str(e)}')
            return redirect('monitoring_detail', pk=trip.pk)
    
    return redirect('monitoring_detail', pk=trip.pk)


@login_required
def monitoring_complete(request, pk):
    """Finalizar viagem"""
    
    if request.user.is_superuser or request.user.user_type == 'GR':
        trip = get_object_or_404(MonitoringSystem, pk=pk)
    else:
        trip = get_object_or_404(MonitoringSystem, pk=pk, transportadora=request.user)
    
    if request.method == 'POST':
        try:
            trip.complete_monitoring()
            messages.success(request, f'Viagem "{trip.identifier}" concluída!')
            return redirect('monitoring_detail', pk=trip.pk)
        except Exception as e:
            messages.error(request, f'Erro ao finalizar viagem: {str(e)}')
            return redirect('monitoring_detail', pk=trip.pk)
    
    return redirect('monitoring_detail', pk=trip.pk)


@login_required
def monitoring_cancel(request, pk):
    """Cancelar viagem"""
    
    if request.user.is_superuser or request.user.user_type == 'GR':
        trip = get_object_or_404(MonitoringSystem, pk=pk)
    else:
        trip = get_object_or_404(MonitoringSystem, pk=pk, transportadora=request.user)
    
    if request.method == 'POST':
        try:
            reason = request.POST.get('reason', '')
            trip.cancel_monitoring(reason=reason)
            messages.success(request, f'Viagem "{trip.identifier}" cancelada!')
            return redirect('monitoring_detail', pk=trip.pk)
        except Exception as e:
            messages.error(request, f'Erro ao cancelar viagem: {str(e)}')
            return redirect('monitoring_detail', pk=trip.pk)
    
    return redirect('monitoring_detail', pk=trip.pk)


@login_required
def monitoring_map(request):
    """Mapa full-screen com todas as viagens ativas"""
    
    # Filtrar viagens em andamento
    if request.user.is_superuser or request.user.user_type == 'GR':
        trips = MonitoringSystem.objects.filter(status='EM_ANDAMENTO')
    else:
        trips = MonitoringSystem.objects.filter(
            transportadora=request.user,
            status='EM_ANDAMENTO'
        )
    
    trips = trips.select_related('driver', 'vehicle', 'vehicle__device', 'route')
    
    # Preparar dados para o mapa
    map_data = []
    for trip in trips:
        position = trip.current_vehicle_position
        if position:
            map_data.append({
                'id': trip.id,
                'identifier': trip.identifier,
                'name': trip.name,
                'driver': trip.driver.nome,
                'vehicle': trip.vehicle.placa,
                'latitude': position['latitude'],
                'longitude': position['longitude'],
                'speed': position['speed'],
                'last_update': position['last_update'].isoformat() if position['last_update'] else None,
            })
    
    context = {
        'map_data': json.dumps(map_data),
        'trips_count': len(map_data),
    }
    
    return render(request, 'monitoring/monitoring_map.html', context)


@login_required
def monitoring_refresh_position(request, pk):
    """API endpoint para atualizar posição do veículo (AJAX)"""
    
    if request.user.is_superuser or request.user.user_type == 'GR':
        trip = get_object_or_404(MonitoringSystem, pk=pk)
    else:
        trip = get_object_or_404(MonitoringSystem, pk=pk, transportadora=request.user)
    
    position = trip.current_vehicle_position
    
    if position:
        return JsonResponse({
            'success': True,
            'position': position,
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Posição não disponível'
        }, status=404)
