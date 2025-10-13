from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Device
from apps.vehicles.models import Vehicle


@login_required
def device_list(request):
    """Lista de rastreadores com filtros e busca"""
    # Filtrar por transportadora se não for GR
    if request.user.is_superuser or request.user.user_type == 'GR':
        devices = Device.objects.all().select_related('vehicle', 'vehicle__transportadora')
    else:
        devices = Device.objects.filter(vehicle__transportadora=request.user).select_related('vehicle', 'vehicle__transportadora')
    
    # Busca
    search = request.GET.get('search', '')
    if search:
        devices = devices.filter(
            Q(label__icontains=search) |
            Q(imei__icontains=search) |
            Q(vehicle__placa__icontains=search)
        )
    
    # Filtros
    update_status = request.GET.get('update_status', '')
    if update_status == 'active':
        # Atualizado nas últimas 24h
        from django.utils import timezone
        from datetime import timedelta
        yesterday = timezone.now() - timedelta(hours=24)
        devices = devices.filter(last_position_date__gte=yesterday)
    elif update_status == 'outdated':
        # Desatualizado (mais de 24h)
        from django.utils import timezone
        from datetime import timedelta
        yesterday = timezone.now() - timedelta(hours=24)
        devices = devices.filter(last_position_date__lt=yesterday, last_position_date__isnull=False)
    elif update_status == 'no_data':
        # Nunca enviou dados
        devices = devices.filter(last_position_date__isnull=True)
    
    vehicle_status = request.GET.get('vehicle_status', '')
    if vehicle_status == 'with_vehicle':
        devices = devices.filter(vehicle__isnull=False)
    elif vehicle_status == 'without_vehicle':
        devices = devices.filter(vehicle__isnull=True)
    
    # Ordenação
    sort = request.GET.get('sort', '-updated_at')
    devices = devices.order_by(sort)
    
    # Estatísticas
    from django.utils import timezone
    from datetime import timedelta
    yesterday = timezone.now() - timedelta(hours=24)
    
    stats = {
        'total': devices.count(),
        'active': devices.filter(last_position_date__gte=yesterday).count(),
        'outdated': devices.filter(last_position_date__lt=yesterday, last_position_date__isnull=False).count(),
        'no_data': devices.filter(last_position_date__isnull=True).count(),
    }
    
    # Paginação
    paginator = Paginator(devices, 20)
    page = request.GET.get('page', 1)
    devices_page = paginator.get_page(page)
    
    # Adicionar propriedades de status para cada device
    for device in devices_page:
        if device.last_position_date:
            device.is_updated = device.last_position_date >= yesterday
            device.is_outdated = device.last_position_date < yesterday
        else:
            device.is_updated = False
            device.is_outdated = False
    
    context = {
        'devices': devices_page,
        'stats': stats,
        'search': search,
        'update_status': update_status,
        'vehicle_status': vehicle_status,
        'sort': sort,
        'last_sync': timezone.now(),  # Para mostrar timestamp da última consulta
    }
    return render(request, 'devices/device_list.html', context)


@login_required
def device_detail(request, pk):
    """Detalhes do rastreador"""
    # Verificar permissões
    if request.user.is_superuser or request.user.user_type == 'GR':
        device = get_object_or_404(Device.objects.select_related('vehicle', 'vehicle__transportadora'), pk=pk)
    else:
        device = get_object_or_404(
            Device.objects.select_related('vehicle', 'vehicle__transportadora'),
            pk=pk,
            vehicle__transportadora=request.user
        )
    
    context = {
        'device': device,
    }
    return render(request, 'devices/device_detail.html', context)


@login_required
def device_create(request):
    """Criar novo rastreador"""
    if request.method == 'POST':
        try:
            # Verificar se veículo foi selecionado
            vehicle_id = request.POST.get('vehicle')
            vehicle = None
            if vehicle_id:
                vehicle = Vehicle.objects.get(pk=vehicle_id)
                
                # Verificar se veículo já tem rastreador
                if hasattr(vehicle, 'device'):
                    messages.error(request, f'O veículo {vehicle.placa} já possui um rastreador vinculado!')
                    return redirect('devices-create')
            
            # Obter número do equipamento
            device_number = request.POST.get('device_number', '').strip()
            if not device_number:
                messages.error(request, 'Informe o número do equipamento!')
                return redirect('devices-create')
            
            # Buscar dispositivo na API Suntech
            from apps.integrations.suntech_client import suntech_client, SuntechAPIError
            
            try:
                device_data = suntech_client.get_vehicle_by_device_id(int(device_number))
                
                if not device_data:
                    messages.error(request, f'Equipamento {device_number} não encontrado na API Suntech. Verifique o número.')
                    return redirect('devices-create')
                
                # Extrair dados da API
                suntech_device_id = device_data.get('deviceId')
                suntech_vehicle_id = device_data.get('vehicleId')
                imei = device_data.get('imei', device_number)
                api_label = device_data.get('label', '')
                
            except (SuntechAPIError, ValueError) as e:
                messages.error(request, f'Erro ao buscar equipamento na API Suntech: {str(e)}')
                return redirect('devices-create')
            
            # Obter label do formulário ou usar o da API
            user_label = request.POST.get('label', '').strip()
            final_label = user_label if user_label else api_label
            
            # Criar device e já sincronizar dados
            from django.utils import timezone
            from datetime import datetime
            
            device = Device.objects.create(
                suntech_device_id=suntech_device_id,
                suntech_vehicle_id=suntech_vehicle_id,
                imei=imei,
                label=final_label,
                vehicle=vehicle,
                is_active='is_active' in request.POST,
                # Já salvar dados da telemetria
                last_latitude=device_data.get('latitude'),
                last_longitude=device_data.get('longitude'),
                last_speed=device_data.get('speed', 0),
                last_sync_at=timezone.now(),
            )
            
            # Mapear ignição
            ignition_value = device_data.get('ignition')
            if isinstance(ignition_value, bool):
                device.last_ignition_status = 'ON' if ignition_value else 'OFF'
            else:
                device.last_ignition_status = 'OFF'
            
            # Parsear datas
            position_date_str = device_data.get('date')
            if position_date_str:
                try:
                    device.last_position_date = timezone.make_aware(
                        datetime.strptime(position_date_str, '%Y-%m-%d %H:%M:%S')
                    )
                except (ValueError, TypeError):
                    pass
            
            system_date_str = device_data.get('systemDate')
            if system_date_str:
                try:
                    device.last_system_date = timezone.make_aware(
                        datetime.strptime(system_date_str, '%Y-%m-%d %H:%M:%S')
                    )
                except (ValueError, TypeError):
                    pass
            
            device.save()
            
            messages.success(request, f'✅ Rastreador {device.label or device.imei} cadastrado com sucesso!')
            messages.info(request, f'📡 Dados sincronizados automaticamente com a API Suntech')
            return redirect('devices-detail', pk=device.pk)
            
        except Vehicle.DoesNotExist:
            messages.error(request, 'Veículo não encontrado!')
            return redirect('devices-create')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar rastreador: {str(e)}')
            return redirect('devices-create')
    
    # GET - Mostrar formulário
    # Listar apenas veículos sem rastreador
    if request.user.is_superuser or request.user.user_type == 'GR':
        available_vehicles = Vehicle.objects.filter(device__isnull=True)
    else:
        available_vehicles = Vehicle.objects.filter(
            transportadora=request.user,
            device__isnull=True
        )
    
    context = {
        'device': None,
        'available_vehicles': available_vehicles,
    }
    return render(request, 'devices/device_form.html', context)


@login_required
def device_edit(request, pk):
    """Editar rastreador"""
    # Verificar permissões
    if request.user.is_superuser or request.user.user_type == 'GR':
        device = get_object_or_404(Device, pk=pk)
    else:
        device = get_object_or_404(Device, pk=pk, vehicle__transportadora=request.user)
    
    if request.method == 'POST':
        try:
            from apps.integrations.suntech_client import suntech_client, SuntechAPIError
            
            # Atualizar label e status (campos simples)
            device.label = request.POST.get('label', '').strip()
            device.is_active = 'is_active' in request.POST
            
            # Verificar se mudou o número do equipamento
            device_number = request.POST.get('device_number', '').strip()
            if device_number and str(device.suntech_device_id) != device_number:
                # Buscar novo equipamento na API
                try:
                    device_data = suntech_client.get_vehicle_by_device_id(int(device_number))
                    
                    if not device_data:
                        messages.error(request, f'Equipamento {device_number} não encontrado na API Suntech.')
                        return redirect('devices-edit', pk=pk)
                    
                    # Atualizar IDs
                    device.suntech_device_id = device_data.get('deviceId')
                    device.suntech_vehicle_id = device_data.get('vehicleId')
                    device.imei = device_data.get('imei', device_number)
                    
                    messages.info(request, '📡 Dados do equipamento atualizados da API Suntech')
                    
                except (SuntechAPIError, ValueError) as e:
                    messages.error(request, f'Erro ao buscar equipamento: {str(e)}')
                    return redirect('devices-edit', pk=pk)
            
            # Atualizar veículo
            vehicle_id = request.POST.get('vehicle')
            if vehicle_id:
                new_vehicle = Vehicle.objects.get(pk=vehicle_id)
                
                # Se mudou de veículo, verificar se o novo já tem rastreador
                if device.vehicle != new_vehicle and hasattr(new_vehicle, 'device'):
                    messages.error(request, f'O veículo {new_vehicle.placa} já possui um rastreador vinculado!')
                    return redirect('devices-edit', pk=pk)
                
                device.vehicle = new_vehicle
            else:
                device.vehicle = None
            
            device.save()
            
            messages.success(request, f'Rastreador {device.label or device.imei} atualizado com sucesso!')
            return redirect('devices-detail', pk=device.pk)
            
        except Vehicle.DoesNotExist:
            messages.error(request, 'Veículo não encontrado!')
            return redirect('devices-edit', pk=pk)
        except Exception as e:
            messages.error(request, f'Erro ao atualizar rastreador: {str(e)}')
            return redirect('devices-edit', pk=pk)
    
    # GET - Mostrar formulário
    # Listar veículos disponíveis (sem rastreador ou com este rastreador)
    if request.user.is_superuser or request.user.user_type == 'GR':
        available_vehicles = Vehicle.objects.filter(
            Q(device__isnull=True) | Q(device=device)
        )
    else:
        available_vehicles = Vehicle.objects.filter(
            Q(device__isnull=True) | Q(device=device),
            transportadora=request.user
        )
    
    context = {
        'device': device,
        'available_vehicles': available_vehicles,
    }
    return render(request, 'devices/device_form.html', context)


@login_required
def device_sync(request, pk):
    """Sincronizar dados do rastreador com API Suntech"""
    # Verificar permissões
    if request.user.is_superuser or request.user.user_type == 'GR':
        device = get_object_or_404(Device, pk=pk)
    else:
        device = get_object_or_404(Device, pk=pk, vehicle__transportadora=request.user)
    
    try:
        # Importar cliente Suntech
        from apps.integrations.suntech_client import suntech_client, SuntechAPIError
        
        # Verificar se o dispositivo tem ID Suntech
        if not device.suntech_device_id:
            messages.warning(request, f'Rastreador {device.identifier} não possui ID Suntech vinculado!')
            messages.info(request, 'Configure o ID Suntech no cadastro do rastreador.')
            return redirect('devices-detail', pk=pk)
        
        # Buscar dados do dispositivo na API Suntech
        try:
            device_id = int(device.suntech_device_id)
            vehicle_data = suntech_client.get_vehicle_by_device_id(device_id)
            
            if not vehicle_data:
                messages.error(request, f'Dispositivo {device_id} não encontrado na API Suntech!')
                return redirect('devices-detail', pk=pk)
            
            # Atualizar dados do rastreador
            device.last_latitude = vehicle_data.get('latitude')
            device.last_longitude = vehicle_data.get('longitude')
            device.last_speed = vehicle_data.get('speed', 0)
            
            # Mapear ignição corretamente (boolean -> ON/OFF)
            ignition_value = vehicle_data.get('ignition')
            if isinstance(ignition_value, bool):
                device.last_ignition_status = 'ON' if ignition_value else 'OFF'
            elif isinstance(ignition_value, str):
                device.last_ignition_status = ignition_value.upper() if ignition_value.upper() in ['ON', 'OFF'] else 'OFF'
            else:
                device.last_ignition_status = 'OFF'
            
            # Parsear datas
            from django.utils import timezone
            from datetime import datetime
            
            position_date_str = vehicle_data.get('date')
            if position_date_str:
                try:
                    device.last_position_date = timezone.make_aware(
                        datetime.strptime(position_date_str, '%Y-%m-%d %H:%M:%S')
                    )
                except ValueError:
                    pass
            
            system_date_str = vehicle_data.get('systemDate')
            if system_date_str:
                try:
                    device.last_system_date = timezone.make_aware(
                        datetime.strptime(system_date_str, '%Y-%m-%d %H:%M:%S')
                    )
                except ValueError:
                    pass
            
            # Atualizar label se disponível
            if vehicle_data.get('label') and not device.label:
                device.label = vehicle_data.get('label')
            
            # Atualizar timestamp de sincronização
            device.last_sync_at = timezone.now()
            
            device.save()
            
            messages.success(request, f'✅ Rastreador {device.identifier} sincronizado com sucesso!')
            if device.last_position_date:
                messages.info(request, f'Última posição: {device.last_position_date.strftime("%d/%m/%Y %H:%M:%S")}')
            
        except SuntechAPIError as e:
            messages.error(request, f'Erro da API Suntech: {str(e)}')
        except ValueError as e:
            messages.error(request, f'ID Suntech inválido: {device.suntech_device_id}')
        
    except Exception as e:
        messages.error(request, f'Erro ao sincronizar rastreador: {str(e)}')
    
    return redirect('devices-detail', pk=pk)


@login_required
def device_sync_all(request):
    """Sincronizar todos os rastreadores ativos"""
    try:
        from apps.integrations.suntech_client import suntech_client, SuntechAPIError
        
        # Filtrar por transportadora se não for GR
        if request.user.is_superuser or request.user.user_type == 'GR':
            devices = Device.objects.filter(is_active=True, suntech_device_id__isnull=False)
        else:
            devices = Device.objects.filter(
                is_active=True, 
                suntech_device_id__isnull=False,
                vehicle__transportadora=request.user
            )
        
        if not devices.exists():
            messages.warning(request, 'Nenhum rastreador ativo com ID Suntech encontrado!')
            return redirect('devices-list')
        
        # Buscar todos os veículos da API Suntech de uma vez
        try:
            vehicles_data = suntech_client.get_client_vehicles(use_cache=False)
            
            # Criar dicionário de veículos por device_id para busca rápida
            vehicles_by_device_id = {
                v.get('deviceId'): v for v in vehicles_data
            }
            
            synced = 0
            errors = 0
            
            from django.utils import timezone
            from datetime import datetime
            
            # Sincronizar cada dispositivo
            for device in devices:
                try:
                    device_id = int(device.suntech_device_id)
                    vehicle_data = vehicles_by_device_id.get(device_id)
                    
                    if not vehicle_data:
                        errors += 1
                        continue
                    
                    # Atualizar dados
                    device.last_latitude = vehicle_data.get('latitude')
                    device.last_longitude = vehicle_data.get('longitude')
                    device.last_speed = vehicle_data.get('speed', 0)
                    
                    # Mapear ignição corretamente (boolean -> ON/OFF)
                    ignition_value = vehicle_data.get('ignition')
                    if isinstance(ignition_value, bool):
                        device.last_ignition_status = 'ON' if ignition_value else 'OFF'
                    elif isinstance(ignition_value, str):
                        device.last_ignition_status = ignition_value.upper() if ignition_value.upper() in ['ON', 'OFF'] else 'OFF'
                    else:
                        device.last_ignition_status = 'OFF'
                    
                    # Parsear datas
                    position_date_str = vehicle_data.get('date')
                    if position_date_str:
                        try:
                            device.last_position_date = timezone.make_aware(
                                datetime.strptime(position_date_str, '%Y-%m-%d %H:%M:%S')
                            )
                        except ValueError:
                            pass
                    
                    system_date_str = vehicle_data.get('systemDate')
                    if system_date_str:
                        try:
                            device.last_system_date = timezone.make_aware(
                                datetime.strptime(system_date_str, '%Y-%m-%d %H:%M:%S')
                            )
                        except ValueError:
                            pass
                    
                    if vehicle_data.get('label') and not device.label:
                        device.label = vehicle_data.get('label')
                    
                    # Atualizar timestamp de sincronização
                    device.last_sync_at = timezone.now()
                    
                    device.save()
                    synced += 1
                    
                except (ValueError, Exception) as e:
                    errors += 1
                    continue
            
            # Limpar cache
            suntech_client.clear_cache()
            
            if synced > 0:
                messages.success(request, f'✅ {synced} rastreadores sincronizados com sucesso!')
            if errors > 0:
                messages.warning(request, f'⚠️ {errors} rastreadores com erro na sincronização.')
            
        except SuntechAPIError as e:
            messages.error(request, f'Erro da API Suntech: {str(e)}')
            
    except Exception as e:
        messages.error(request, f'Erro ao sincronizar rastreadores: {str(e)}')
    
    return redirect('devices-list')
