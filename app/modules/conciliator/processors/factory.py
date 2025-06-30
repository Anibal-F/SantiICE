#!/usr/bin/env python3
"""
Factory Pattern Mejorado para Procesadores Multi-Cliente
Versión robusta con mejor manejo de configuraciones y validaciones
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, Union, Tuple
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Interfaz base para procesadores
class BaseProcessor(ABC):
    """Interfaz base que deben implementar todos los procesadores"""
    
    @abstractmethod
    def process_files(self, source_file: str, looker_file: str, client_filter: Optional[str] = None):
        """Procesa archivos del cliente específico"""
        pass
    
    @abstractmethod
    def get_processing_summary(self) -> Dict:
        """Obtiene resumen del procesamiento"""
        pass
    
    @abstractmethod
    def save_processed_data(self, timestamp: str) -> Dict[str, str]:
        """Guarda datos procesados"""
        pass

class ProcessorFactory:
    """Factory mejorado para crear procesadores específicos por cliente"""
    
    # Registro de procesadores con metadata
    _processor_registry = {
        'OXXO': {
            'class_name': 'OxxoProcessor',
            'module_path': 'src.processors.oxxo_processor',
            'class_import': 'DataProcessor',
            'config_file': 'config/settings_oxxo.yaml',
            'description': '',
            'version': '2.0',
            'capabilities': ['grouping', 'filtering', 'validation']
        },
        'KIOSKO': {
            'class_name': 'KioskoProcessor', 
            'module_path': 'src.processors.kiosko_processor',
            'class_import': 'KioskoProcessor',
            'config_file': 'config/settings_kiosko.yaml',
            'description': '',
            'version': '1.0',
            'capabilities': ['mixed_ids', 'product_grouping', 'strict_validation']
        }
    }
    
    # Configuraciones por defecto
    _default_configs = {
        'OXXO': {
            'tolerances': {'value_percentage': 5.0, 'amount_absolute': 50.0},
            'matching': {'fuzzy_threshold': 85},
            'file_format': {'skip_rows': 3, 'identifier_column': 4, 'value_column': 7}
        },
        'KIOSKO': {
            'tolerances': {'value_percentage': 3.0, 'amount_absolute': 25.0},
            'matching': {'fuzzy_threshold': 90},
            'file_format': {'skip_rows': 0, 'identifier_column': 'Ticket', 'value_column': 'Costo Total'}
        }
    }
    
    @classmethod
    def create_processor(cls, client_type: str, config_override: Optional[Dict] = None, **kwargs) -> BaseProcessor:
        """
        Crea un procesador específico para el tipo de cliente
        
        Args:
            client_type: Tipo de cliente ('OXXO', 'KIOSKO')
            config_override: Configuración personalizada opcional
            **kwargs: Argumentos adicionales para el procesador
            
        Returns:
            Instancia del procesador específico
            
        Raises:
            ValueError: Si el tipo de cliente no es soportado
            ImportError: Si el procesador no se puede importar
        """
        client_type = client_type.upper()
        
        if not cls.is_client_supported(client_type):
            available = cls.get_supported_clients()
            raise ValueError(f"Cliente '{client_type}' no soportado. Disponibles: {', '.join(available)}")
        
        logger.info(f"🏭 Creando procesador para cliente: {client_type}")
        
        try:
            # Obtener metadata del procesador
            processor_info = cls._processor_registry[client_type]
            
            # Cargar configuración específica
            client_config = cls._load_and_merge_config(client_type, config_override)
            
            # Crear instancia del procesador
            processor_instance = cls._create_processor_instance(client_type, processor_info, client_config, **kwargs)
            
            # Validar el procesador creado
            cls._validate_processor_instance(processor_instance, client_type)
            
            logger.info(f"✅ Procesador {client_type} v{processor_info['version']} creado exitosamente")
            return processor_instance
            
        except ImportError as e:
            logger.error(f"❌ Error importando procesador {client_type}: {e}")
            raise ImportError(f"No se pudo importar procesador para {client_type}: {e}")
        except Exception as e:
            logger.error(f"❌ Error creando procesador {client_type}: {e}")
            raise
    
    @classmethod
    def _load_and_merge_config(cls, client_type: str, config_override: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Carga y combina configuraciones desde múltiples fuentes
        
        Args:
            client_type: Tipo de cliente
            config_override: Configuración de override
            
        Returns:
            Configuración combinada
        """
        # Empezar con configuración por defecto
        merged_config = cls._default_configs.get(client_type, {}).copy()
        
        # Cargar configuración base del sistema
        base_config = cls._load_config_file('config/settings.yaml')
        if base_config:
            merged_config = cls._deep_merge(merged_config, base_config)
            logger.debug(f"📋 Configuración base cargada para {client_type}")
        
        # Cargar configuración específica del cliente
        processor_info = cls._processor_registry[client_type]
        client_config_file = processor_info['config_file']
        client_config = cls._load_config_file(client_config_file)
        
        if client_config:
            merged_config = cls._deep_merge(merged_config, client_config)
            logger.info(f"📋 Configuración específica {client_type} cargada: {client_config_file}")
        else:
            logger.warning(f"⚠️ Configuración específica {client_type} no encontrada: {client_config_file}")
        
        # Aplicar overrides si se proporcionan
        if config_override:
            merged_config = cls._deep_merge(merged_config, config_override)
            logger.info(f"🔧 Configuración personalizada aplicada para {client_type}")
        
        # Validar configuración final
        cls._validate_config(merged_config, client_type)
        
        return merged_config
    
    @classmethod
    def _load_config_file(cls, config_path: str) -> Optional[Dict]:
        """
        Carga un archivo de configuración YAML o JSON
        
        Args:
            config_path: Ruta al archivo de configuración
            
        Returns:
            Diccionario con configuración o None si no se puede cargar
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif config_file.suffix.lower() == '.json':
                    return json.load(f) or {}
                else:
                    logger.warning(f"⚠️ Formato de archivo no reconocido: {config_path}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error cargando configuración {config_path}: {e}")
            return None
    
    @classmethod
    def _deep_merge(cls, base_dict: Dict, override_dict: Dict) -> Dict:
        """
        Hace merge profundo de diccionarios de configuración
        
        Args:
            base_dict: Diccionario base
            override_dict: Diccionario que sobrescribe
            
        Returns:
            Diccionario resultado del merge
        """
        result = base_dict.copy()
        
        for key, value in override_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = cls._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @classmethod
    def _validate_config(cls, config: Dict, client_type: str) -> bool:
        """
        Valida que la configuración tenga las secciones requeridas
        
        Args:
            config: Configuración a validar
            client_type: Tipo de cliente
            
        Returns:
            True si la configuración es válida
            
        Raises:
            ValueError: Si la configuración es inválida
        """
        required_sections = ['tolerances', 'matching']
        optional_sections = ['file_format', 'output', 'logging']
        
        missing_required = [section for section in required_sections if section not in config]
        
        if missing_required:
            raise ValueError(f"Configuración {client_type} inválida. Secciones requeridas faltantes: {missing_required}")
        
        # Validar subsecciones críticas
        if 'tolerances' in config:
            tolerances = config['tolerances']
            if 'value_percentage' not in tolerances or 'amount_absolute' not in tolerances:
                raise ValueError(f"Configuración {client_type}: tolerances incompleta")
        
        if 'matching' in config:
            matching = config['matching']
            if 'fuzzy_threshold' not in matching:
                raise ValueError(f"Configuración {client_type}: matching incompleta")
        
        logger.debug(f"✅ Configuración {client_type} validada correctamente")
        return True
    
    @classmethod
    def _create_processor_instance(cls, client_type: str, processor_info: Dict, 
                                 client_config: Dict, **kwargs) -> BaseProcessor:
        """
        Crea la instancia específica del procesador
        
        Args:
            client_type: Tipo de cliente
            processor_info: Información del procesador
            client_config: Configuración del cliente
            **kwargs: Argumentos adicionales
            
        Returns:
            Instancia del procesador
        """
        if client_type == 'OXXO':
            return cls._create_oxxo_processor(processor_info, client_config, **kwargs)
        elif client_type == 'KIOSKO':
            return cls._create_kiosko_processor(processor_info, client_config, **kwargs)
        else:
            raise ValueError(f"Procesador para {client_type} no implementado")
    
    @classmethod
    def _create_oxxo_processor(cls, processor_info: Dict, client_config: Dict, **kwargs) -> BaseProcessor:
        """
        Crea procesador específico para OXXO con configuración mejorada
        
        Args:
            processor_info: Información del procesador
            client_config: Configuración del cliente
            **kwargs: Argumentos adicionales
            
        Returns:
            Instancia del procesador OXXO
        """
        try:
            # Importar el procesador OXXO
            from .oxxo_processor import DataProcessor as OxxoProcessor
            
            # Crear clase adaptada con configuración
            class OxxoProcessorAdapter(OxxoProcessor):
                def __init__(self, config, **adapter_kwargs):
                    super().__init__()
                    self.client_config = config
                    self.client_name = "OXXO"
                    self.processor_info = processor_info
                    
                    # Aplicar configuraciones específicas
                    self._apply_oxxo_config()
                
                def _apply_oxxo_config(self):
                    """Aplica configuración específica de OXXO"""
                    # Configurar tolerancias
                    tolerances = self.client_config.get('tolerances', {})
                    self.tolerance_percentage = tolerances.get('value_percentage', 5.0)
                    self.tolerance_absolute = tolerances.get('amount_absolute', 50.0)
                    
                    # Configurar matching
                    matching = self.client_config.get('matching', {})
                    self.fuzzy_threshold = matching.get('fuzzy_threshold', 85)
                    
                    # Configurar formato de archivo
                    file_format = self.client_config.get('file_format', {})
                    self.skip_rows = file_format.get('skip_rows', 3)
                    
                    logger.debug(f"🔧 Configuración OXXO aplicada: "
                               f"±{self.tolerance_percentage}%, ±${self.tolerance_absolute}")
                
                def get_client_config(self, key: str, default=None):
                    """Obtiene configuración específica del cliente"""
                    keys = key.split('.')
                    value = self.client_config
                    
                    try:
                        for k in keys:
                            value = value[k]
                        return value
                    except (KeyError, TypeError):
                        return default
                
                def get_processor_info(self) -> Dict:
                    """Obtiene información del procesador"""
                    return self.processor_info.copy()
            
            # Crear instancia del adaptador
            processor = OxxoProcessorAdapter(client_config, **kwargs)
            logger.info("✅ Procesador OXXO (adaptado) creado")
            return processor
            
        except ImportError as e:
            logger.error(f"❌ No se pudo importar procesador OXXO: {e}")
            raise ImportError(f"Módulo OXXO no disponible: {e}")
    
    @classmethod
    def _create_kiosko_processor(cls, processor_info: Dict, client_config: Dict, **kwargs) -> BaseProcessor:
        """
        Crea procesador específico para KIOSKO con configuración mejorada
        
        Args:
            processor_info: Información del procesador
            client_config: Configuración del cliente
            **kwargs: Argumentos adicionales
            
        Returns:
            Instancia del procesador KIOSKO
        """
        try:
            # Importar el procesador KIOSKO
            from .kiosko_processor import KioskoProcessor
            
            # Crear clase adaptada con configuración
            class KioskoProcessorAdapter(KioskoProcessor):
                def __init__(self, config, **adapter_kwargs):
                    super().__init__()
                    self.client_config = config
                    self.client_name = "KIOSKO"
                    self.processor_info = processor_info
                    
                    # Aplicar configuraciones específicas
                    self._apply_kiosko_config()
                
                def _apply_kiosko_config(self):
                    """Aplica configuración específica de KIOSKO"""
                    # Configurar tolerancias (más estrictas)
                    tolerances = self.client_config.get('tolerances', {})
                    self.tolerance_percentage = tolerances.get('value_percentage', 3.0)
                    self.tolerance_absolute = tolerances.get('amount_absolute', 25.0)
                    
                    # Configurar matching (más estricto)
                    matching = self.client_config.get('matching', {})
                    self.fuzzy_threshold = matching.get('fuzzy_threshold', 90)
                    
                    # Configurar formato de archivo KIOSKO
                    file_format = self.client_config.get('file_format', {})
                    self.identifier_column = file_format.get('identifier_column', 'Ticket')
                    self.value_column = file_format.get('value_column', 'Costo Total')
                    
                    logger.debug(f"🔧 Configuración KIOSKO aplicada: "
                               f"±{self.tolerance_percentage}%, ±${self.tolerance_absolute}")
                
                def get_client_config(self, key: str, default=None):
                    """Obtiene configuración específica del cliente"""
                    keys = key.split('.')
                    value = self.client_config
                    
                    try:
                        for k in keys:
                            value = value[k]
                        return value
                    except (KeyError, TypeError):
                        return default
                
                def get_processor_info(self) -> Dict:
                    """Obtiene información del procesador"""
                    return self.processor_info.copy()
            
            # Crear instancia del adaptador
            processor = KioskoProcessorAdapter(client_config, **kwargs)
            logger.info("✅ Procesador KIOSKO (adaptado) creado")
            return processor
            
        except ImportError as e:
            logger.error(f"❌ No se pudo importar procesador KIOSKO: {e}")
            raise ImportError(f"Módulo KIOSKO no disponible: {e}")
    
    @classmethod
    def _validate_processor_instance(cls, processor: BaseProcessor, client_type: str):
        """
        Valida que la instancia del procesador sea correcta
        
        Args:
            processor: Instancia del procesador
            client_type: Tipo de cliente
            
        Raises:
            TypeError: Si el procesador no implementa la interfaz correcta
        """
        required_methods = ['process_files', 'get_processing_summary', 'save_processed_data']
        
        for method_name in required_methods:
            if not hasattr(processor, method_name):
                raise TypeError(f"Procesador {client_type} no implementa método requerido: {method_name}")
        
        logger.debug(f"✅ Procesador {client_type} validado correctamente")
    
    @classmethod
    def is_client_supported(cls, client_type: str) -> bool:
        """
        Verifica si un tipo de cliente está soportado
        
        Args:
            client_type: Tipo de cliente a verificar
            
        Returns:
            True si el cliente está soportado
        """
        return client_type.upper() in cls._processor_registry
    
    @classmethod
    def get_supported_clients(cls) -> List[str]:
        """
        Obtiene lista de clientes soportados
        
        Returns:
            Lista de tipos de cliente soportados
        """
        return list(cls._processor_registry.keys())
    
    @classmethod
    def get_client_info(cls, client_type: str) -> Optional[Dict]:
        """
        Obtiene información detallada de un cliente
        
        Args:
            client_type: Tipo de cliente
            
        Returns:
            Diccionario con información del cliente o None si no existe
        """
        return cls._processor_registry.get(client_type.upper())
    
    @classmethod
    def get_all_clients_info(cls) -> Dict[str, Dict]:
        """
        Obtiene información de todos los clientes soportados
        
        Returns:
            Diccionario con información de todos los clientes
        """
        return cls._processor_registry.copy()
    
    @classmethod
    def validate_client_config(cls, client_type: str) -> bool:
        """
        Valida que la configuración del cliente esté completa
        
        Args:
            client_type: Tipo de cliente a validar
            
        Returns:
            True si la configuración es válida
        """
        try:
            client_type = client_type.upper()
            
            if not cls.is_client_supported(client_type):
                logger.error(f"❌ Cliente {client_type} no soportado")
                return False
            
            # Intentar cargar configuración
            client_config = cls._load_and_merge_config(client_type)
            
            # Validar configuración
            cls._validate_config(client_config, client_type)
            
            logger.info(f"✅ Configuración {client_type} validada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validando configuración {client_type}: {e}")
            return False
    
    @classmethod
    def create_processor_with_validation(cls, client_type: str, source_file: str, 
                                       looker_file: str, **kwargs) -> Tuple[BaseProcessor, bool]:
        """
        Crea procesador con validación de archivos
        
        Args:
            client_type: Tipo de cliente
            source_file: Archivo fuente
            looker_file: Archivo Looker
            **kwargs: Argumentos adicionales
            
        Returns:
            Tupla con (procesador, archivos_válidos)
        """
        # Validar archivos
        files_valid = True
        
        if not Path(source_file).exists():
            logger.error(f"❌ Archivo fuente no encontrado: {source_file}")
            files_valid = False
        
        if not Path(looker_file).exists():
            logger.error(f"❌ Archivo Looker no encontrado: {looker_file}")
            files_valid = False
        
        # Crear procesador
        processor = cls.create_processor(client_type, **kwargs)
        
        return processor, files_valid

# Funciones de conveniencia mejoradas
def create_oxxo_processor(config_override: Optional[Dict] = None, **kwargs) -> BaseProcessor:
    """Función de conveniencia para crear procesador OXXO"""
    return ProcessorFactory.create_processor('OXXO', config_override, **kwargs)

def create_kiosko_processor(config_override: Optional[Dict] = None, **kwargs) -> BaseProcessor:
    """Función de conveniencia para crear procesador KIOSKO"""
    return ProcessorFactory.create_processor('KIOSKO', config_override, **kwargs)

def get_supported_clients() -> List[str]:
    """Función de conveniencia para obtener clientes soportados"""
    return ProcessorFactory.get_supported_clients()

def validate_all_clients() -> Dict[str, bool]:
    """Valida configuraciones de todos los clientes"""
    results = {}
    for client in get_supported_clients():
        results[client] = ProcessorFactory.validate_client_config(client)
    return results

def show_clients_status():
    """Muestra estado de todos los clientes"""
    print("🏭 ESTADO DE PROCESADORES MULTI-CLIENTE")
    print("=" * 50)
    
    for client_type in get_supported_clients():
        client_info = ProcessorFactory.get_client_info(client_type)
        is_valid = ProcessorFactory.validate_client_config(client_type)
        
        status = "✅ Listo" if is_valid else "❌ Error"
        print(f"{client_type}: {status}")
        print(f"  📝 {client_info.get('description', 'Sin descripción')}")
        print(f"  🔧 Versión: {client_info.get('version', 'N/A')}")
        print(f"  📋 Capacidades: {', '.join(client_info.get('capabilities', []))}")
        
        if not is_valid:
            print(f"  ⚠️ Configuración incompleta")
        
        print()

# Script principal para testing
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 TESTING FACTORY MULTI-CLIENTE")
    print("=" * 50)
    
    # Mostrar estado general
    show_clients_status()
    
    # Test de creación de procesadores
    print("\n🔧 TESTING CREACIÓN DE PROCESADORES")
    print("-" * 40)
    
    for client in get_supported_clients():
        try:
            processor = ProcessorFactory.create_processor(client)
            print(f"✅ {client}: Procesador creado exitosamente")
            
            # Verificar métodos requeridos
            methods = ['process_files', 'get_processing_summary', 'save_processed_data']
            for method in methods:
                if hasattr(processor, method):
                    print(f"   ✓ Método {method} disponible")
                else:
                    print(f"   ✗ Método {method} faltante")
                    
        except Exception as e:
            print(f"❌ {client}: Error - {e}")
    
    # Test de validación de configuraciones
    print("\n📋 TESTING VALIDACIÓN DE CONFIGURACIONES")
    print("-" * 45)
    
    validation_results = validate_all_clients()
    for client, is_valid in validation_results.items():
        status = "✅ Válida" if is_valid else "❌ Inválida"
        print(f"{client}: {status}")
    
    print("\n🎉 Testing completado")