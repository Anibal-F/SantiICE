"""
Módulo de configuración para el Sistema Conciliador
Carga y valida la configuración desde archivos YAML
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List
import logging

class Config:
    """Clase para manejar la configuración del sistema"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Inicializa la configuración
        
        Args:
            config_path: Ruta al archivo de configuración YAML
        """
        self.config_path = Path(config_path)
        self._config = {}
        self._load_config()
        self._setup_logging()
        
    def _load_config(self):
        """Carga la configuración desde el archivo YAML"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self._config = yaml.safe_load(file)
                print(f"✅ Configuración cargada desde: {self.config_path}")
            else:
                print(f"⚠️ Archivo de configuración no encontrado: {self.config_path}")
                self._load_default_config()
                
        except Exception as e:
            print(f"❌ Error al cargar configuración: {e}")
            self._load_default_config()
    
    def _load_default_config(self):
        """Carga configuración por defecto si no existe archivo"""
        self._config = {
            'tolerances': {
                'value_percentage': 5.0,
                'amount_absolute': 50.0
            },
            'matching': {
                'fuzzy_threshold': 85,
                'exact_match_required': ['pedido_id'],
                'case_sensitive': False
            },
            'file_formats': {
                'oxxo': {
                    'skip_rows': 3,
                    'header_row': 1,
                    'total_indicators': ['TOTAL POR FECHA', ';', 'TOTALES']
                },
                'looker': {
                    'header_row': 0,
                    'group_by_fields': {
                        'oxxo': 'No. Pedido (Filtrado)',
                        'kiosko': 'Folio del Ticket (Filtrado)'
                    }
                }
            },
            'output': {
                'reports_dir': './data/output',
                'processed_dir': './data/processed',
                'formats': ['xlsx', 'csv']
            }
        }
        print("✅ Configuración por defecto cargada")
    
    def _setup_logging(self):
        """Configura el sistema de logging"""
        log_level = self.get('logging.level', 'INFO')
        log_file = self.get('logging.file', 'conciliador.log')
        
        # Crear directorio de logs si no existe
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/{log_file}'),
                logging.StreamHandler()
            ]
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando notación de puntos
        
        Args:
            key: Clave en formato 'section.subsection.key'
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración o default
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_tolerance_percentage(self) -> float:
        """Obtiene el porcentaje de tolerancia para comparaciones"""
        return self.get('tolerances.value_percentage', 5.0)
    
    def get_tolerance_absolute(self) -> float:
        """Obtiene la tolerancia absoluta para comparaciones"""
        return self.get('tolerances.amount_absolute', 50.0)
    
    def get_fuzzy_threshold(self) -> int:
        """Obtiene el umbral para matching fuzzy"""
        return self.get('matching.fuzzy_threshold', 85)
    
    def get_oxxo_skip_rows(self) -> int:
        """Obtiene el número de filas a saltar en archivo OXXO"""
        return self.get('file_formats.oxxo.skip_rows', 3)
    
    def get_oxxo_total_indicators(self) -> List[str]:
        """Obtiene los indicadores de filas de totales en OXXO"""
        return self.get('file_formats.oxxo.total_indicators', [])
    
    def get_looker_group_field(self, client_type: str) -> str:
        """
        Obtiene el campo de agrupación para archivos Looker
        
        Args:
            client_type: 'oxxo' o 'kiosko'
        """
        return self.get(f'file_formats.looker.group_by_fields.{client_type}', '')
    
    def get_output_dir(self) -> str:
        """Obtiene el directorio de salida para reportes"""
        return self.get('output.reports_dir', './data/output')
    
    def get_processed_dir(self) -> str:
        """Obtiene el directorio para datos procesados"""
        return self.get('output.processed_dir', './data/processed')
    
    def get_output_formats(self) -> List[str]:
        """Obtiene los formatos de salida disponibles"""
        return self.get('output.formats', ['xlsx', 'csv'])
    
    def create_directories(self):
        """Crea los directorios necesarios si no existen"""
        directories = [
            'data/input',
            'data/processed', 
            'data/output',
            'logs',
            'tests'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
        print("✅ Directorios del proyecto creados")
    
    def validate_config(self) -> bool:
        """
        Valida que la configuración tenga los valores mínimos requeridos
        
        Returns:
            True si la configuración es válida
        """
        required_keys = [
            'tolerances.value_percentage',
            'tolerances.amount_absolute',
            'file_formats.oxxo.skip_rows',
            'output.reports_dir'
        ]
        
        missing_keys = []
        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"❌ Configuración inválida. Claves faltantes: {missing_keys}")
            return False
            
        print("✅ Configuración validada correctamente")
        return True
    
        # Configuración web
    UPLOAD_DIR = "uploads"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = ['.xlsx', '.xls', '.csv']
    CORS_ORIGINS = ["http://localhost:3000"]

# Instancia global de configuración
config = Config()