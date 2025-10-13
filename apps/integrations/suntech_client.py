"""
Cliente para integração com a API Suntech.
"""
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SuntechAPIError(Exception):
    """Exceção personalizada para erros da API Suntech."""
    pass


class SuntechAPIClient:
    """
    Cliente para integração com a API Suntech.
    
    A API Suntech fornece acesso aos dados dos dispositivos de rastreamento.
    Base URL: https://ap3.stc.srv.br/integration/prod/ws/
    """
    
    def __init__(self):
        """Inicializa o cliente com as credenciais do settings."""
        self.base_url = settings.SUNTECH_API_BASE_URL
        self.api_key = settings.SUNTECH_API_KEY
        self.api_user = settings.SUNTECH_API_USER
        self.api_pass = settings.SUNTECH_API_PASS
        self.timeout = 30  # segundos
        
    def _get_auth_payload(self) -> Dict[str, str]:
        """
        Retorna o payload de autenticação padrão.
        
        Returns:
            Dict com credenciais de autenticação
        """
        return {
            'key': self.api_key,
            'user': self.api_user,
            'pass': self.api_pass
        }
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Faz uma requisição para a API Suntech.
        
        Args:
            endpoint: Nome do endpoint (ex: 'getClientVehicles')
            payload: Dados a serem enviados
            
        Returns:
            Resposta da API em formato dict
            
        Raises:
            SuntechAPIError: Em caso de erro na requisição
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Fazendo requisição para Suntech API: {endpoint}")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Verificar se a API retornou erro
            if not data.get('success', False):
                error_message = data.get('message', 'Erro desconhecido')
                logger.error(f"Erro da API Suntech: {error_message}")
                raise SuntechAPIError(f"Erro da API Suntech: {error_message}")
            
            logger.info(f"Requisição para {endpoint} bem-sucedida")
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout na requisição para {endpoint}")
            raise SuntechAPIError("Timeout ao conectar com a API Suntech")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {endpoint}: {str(e)}")
            raise SuntechAPIError(f"Erro ao conectar com a API Suntech: {str(e)}")
        
        except ValueError as e:
            logger.error(f"Erro ao decodificar resposta JSON: {str(e)}")
            raise SuntechAPIError("Resposta inválida da API Suntech")
    
    def get_client_vehicles(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Lista todos os dispositivos/veículos registrados na conta.
        
        Args:
            use_cache: Se True, usa cache de 5 minutos para evitar requisições desnecessárias
            
        Returns:
            Lista de veículos com suas últimas posições
            
        Raises:
            SuntechAPIError: Em caso de erro na requisição
        """
        cache_key = 'suntech_client_vehicles'
        
        # Tentar obter do cache
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info("Retornando veículos do cache")
                return cached_data
        
        # Fazer requisição à API
        payload = self._get_auth_payload()
        response = self._make_request('getClientVehicles', payload)
        
        vehicles = response.get('data', [])
        
        # Salvar no cache por 5 minutos
        if use_cache:
            cache.set(cache_key, vehicles, 300)
        
        return vehicles
    
    def get_vehicle_by_device_id(self, device_id: int, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Busca um veículo específico pelo ID do dispositivo.
        
        Args:
            device_id: ID do dispositivo Suntech
            
        Returns:
            Dados do veículo ou None se não encontrado
        """
        vehicles = self.get_client_vehicles(use_cache=use_cache)

        for vehicle in vehicles:
            if vehicle.get('deviceId') == device_id:
                return vehicle

        return None
    
    def get_vehicle_positions(
        self,
        vehicle_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Retorna o histórico de posições de um veículo em um período.
        
        Args:
            vehicle_id: ID do veículo na plataforma Suntech
            start_date: Data/hora inicial
            end_date: Data/hora final
            
        Returns:
            Lista de posições do veículo
            
        Raises:
            SuntechAPIError: Em caso de erro na requisição
        """
        payload = self._get_auth_payload()
        payload.update({
            'vehicleId': vehicle_id,
            'startDate': start_date.strftime('%Y-%m-%d %H:%M:%S'),
            'endDate': end_date.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        response = self._make_request('getVehiclePositions', payload)
        return response.get('data', [])
    
    def send_command(
        self,
        vehicle_id: int,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Envia um comando para um dispositivo específico.
        
        Args:
            vehicle_id: ID do veículo na plataforma Suntech
            command: Comando a ser enviado (ex: 'block', 'unblock')
            parameters: Parâmetros adicionais do comando
            
        Returns:
            Resposta da API
            
        Raises:
            SuntechAPIError: Em caso de erro na requisição
        """
        payload = self._get_auth_payload()
        payload.update({
            'vehicleId': vehicle_id,
            'command': command
        })
        
        if parameters:
            payload.update(parameters)
        
        return self._make_request('sendCommand', payload)
    
    def check_device_updated_recently(
        self,
        device_id: int,
        minutes: int = None
    ) -> bool:
        """
        Verifica se o dispositivo foi atualizado recentemente.
        
        Args:
            device_id: ID do dispositivo Suntech
            minutes: Número de minutos para considerar "recente"
                    (padrão: DEVICE_UPDATE_THRESHOLD_MINUTES do settings)
            
        Returns:
            True se o dispositivo foi atualizado dentro do período, False caso contrário
        """
        if minutes is None:
            minutes = settings.DEVICE_UPDATE_THRESHOLD_MINUTES
        
        vehicle = self.get_vehicle_by_device_id(device_id)
        
        if not vehicle:
            logger.warning(f"Dispositivo {device_id} não encontrado")
            return False
        
        # Obter data da última atualização
        system_date_str = vehicle.get('systemDate')
        if not system_date_str:
            logger.warning(f"Dispositivo {device_id} sem data de atualização")
            return False
        
        try:
            # Converter string para datetime
            system_date = datetime.strptime(system_date_str, '%Y-%m-%d %H:%M:%S')
            
            # Calcular diferença
            now = datetime.now()
            time_diff = now - system_date
            
            # Verificar se está dentro do período
            is_recent = time_diff.total_seconds() / 60 <= minutes
            
            if is_recent:
                logger.info(
                    f"Dispositivo {device_id} atualizado há "
                    f"{time_diff.total_seconds() / 60:.1f} minutos"
                )
            else:
                logger.warning(
                    f"Dispositivo {device_id} desatualizado - última atualização há "
                    f"{time_diff.total_seconds() / 60:.1f} minutos"
                )
            
            return is_recent
            
        except ValueError as e:
            logger.error(f"Erro ao parsear data do dispositivo {device_id}: {str(e)}")
            return False
    
    def get_device_last_position(self, device_id: int) -> Optional[Dict[str, Any]]:
        """
        Retorna a última posição conhecida de um dispositivo.
        
        Args:
            device_id: ID do dispositivo Suntech
            
        Returns:
            Dicionário com dados da última posição ou None
        """
        vehicle = self.get_vehicle_by_device_id(device_id)
        
        if not vehicle:
            return None
        
        return {
            'latitude': vehicle.get('latitude'),
            'longitude': vehicle.get('longitude'),
            'address': vehicle.get('address'),
            'speed': vehicle.get('speed'),
            'ignition': vehicle.get('ignition'),
            'date': vehicle.get('date'),
            'system_date': vehicle.get('systemDate'),
            'odometer': vehicle.get('odometer'),
            'direction': vehicle.get('direction')
        }
    
    def clear_cache(self):
        """Limpa o cache de veículos."""
        cache.delete('suntech_client_vehicles')
        logger.info("Cache da API Suntech limpo")


# Instância global do cliente
suntech_client = SuntechAPIClient()
