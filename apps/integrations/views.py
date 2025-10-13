"""
Views da API de integrações Suntech.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
import logging

from .suntech_client import suntech_client, SuntechAPIError

logger = logging.getLogger(__name__)


class SuntechVehiclesListView(APIView):
    """
    Lista todos os veículos/dispositivos da API Suntech.
    
    GET /api/integrations/suntech/vehicles/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Retorna lista de veículos da API Suntech.
        
        Query params:
        - use_cache: bool (default: true) - Se deve usar cache
        """
        try:
            use_cache = request.query_params.get('use_cache', 'true').lower() == 'true'
            
            vehicles = suntech_client.get_client_vehicles(use_cache=use_cache)
            
            return Response({
                'success': True,
                'count': len(vehicles),
                'data': vehicles
            }, status=status.HTTP_200_OK)
            
        except SuntechAPIError as e:
            logger.error(f"Erro ao buscar veículos Suntech: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class SuntechVehicleDetailView(APIView):
    """
    Retorna detalhes de um veículo específico pelo device_id.
    
    GET /api/integrations/suntech/vehicles/{device_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, device_id):
        """
        Retorna dados de um veículo específico.
        """
        try:
            vehicle = suntech_client.get_vehicle_by_device_id(int(device_id))
            
            if not vehicle:
                return Response({
                    'success': False,
                    'error': 'Veículo não encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'data': vehicle
            }, status=status.HTTP_200_OK)
            
        except SuntechAPIError as e:
            logger.error(f"Erro ao buscar veículo {device_id}: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class SuntechVehiclePositionsView(APIView):
    """
    Retorna histórico de posições de um veículo.
    
    GET /api/integrations/suntech/vehicles/{vehicle_id}/positions/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, vehicle_id):
        """
        Retorna histórico de posições.
        
        Query params:
        - start_date: str (YYYY-MM-DD HH:MM:SS) - Data inicial
        - end_date: str (YYYY-MM-DD HH:MM:SS) - Data final
        - days: int (default: 1) - Número de dias atrás (se start_date não informado)
        """
        try:
            # Obter parâmetros de data
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            days = int(request.query_params.get('days', 1))
            
            # Se não informar datas, usar últimos X dias
            if not start_date_str or not end_date_str:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
            else:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Formato de data inválido. Use: YYYY-MM-DD HH:MM:SS'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            positions = suntech_client.get_vehicle_positions(
                int(vehicle_id),
                start_date,
                end_date
            )
            
            return Response({
                'success': True,
                'count': len(positions),
                'start_date': start_date.strftime('%Y-%m-%d %H:%M:%S'),
                'end_date': end_date.strftime('%Y-%m-%d %H:%M:%S'),
                'data': positions
            }, status=status.HTTP_200_OK)
            
        except SuntechAPIError as e:
            logger.error(f"Erro ao buscar posições do veículo {vehicle_id}: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class SuntechDeviceStatusView(APIView):
    """
    Verifica se um dispositivo está atualizado.
    
    GET /api/integrations/suntech/devices/{device_id}/status/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, device_id):
        """
        Verifica status de atualização do dispositivo.
        
        Query params:
        - minutes: int (default: 30) - Minutos para considerar atualizado
        """
        try:
            minutes = int(request.query_params.get('minutes', 30))
            
            is_updated = suntech_client.check_device_updated_recently(
                int(device_id),
                minutes
            )
            
            vehicle = suntech_client.get_vehicle_by_device_id(int(device_id))
            
            if not vehicle:
                return Response({
                    'success': False,
                    'error': 'Dispositivo não encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Calcular tempo desde última atualização
            system_date_str = vehicle.get('systemDate')
            last_update_minutes = None
            
            if system_date_str:
                try:
                    system_date = datetime.strptime(system_date_str, '%Y-%m-%d %H:%M:%S')
                    time_diff = datetime.now() - system_date
                    last_update_minutes = time_diff.total_seconds() / 60
                except ValueError:
                    pass
            
            return Response({
                'success': True,
                'device_id': int(device_id),
                'is_updated': is_updated,
                'threshold_minutes': minutes,
                'last_update': system_date_str,
                'last_update_minutes_ago': round(last_update_minutes, 2) if last_update_minutes else None,
                'plate': vehicle.get('plate'),
                'label': vehicle.get('label')
            }, status=status.HTTP_200_OK)
            
        except SuntechAPIError as e:
            logger.error(f"Erro ao verificar status do dispositivo {device_id}: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class SuntechDevicePositionView(APIView):
    """
    Retorna última posição de um dispositivo.
    
    GET /api/integrations/suntech/devices/{device_id}/position/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, device_id):
        """
        Retorna última posição conhecida do dispositivo.
        """
        try:
            position = suntech_client.get_device_last_position(int(device_id))
            
            if not position:
                return Response({
                    'success': False,
                    'error': 'Dispositivo não encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'device_id': int(device_id),
                'data': position
            }, status=status.HTTP_200_OK)
            
        except SuntechAPIError as e:
            logger.error(f"Erro ao buscar posição do dispositivo {device_id}: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class SuntechSendCommandView(APIView):
    """
    Envia um comando para um dispositivo.
    
    POST /api/integrations/suntech/vehicles/{vehicle_id}/command/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, vehicle_id):
        """
        Envia comando para o dispositivo.
        
        Body:
        {
            "command": "block",
            "parameters": {}
        }
        """
        try:
            command = request.data.get('command')
            parameters = request.data.get('parameters', {})
            
            if not command:
                return Response({
                    'success': False,
                    'error': 'Campo "command" é obrigatório'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = suntech_client.send_command(
                int(vehicle_id),
                command,
                parameters
            )
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except SuntechAPIError as e:
            logger.error(f"Erro ao enviar comando para veículo {vehicle_id}: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class SuntechClearCacheView(APIView):
    """
    Limpa o cache da API Suntech.
    
    POST /api/integrations/suntech/cache/clear/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Limpa cache (apenas para usuários GR ou staff).
        """
        user = request.user
        
        if not (user.is_staff or user.is_superuser or user.user_type == 'GR'):
            return Response({
                'success': False,
                'error': 'Permissão negada'
            }, status=status.HTTP_403_FORBIDDEN)
        
        suntech_client.clear_cache()
        
        return Response({
            'success': True,
            'message': 'Cache limpo com sucesso'
        }, status=status.HTTP_200_OK)
