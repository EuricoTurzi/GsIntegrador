"""
Views para renderizar templates HTML de Vehicles
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Vehicle
from apps.devices.models import Device


@login_required
def vehicle_list(request):
    """Lista de veículos com filtros e paginação"""
    # GR pode ver todos os veículos, Transportadora vê apenas os seus
    if request.user.is_superuser or request.user.user_type == 'GR':
        vehicles = Vehicle.objects.all().select_related('transportadora').prefetch_related('device')
    else:
        vehicles = Vehicle.objects.filter(transportadora=request.user).select_related('transportadora').prefetch_related('device')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        vehicles = vehicles.filter(
            Q(placa__icontains=search) |
            Q(modelo__icontains=search) |
            Q(renavam__icontains=search)
        )
    
    # Filters
    status = request.GET.get('status', '')
    if status:
        vehicles = vehicles.filter(status=status)
    
    device_status = request.GET.get('device_status', '')
    if device_status == 'with':
        vehicles = vehicles.filter(device__isnull=False)
    elif device_status == 'without':
        vehicles = vehicles.filter(device__isnull=True)
    
    # Sort
    sort = request.GET.get('sort', '-created_at')
    vehicles = vehicles.order_by(sort)
    
    # Stats
    all_vehicles = Vehicle.objects.filter(transportadora=request.user)
    stats = {
        'total': all_vehicles.count(),
        'available': all_vehicles.filter(status='DISPONIVEL').count(),
        'on_trip': all_vehicles.filter(status='EM_VIAGEM').count(),
        'maintenance': all_vehicles.filter(status='MANUTENCAO').count(),
    }
    
    # Pagination
    paginator = Paginator(vehicles, 20)
    page = request.GET.get('page', 1)
    vehicles = paginator.get_page(page)
    
    context = {
        'vehicles': vehicles,
        'stats': stats,
    }
    return render(request, 'vehicles/vehicle_list.html', context)


@login_required
def vehicle_detail(request, pk):
    """Detalhes de um veículo"""
    # GR pode ver qualquer veículo, Transportadora apenas os seus
    if request.user.is_superuser or request.user.user_type == 'GR':
        vehicle = get_object_or_404(Vehicle, pk=pk)
    else:
        vehicle = get_object_or_404(Vehicle, pk=pk, transportadora=request.user)
    
    # Stats
    stats = {
        'total_trips': 0,  # TODO: contar viagens
        'completed_trips': 0,
        'active_trips': 0,
        'total_distance': 0,
    }
    
    # Recent trips
    recent_trips = []  # TODO: buscar viagens recentes
    
    context = {
        'vehicle': vehicle,
        'stats': stats,
        'recent_trips': recent_trips,
    }
    return render(request, 'vehicles/vehicle_detail.html', context)


@login_required
def vehicle_create(request):
    """Criar novo veículo"""
    if request.method == 'POST':
        try:
            # Determinar a transportadora
            from apps.authentication.models import User
            
            if request.user.is_superuser or request.user.user_type == 'GR':
                # GR precisa selecionar uma transportadora
                transportadora_id = request.POST.get('transportadora')
                if not transportadora_id:
                    messages.error(request, 'Você precisa selecionar uma transportadora!')
                    # Recarregar formulário com dados preenchidos
                    available_devices = Device.objects.filter(vehicle__isnull=True)
                    transportadoras = User.objects.filter(user_type='TRANSPORTADORA')
                    context = {
                        'vehicle': None,
                        'available_devices': available_devices,
                        'transportadoras': transportadoras,
                        'form_data': request.POST,
                    }
                    return render(request, 'vehicles/vehicle_form.html', context)
                
                try:
                    transportadora = User.objects.get(pk=transportadora_id, user_type='TRANSPORTADORA')
                except User.DoesNotExist:
                    messages.error(request, 'Transportadora não encontrada!')
                    return redirect('vehicles-create')
            else:
                # Transportadora usa seu próprio usuário
                if request.user.user_type != 'TRANSPORTADORA':
                    messages.error(request, 'Apenas transportadoras podem cadastrar veículos!')
                    return redirect('vehicles-list')
                transportadora = request.user
            
            vehicle = Vehicle.objects.create(
                transportadora=transportadora,
                placa=request.POST['placa'].upper(),
                renavam=request.POST['renavam'],
                chassi=request.POST['chassi'].upper(),
                modelo=request.POST['modelo'],
                ano=int(request.POST['ano']),
                cor=request.POST['cor'],
                status=request.POST.get('status', 'DISPONIVEL'),
                observacoes=request.POST.get('observacoes', ''),
            )
            
            # Vincular device se selecionado
            device_id = request.POST.get('device')
            if device_id:
                try:
                    device = Device.objects.get(pk=device_id, vehicle__isnull=True)
                    device.vehicle = vehicle
                    device.save()
                except Device.DoesNotExist:
                    pass
            
            messages.success(request, f'Veículo {vehicle.placa} cadastrado com sucesso!')
            return redirect('vehicles-detail', pk=vehicle.pk)
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar veículo: {str(e)}')
    
    # Devices disponíveis (sem veículo vinculado)
    available_devices = Device.objects.filter(vehicle__isnull=True)
    
    # Lista de transportadoras para GR
    from apps.authentication.models import User
    transportadoras = None
    if request.user.is_superuser or request.user.user_type == 'GR':
        transportadoras = User.objects.filter(user_type='TRANSPORTADORA')
    
    context = {
        'vehicle': None,
        'available_devices': available_devices,
        'transportadoras': transportadoras,
    }
    return render(request, 'vehicles/vehicle_form.html', context)


@login_required
def vehicle_edit(request, pk):
    """Editar veículo"""
    # GR pode editar qualquer veículo, Transportadora apenas os seus
    if request.user.is_superuser or request.user.user_type == 'GR':
        vehicle = get_object_or_404(Vehicle, pk=pk)
    else:
        vehicle = get_object_or_404(Vehicle, pk=pk, transportadora=request.user)
    
    if request.method == 'POST':
        try:
            vehicle.placa = request.POST['placa'].upper()
            vehicle.renavam = request.POST['renavam']
            vehicle.chassi = request.POST['chassi'].upper()
            vehicle.modelo = request.POST['modelo']
            vehicle.ano = int(request.POST['ano'])
            vehicle.cor = request.POST['cor']
            vehicle.status = request.POST.get('status', 'DISPONIVEL')
            vehicle.observacoes = request.POST.get('observacoes', '')
            vehicle.save()
            
            # Atualizar device vinculado
            device_id = request.POST.get('device')
            
            # Remover device antigo se houver
            if hasattr(vehicle, 'device') and vehicle.device:
                if not device_id or str(vehicle.device.pk) != device_id:
                    old_device = vehicle.device
                    old_device.vehicle = None
                    old_device.save()
            
            # Vincular novo device
            if device_id:
                try:
                    device = Device.objects.get(pk=device_id)
                    device.vehicle = vehicle
                    device.save()
                except Device.DoesNotExist:
                    pass
            
            messages.success(request, f'Veículo {vehicle.placa} atualizado com sucesso!')
            return redirect('vehicles-detail', pk=vehicle.pk)
        except Exception as e:
            messages.error(request, f'Erro ao atualizar veículo: {str(e)}')
    
    # Devices disponíveis (sem veículo ou o atual)
    available_devices = Device.objects.filter(
        Q(vehicle__isnull=True) | Q(vehicle=vehicle)
    )
    
    # Lista de transportadoras para GR
    from apps.authentication.models import User
    transportadoras = None
    if request.user.is_superuser or request.user.user_type == 'GR':
        transportadoras = User.objects.filter(user_type='TRANSPORTADORA')
    
    context = {
        'vehicle': vehicle,
        'available_devices': available_devices,
        'transportadoras': transportadoras,
    }
    return render(request, 'vehicles/vehicle_form.html', context)


@login_required
def vehicle_change_status(request, pk):
    """Mudar status do veículo"""
    # GR pode alterar qualquer veículo, Transportadora apenas os seus
    if request.user.is_superuser or request.user.user_type == 'GR':
        vehicle = get_object_or_404(Vehicle, pk=pk)
    else:
        vehicle = get_object_or_404(Vehicle, pk=pk, transportadora=request.user)
    new_status = request.GET.get('status')
    
    if new_status in dict(Vehicle.STATUS_CHOICES):
        vehicle.status = new_status
        vehicle.save()
        messages.success(request, f'Status do veículo {vehicle.placa} alterado para {vehicle.get_status_display()}!')
    else:
        messages.error(request, 'Status inválido!')
    
    return redirect('vehicles-detail', pk=vehicle.pk)
