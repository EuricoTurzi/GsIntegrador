"""
Views para renderizar templates HTML de Drivers
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Driver


@login_required
def driver_list(request):
    """Lista de motoristas com filtros e paginação"""
    # GR pode ver todos os motoristas, Transportadora vê apenas os seus
    if request.user.is_superuser or request.user.user_type == 'GR':
        drivers = Driver.objects.all().select_related('transportadora')
    else:
        drivers = Driver.objects.filter(transportadora=request.user).select_related('transportadora')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        drivers = drivers.filter(
            Q(nome__icontains=search) |
            Q(cpf__icontains=search) |
            Q(cnh__icontains=search)
        )
    
    # Filters
    status = request.GET.get('status', '')
    if status == 'active':
        drivers = drivers.filter(is_active=True)
    elif status == 'inactive':
        drivers = drivers.filter(is_active=False)
    
    vehicle_type = request.GET.get('vehicle_type', '')
    if vehicle_type:
        drivers = drivers.filter(tipo_de_veiculo__icontains=vehicle_type)
    
    # Sort
    sort = request.GET.get('sort', '-created_at')
    drivers = drivers.order_by(sort)
    
    # Stats
    stats = {
        'total': Driver.objects.filter(transportadora=request.user).count(),
        'active': Driver.objects.filter(transportadora=request.user, is_active=True).count(),
        'inactive': Driver.objects.filter(transportadora=request.user, is_active=False).count(),
        'on_trip': 0,  # TODO: contar motoristas em viagem
    }
    
    # Pagination
    paginator = Paginator(drivers, 20)
    page = request.GET.get('page', 1)
    drivers = paginator.get_page(page)
    
    context = {
        'drivers': drivers,
        'stats': stats,
    }
    return render(request, 'drivers/driver_list.html', context)


@login_required
def driver_detail(request, pk):
    """Detalhes de um motorista"""
    # GR pode ver qualquer motorista, Transportadora apenas os seus
    if request.user.is_superuser or request.user.user_type == 'GR':
        driver = get_object_or_404(Driver, pk=pk)
    else:
        driver = get_object_or_404(Driver, pk=pk, transportadora=request.user)
    
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
        'driver': driver,
        'stats': stats,
        'recent_trips': recent_trips,
    }
    return render(request, 'drivers/driver_detail.html', context)


@login_required
def driver_create(request):
    """Criar novo motorista"""
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
                    transportadoras = User.objects.filter(user_type='TRANSPORTADORA')
                    context = {
                        'driver': None,
                        'transportadoras': transportadoras,
                        'form_data': request.POST,
                    }
                    return render(request, 'drivers/driver_form.html', context)
                
                try:
                    transportadora = User.objects.get(pk=transportadora_id, user_type='TRANSPORTADORA')
                except User.DoesNotExist:
                    messages.error(request, 'Transportadora não encontrada!')
                    return redirect('drivers-create')
            else:
                # Transportadora usa seu próprio usuário
                if request.user.user_type != 'TRANSPORTADORA':
                    messages.error(request, 'Apenas transportadoras podem cadastrar motoristas!')
                    return redirect('drivers-list')
                transportadora = request.user
            
            driver = Driver.objects.create(
                transportadora=transportadora,
                nome=request.POST['nome'],
                cpf=request.POST['cpf'],
                rg=request.POST['rg'],
                cnh=request.POST['cnh'],
                nome_do_pai=request.POST.get('nome_do_pai', ''),
                nome_da_mae=request.POST['nome_da_mae'],
                tipo_de_veiculo=request.POST['tipo_de_veiculo'],
                data_nascimento=request.POST.get('data_nascimento') or None,
                telefone=request.POST.get('telefone', ''),
                email=request.POST.get('email', ''),
                endereco=request.POST.get('endereco', ''),
                observacoes=request.POST.get('observacoes', ''),
                is_active='is_active' in request.POST,
            )
            messages.success(request, f'Motorista {driver.nome} cadastrado com sucesso!')
            return redirect('drivers-detail', pk=driver.pk)
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar motorista: {str(e)}')
    
    # Lista de transportadoras para GR
    from apps.authentication.models import User
    transportadoras = None
    if request.user.is_superuser or request.user.user_type == 'GR':
        transportadoras = User.objects.filter(user_type='TRANSPORTADORA')
    
    context = {
        'driver': None,
        'transportadoras': transportadoras,
    }
    return render(request, 'drivers/driver_form.html', context)


@login_required
def driver_edit(request, pk):
    """Editar motorista"""
    # GR pode editar qualquer motorista, Transportadora apenas os seus
    if request.user.is_superuser or request.user.user_type == 'GR':
        driver = get_object_or_404(Driver, pk=pk)
    else:
        driver = get_object_or_404(Driver, pk=pk, transportadora=request.user)
    
    if request.method == 'POST':
        try:
            driver.nome = request.POST['nome']
            driver.cpf = request.POST['cpf']
            driver.rg = request.POST['rg']
            driver.cnh = request.POST['cnh']
            driver.nome_do_pai = request.POST.get('nome_do_pai', '')
            driver.nome_da_mae = request.POST['nome_da_mae']
            driver.tipo_de_veiculo = request.POST['tipo_de_veiculo']
            driver.data_nascimento = request.POST.get('data_nascimento') or None
            driver.telefone = request.POST.get('telefone', '')
            driver.email = request.POST.get('email', '')
            driver.endereco = request.POST.get('endereco', '')
            driver.observacoes = request.POST.get('observacoes', '')
            driver.is_active = 'is_active' in request.POST
            driver.save()
            messages.success(request, f'Motorista {driver.nome} atualizado com sucesso!')
            return redirect('drivers-detail', pk=driver.pk)
        except Exception as e:
            messages.error(request, f'Erro ao atualizar motorista: {str(e)}')
    
    context = {
        'driver': driver,
    }
    return render(request, 'drivers/driver_form.html', context)


@login_required
def driver_activate(request, pk):
    """Ativar motorista"""
    # GR pode ativar qualquer motorista, Transportadora apenas os seus
    if request.user.is_superuser or request.user.user_type == 'GR':
        driver = get_object_or_404(Driver, pk=pk)
    else:
        driver = get_object_or_404(Driver, pk=pk, transportadora=request.user)
    driver.is_active = True
    driver.save()
    messages.success(request, f'Motorista {driver.nome} ativado com sucesso!')
    return redirect('drivers-detail', pk=driver.pk)


@login_required
def driver_deactivate(request, pk):
    """Desativar motorista"""
    # GR pode desativar qualquer motorista, Transportadora apenas os seus
    if request.user.is_superuser or request.user.user_type == 'GR':
        driver = get_object_or_404(Driver, pk=pk)
    else:
        driver = get_object_or_404(Driver, pk=pk, transportadora=request.user)
    driver.is_active = False
    driver.save()
    messages.success(request, f'Motorista {driver.nome} desativado com sucesso!')
    return redirect('drivers-detail', pk=driver.pk)
