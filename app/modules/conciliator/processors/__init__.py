"""
Paquete de procesadores específicos por cliente
"""

from .factory import ProcessorFactory, get_supported_clients

try:
    from .oxxo_processor import DataProcessor as OxxoProcessor
    from .kiosko_processor import KioskoProcessor
except ImportError:
    # Los procesadores específicos pueden no estar disponibles
    pass

__all__ = [
    'ProcessorFactory',
    'get_supported_clients',
    'OxxoProcessor', 
    'KioskoProcessor'
]