from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from .models import Route


@login_required
def route_list(request):
    """Lista de rotas com filtros e busca"""
    # Filtrar por transportadora se não for GR
    if request.user.is_superuser or request.user.user_type == 'GR':
        routes = Route.objects.all()
    else:
        routes = Route.objects.filter(transportadora=request.user)
    
    # Busca
    search = request.GET.get('search', '')
    if search:
        routes = routes.filter(
            Q(name__icontains=search) |
            Q(origin_name__icontains=search) |
            Q(destination_name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Filtro de status
    status = request.GET.get('status', '')
    if status == 'active':
        routes = routes.filter(is_active=True)
    elif status == 'inactive':
        routes = routes.filter(is_active=False)
    
    # Ordenação
    sort = request.GET.get('sort', '-created_at')
    routes = routes.order_by(sort)
    
    # Estatísticas
    all_routes = routes
    stats = {
        'total': all_routes.count(),
        'active': all_routes.filter(is_active=True).count(),
        'total_distance': (all_routes.aggregate(total=Sum('distance_meters'))['total'] or 0) / 1000,  # km
        'total_hours': (all_routes.aggregate(total=Sum('estimated_duration_seconds'))['total'] or 0) / 3600,  # hours
    }
    
    # Paginação
    paginator = Paginator(routes, 20)
    page = request.GET.get('page', 1)
    routes_page = paginator.get_page(page)
    
    context = {
        'routes': routes_page,
        'stats': stats,
        'search': search,
        'status': status,
        'sort': sort,
    }
    return render(request, 'routes/route_list.html', context)


@login_required
def route_detail(request, pk):
    """Detalhes da rota"""
    # Verificar permissões
    if request.user.is_superuser or request.user.user_type == 'GR':
        route = get_object_or_404(Route, pk=pk)
    else:
        route = get_object_or_404(Route, pk=pk, transportadora=request.user)
    
    # Converter coordenadas Decimal para float para JavaScript
    context = {
        'route': route,
        'origin_lat': float(route.origin_latitude) if route.origin_latitude else 0,
        'origin_lng': float(route.origin_longitude) if route.origin_longitude else 0,
        'dest_lat': float(route.destination_latitude) if route.destination_latitude else 0,
        'dest_lng': float(route.destination_longitude) if route.destination_longitude else 0,
    }
    return render(request, 'routes/route_detail.html', context)


@login_required
def route_create(request):
    """Criar nova rota"""
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            
            # Origem
            origin_name = request.POST.get('origin_name', '').strip()
            origin_address = request.POST.get('origin_address', '').strip()
            origin_latitude = request.POST.get('origin_latitude', '').strip()
            origin_longitude = request.POST.get('origin_longitude', '').strip()
            
            # Destino
            destination_name = request.POST.get('destination_name', '').strip()
            destination_address = request.POST.get('destination_address', '').strip()
            destination_latitude = request.POST.get('destination_latitude', '').strip()
            destination_longitude = request.POST.get('destination_longitude', '').strip()
            
            # Validações
            if not all([name, origin_name, origin_address, origin_latitude, origin_longitude,
                       destination_name, destination_address, destination_latitude, destination_longitude]):
                messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos!')
                return redirect('routes-create')
            
            # Definir transportadora
            if request.user.user_type == 'TRANSPORTADORA':
                transportadora = request.user
            else:
                # Se for GR, precisa selecionar transportadora
                transportadora_id = request.POST.get('transportadora')
                if not transportadora_id:
                    messages.error(request, 'Selecione uma transportadora!')
                    return redirect('routes-create')
                from apps.authentication.models import User
                transportadora = User.objects.get(pk=transportadora_id, user_type='TRANSPORTADORA')
            
            # Obter geometria da rota (GeoJSON do Leaflet Routing Machine)
            route_geometry = request.POST.get('route_geometry', '').strip()
            
            # Arredondar coordenadas para 7 casas decimais (limite do modelo)
            from decimal import Decimal, ROUND_HALF_UP
            origin_lat = Decimal(str(origin_latitude)).quantize(Decimal('0.0000001'), rounding=ROUND_HALF_UP)
            origin_lng = Decimal(str(origin_longitude)).quantize(Decimal('0.0000001'), rounding=ROUND_HALF_UP)
            dest_lat = Decimal(str(destination_latitude)).quantize(Decimal('0.0000001'), rounding=ROUND_HALF_UP)
            dest_lng = Decimal(str(destination_longitude)).quantize(Decimal('0.0000001'), rounding=ROUND_HALF_UP)
            
            # Criar rota
            route = Route.objects.create(
                transportadora=transportadora,
                name=name,
                description=description,
                origin_name=origin_name,
                origin_address=origin_address,
                origin_latitude=origin_lat,
                origin_longitude=origin_lng,
                destination_name=destination_name,
                destination_address=destination_address,
                destination_latitude=dest_lat,
                destination_longitude=dest_lng,
                is_active='is_active' in request.POST,
            )
            
            # Se temos geometria da rota, calcular distância real
            if route_geometry:
                import json
                try:
                    geometry = json.loads(route_geometry)
                    route.route_geometry = geometry
                    
                    # Calcular distância real da rota (somando segmentos)
                    if geometry.get('type') == 'LineString' and geometry.get('coordinates'):
                        coords = geometry['coordinates']
                        from math import radians, sin, cos, sqrt, atan2
                        
                        total_distance = 0
                        for i in range(len(coords) - 1):
                            lon1, lat1 = radians(coords[i][0]), radians(coords[i][1])
                            lon2, lat2 = radians(coords[i+1][0]), radians(coords[i+1][1])
                            
                            dlat = lat2 - lat1
                            dlon = lon2 - lon1
                            
                            a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
                            c = 2 * atan2(sqrt(a), sqrt(1 - a))
                            
                            total_distance += 6371000 * c  # Raio da Terra em metros
                        
                        route.distance_meters = int(total_distance)
                        route.estimated_duration_seconds = int((total_distance / 1000) / 60 * 3600)  # 60 km/h
                except:
                    pass
            
            # Se não temos geometria, usar distância em linha reta (fallback)
            if not route.distance_meters:
                from math import radians, sin, cos, sqrt, atan2
                
                lat1, lon1 = radians(float(origin_latitude)), radians(float(origin_longitude))
                lat2, lon2 = radians(float(destination_latitude)), radians(float(destination_longitude))
                
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                
                distance = 6371000 * c
                route.distance_meters = int(distance)
                route.estimated_duration_seconds = int((distance / 1000) / 60 * 3600)
            
            from django.utils import timezone
            route.last_calculated_at = timezone.now()
            route.save()
            
            messages.success(request, f'✅ Rota "{route.name}" criada com sucesso!')
            messages.info(request, f'📏 Distância: {route.distance_km} km | ⏱️ Tempo estimado: {route.estimated_duration_hours:.1f}h')
            return redirect('routes-detail', pk=route.pk)
            
        except Exception as e:
            messages.error(request, f'Erro ao criar rota: {str(e)}')
            return redirect('routes-create')
    
    # GET - Mostrar formulário
    context = {}
    
    # Se for GR, listar transportadoras
    if request.user.is_superuser or request.user.user_type == 'GR':
        from apps.authentication.models import User
        context['transportadoras'] = User.objects.filter(user_type='TRANSPORTADORA', is_active=True)
    
    return render(request, 'routes/route_form.html', context)


@login_required
def route_edit(request, pk):
    """Editar rota"""
    # Verificar permissões
    if request.user.is_superuser or request.user.user_type == 'GR':
        route = get_object_or_404(Route, pk=pk)
    else:
        route = get_object_or_404(Route, pk=pk, transportadora=request.user)
    
    if request.method == 'POST':
        try:
            # Atualizar dados básicos
            route.name = request.POST.get('name', '').strip()
            route.description = request.POST.get('description', '').strip()
            route.is_active = 'is_active' in request.POST
            
            # Atualizar origem
            route.origin_name = request.POST.get('origin_name', '').strip()
            route.origin_address = request.POST.get('origin_address', '').strip()
            
            # Arredondar coordenadas para 7 casas decimais
            from decimal import Decimal, ROUND_HALF_UP
            new_origin_lat = Decimal(request.POST.get('origin_latitude', '').strip()).quantize(Decimal('0.0000001'), rounding=ROUND_HALF_UP)
            new_origin_lon = Decimal(request.POST.get('origin_longitude', '').strip()).quantize(Decimal('0.0000001'), rounding=ROUND_HALF_UP)
            
            # Atualizar destino
            route.destination_name = request.POST.get('destination_name', '').strip()
            route.destination_address = request.POST.get('destination_address', '').strip()
            new_dest_lat = Decimal(request.POST.get('destination_latitude', '').strip()).quantize(Decimal('0.0000001'), rounding=ROUND_HALF_UP)
            new_dest_lon = Decimal(request.POST.get('destination_longitude', '').strip()).quantize(Decimal('0.0000001'), rounding=ROUND_HALF_UP)
            
            # Se coordenadas mudaram, recalcular rota
            if (route.origin_latitude != new_origin_lat or route.origin_longitude != new_origin_lon or
                route.destination_latitude != new_dest_lat or route.destination_longitude != new_dest_lon):
                
                route.origin_latitude = new_origin_lat
                route.origin_longitude = new_origin_lon
                route.destination_latitude = new_dest_lat
                route.destination_longitude = new_dest_lon
                
                # Recalcular distância
                from math import radians, sin, cos, sqrt, atan2
                
                lat1, lon1 = radians(new_origin_lat), radians(new_origin_lon)
                lat2, lon2 = radians(new_dest_lat), radians(new_dest_lon)
                
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                
                R = 6371000
                distance = R * c
                
                route.distance_meters = int(distance)
                route.estimated_duration_seconds = int((distance / 1000) / 60 * 3600)
                
                from django.utils import timezone
                route.last_calculated_at = timezone.now()
                
                messages.info(request, '📏 Rota recalculada automaticamente')
            
            route.save()
            
            messages.success(request, f'✅ Rota "{route.name}" atualizada com sucesso!')
            return redirect('routes-detail', pk=route.pk)
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar rota: {str(e)}')
            return redirect('routes-edit', pk=pk)
    
    # GET - Mostrar formulário
    context = {'route': route}
    return render(request, 'routes/route_form.html', context)


@login_required
def route_delete(request, pk):
    """Excluir rota"""
    # Verificar permissões
    if request.user.is_superuser or request.user.user_type == 'GR':
        route = get_object_or_404(Route, pk=pk)
    else:
        route = get_object_or_404(Route, pk=pk, transportadora=request.user)
    
    if request.method == 'POST':
        route_name = route.name
        route.delete()
        messages.success(request, f'Rota "{route_name}" excluída com sucesso!')
        return redirect('routes-list')
    
    return redirect('routes-detail', pk=pk)
