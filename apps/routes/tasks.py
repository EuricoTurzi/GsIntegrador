"""
Tasks Celery para rotas.
"""
from celery import shared_task
import logging
from .models import Route

logger = logging.getLogger(__name__)


@shared_task(name='routes.calculate_all_routes')
def calculate_all_routes():
    """
    Task para recalcular todas as rotas ativas.
    
    Útil para manter os dados atualizados periodicamente.
    """
    try:
        logger.info("Iniciando cálculo de todas as rotas...")
        
        routes = Route.objects.filter(is_active=True)
        success_count = 0
        error_count = 0
        
        for route in routes:
            if route.calculate_route():
                success_count += 1
                logger.debug(f"Rota '{route.name}' calculada")
            else:
                error_count += 1
                logger.warning(f"Erro ao calcular rota '{route.name}'")
        
        logger.info(
            f"Cálculo concluído: "
            f"{success_count} sucesso, {error_count} erros"
        )
        
        return {
            'success': True,
            'total': routes.count(),
            'calculated': success_count,
            'errors': error_count
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular rotas: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='routes.calculate_route_by_id')
def calculate_route_by_id(route_id: int):
    """
    Task para calcular uma rota específica.
    
    Args:
        route_id: ID da rota no banco de dados
    """
    try:
        route = Route.objects.get(id=route_id)
        
        logger.info(f"Calculando rota '{route.name}'...")
        
        if route.calculate_route():
            logger.info(f"Rota '{route.name}' calculada com sucesso")
            return {
                'success': True,
                'route_id': route_id,
                'route_name': route.name,
                'distance_km': route.distance_km,
                'duration': route.estimated_duration_formatted
            }
        else:
            logger.error(f"Erro ao calcular rota '{route.name}'")
            return {
                'success': False,
                'route_id': route_id,
                'error': 'Falha no cálculo'
            }
        
    except Route.DoesNotExist:
        logger.error(f"Rota {route_id} não encontrada")
        return {
            'success': False,
            'route_id': route_id,
            'error': 'Rota não encontrada'
        }
    
    except Exception as e:
        logger.error(f"Erro ao calcular rota {route_id}: {str(e)}")
        return {
            'success': False,
            'route_id': route_id,
            'error': str(e)
        }


@shared_task(name='routes.check_routes_without_calculation')
def check_routes_without_calculation():
    """
    Task para verificar rotas que ainda não foram calculadas.
    
    Retorna lista de rotas sem dados de distância/duração.
    """
    try:
        logger.info("Verificando rotas sem cálculo...")
        
        routes = Route.objects.filter(
            is_active=True,
            distance_meters__isnull=True
        )
        
        uncalculated_routes = []
        
        for route in routes:
            uncalculated_routes.append({
                'route_id': route.id,
                'name': route.name,
                'origin': route.origin_name,
                'destination': route.destination_name,
                'transportadora': route.transportadora.company_name
            })
        
        logger.info(f"Encontradas {len(uncalculated_routes)} rotas sem cálculo")
        
        return {
            'success': True,
            'uncalculated_count': len(uncalculated_routes),
            'uncalculated_routes': uncalculated_routes
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar rotas: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
