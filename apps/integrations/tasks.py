"""
Tasks Celery para integração com API Suntech.
"""
from celery import shared_task
import logging
from .suntech_client import suntech_client, SuntechAPIError

logger = logging.getLogger(__name__)


@shared_task(name='integrations.sync_suntech_vehicles')
def sync_suntech_vehicles():
    """
    Task para sincronizar veículos da API Suntech.
    
    Esta task pode ser agendada para executar periodicamente
    e manter os dados atualizados.
    """
    try:
        logger.info("Iniciando sincronização de veículos Suntech...")
        
        # Força atualização sem usar cache
        vehicles = suntech_client.get_client_vehicles(use_cache=False)
        
        logger.info(f"Sincronização concluída: {len(vehicles)} veículos obtidos")
        
        return {
            'success': True,
            'vehicles_count': len(vehicles)
        }
        
    except SuntechAPIError as e:
        logger.error(f"Erro ao sincronizar veículos Suntech: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='integrations.check_devices_status')
def check_devices_status():
    """
    Task para verificar status de todos os dispositivos.
    
    Verifica quais dispositivos estão desatualizados e pode
    gerar alertas ou notificações.
    """
    try:
        logger.info("Verificando status de dispositivos...")
        
        vehicles = suntech_client.get_client_vehicles(use_cache=False)
        
        outdated_devices = []
        updated_devices = []
        
        for vehicle in vehicles:
            device_id = vehicle.get('deviceId')
            
            if suntech_client.check_device_updated_recently(device_id):
                updated_devices.append(device_id)
            else:
                outdated_devices.append({
                    'device_id': device_id,
                    'plate': vehicle.get('plate'),
                    'last_update': vehicle.get('systemDate')
                })
        
        logger.info(
            f"Verificação concluída: "
            f"{len(updated_devices)} atualizados, "
            f"{len(outdated_devices)} desatualizados"
        )
        
        return {
            'success': True,
            'total': len(vehicles),
            'updated_count': len(updated_devices),
            'outdated_count': len(outdated_devices),
            'outdated_devices': outdated_devices
        }
        
    except SuntechAPIError as e:
        logger.error(f"Erro ao verificar status de dispositivos: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='integrations.clear_suntech_cache')
def clear_suntech_cache():
    """
    Task para limpar cache da API Suntech.
    
    Útil para garantir dados sempre atualizados.
    """
    try:
        logger.info("Limpando cache da API Suntech...")
        suntech_client.clear_cache()
        logger.info("Cache limpo com sucesso")
        
        return {
            'success': True,
            'message': 'Cache limpo com sucesso'
        }
        
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
