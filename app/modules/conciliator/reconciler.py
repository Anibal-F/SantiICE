"""
Módulo de conciliación MULTI-CLIENTE MEJORADO para el Sistema Conciliador
Funciona de manera robusta para OXXO, KIOSKO y futuros clientes
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import logging
from datetime import datetime
from fuzzywuzzy import fuzz

# Importar config solo para fallback
try:
    from config import config
except ImportError:
    config = None

logger = logging.getLogger(__name__)

class Reconciler:
    """Clase principal para conciliación de datos - VERSIÓN MULTI-CLIENTE MEJORADA"""
    
    def __init__(self, client_type: str = 'OXXO'):
        """
        Inicializa el conciliador para un tipo de cliente específico
        
        Args:
            client_type: 'OXXO', 'KIOSKO' o futuro tipo de cliente
        """
        self.client_type = client_type.upper()
        self.source_data = None
        self.looker_data = None
        self.reconciliation_results = None
        self.summary_stats = None
        
        # CARGAR CONFIGURACIÓN ESPECÍFICA DEL CLIENTE
        self._load_client_specific_config()
        
        # Configurar parámetros adicionales del cliente
        self._setup_additional_client_params()
        
        logger.info(f"🔧 Reconciler inicializado para cliente: {self.client_type}")
        logger.info(f"   Tolerancias: ±{self.config['tolerance_percentage']}% / ±${self.config['tolerance_absolute']}")
        
    def _load_client_specific_config(self):
        """Carga configuración específica del cliente desde archivos YAML"""
        
        # Configuraciones por defecto
        default_configs = {
            'OXXO': {
                'tolerance_percentage': 5.0,
                'tolerance_absolute': 50.0,
                'fuzzy_threshold': 85
            },
            'KIOSKO': {
                'tolerance_percentage': 3.0,  # Más estricto
                'tolerance_absolute': 25.0,   # Más estricto  
                'fuzzy_threshold': 90         # Más estricto
            }
        }
        
        # Empezar con defaults
        self.config = default_configs.get(self.client_type, default_configs['OXXO']).copy()
        
        # CARGAR DESDE ARCHIVO ESPECÍFICO DEL CLIENTE
        try:
            import yaml
            from pathlib import Path
            
            # Determinar archivo de configuración
            config_file = f"config/settings_{self.client_type.lower()}.yaml"
            config_path = Path(config_file)
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    client_config = yaml.safe_load(f)
                
                # Extraer tolerancias específicas
                if 'tolerances' in client_config:
                    tolerances = client_config['tolerances']
                    self.config['tolerance_percentage'] = tolerances.get('value_percentage', self.config['tolerance_percentage'])
                    self.config['tolerance_absolute'] = tolerances.get('amount_absolute', self.config['tolerance_absolute'])
                
                # Extraer configuración de matching
                if 'matching' in client_config:
                    matching = client_config['matching']
                    self.config['fuzzy_threshold'] = matching.get('fuzzy_threshold', self.config['fuzzy_threshold'])
                
                logger.info(f"✅ Configuración {self.client_type} cargada desde: {config_file}")
                
            else:
                logger.warning(f"⚠️ Archivo {config_file} no encontrado, usando defaults")
                
                # Fallback: intentar usar config global si existe
                if config and hasattr(config, 'get'):
                    try:
                        global_tolerance_pct = config.get('tolerances.value_percentage')
                        global_tolerance_abs = config.get('tolerances.amount_absolute')
                        global_fuzzy = config.get('matching.fuzzy_threshold')
                        
                        if global_tolerance_pct is not None:
                            self.config['tolerance_percentage'] = global_tolerance_pct
                        if global_tolerance_abs is not None:
                            self.config['tolerance_absolute'] = global_tolerance_abs
                        if global_fuzzy is not None:
                            self.config['fuzzy_threshold'] = global_fuzzy
                            
                        logger.info(f"📋 Usando configuración global como fallback para {self.client_type}")
                    except:
                        pass
                
        except Exception as e:
            logger.error(f"❌ Error cargando configuración {self.client_type}: {e}")
            logger.info("🔄 Usando configuración por defecto")
    
    def _setup_additional_client_params(self):
        """Configura parámetros adicionales específicos del cliente"""
        
        # Configuraciones de display y campos por cliente
        client_display_configs = {
            'OXXO': {
                'source_name': 'OXXO',
                'source_id_field': 'pedido_adicional',
                'source_value_field': 'valor',
                'identifier_display': 'Pedido',
                'unit_name': 'pedidos',
                'currency_symbol': '$',
                'categories': {
                    'EXACT_MATCH': 'Pedido Conciliado',
                    'WITHIN_TOLERANCE': 'Dentro de Tolerancia',
                    'MINOR_DIFFERENCE': 'Diferencia Menor',
                    'MAJOR_DIFFERENCE': 'Diferencia Mayor',
                    'MISSING_IN_SOURCE': 'Faltante en OXXO',
                    'MISSING_IN_LOOKER': 'Pedido no registrado'
                }
            },
            'KIOSKO': {
                'source_name': 'KIOSKO',
                'source_id_field': 'ticket',
                'source_value_field': 'costo_total',
                'identifier_display': 'Ticket',
                'unit_name': 'tickets',
                'currency_symbol': '$',
                'categories': {
                    'EXACT_MATCH': 'Ticket Conciliado',
                    'WITHIN_TOLERANCE': 'Dentro de Tolerancia',
                    'MINOR_DIFFERENCE': 'Diferencia Menor',
                    'MAJOR_DIFFERENCE': 'Diferencia Mayor',
                    'MISSING_IN_SOURCE': 'Faltante en KIOSKO',
                    'MISSING_IN_LOOKER': 'Ticket no registrado'
                }
            }
        }
        
        # Agregar configuraciones de display a la configuración principal
        display_config = client_display_configs.get(self.client_type, client_display_configs['OXXO'])
        self.config.update(display_config)
        
        logger.debug(f"📋 Parámetros adicionales configurados para {self.client_type}")

    def reconcile(self, source_df: pd.DataFrame, looker_df: pd.DataFrame) -> pd.DataFrame:
        """
        Realiza la conciliación entre datos fuente y Looker (MULTI-CLIENTE MEJORADO)
        
        Args:
            source_df: DataFrame procesado del cliente (OXXO/KIOSKO)
            looker_df: DataFrame procesado de Looker (YA AGRUPADO si es necesario)
            
        Returns:
            DataFrame con resultados de conciliación
        """
        logger.info(f"🔄 INICIANDO CONCILIACIÓN {self.client_type}")
        logger.info("=" * 60)
        
        # Validar datos de entrada
        if not self._validate_input_data(source_df, looker_df):
            raise ValueError(f"Datos de entrada inválidos para {self.client_type}")
        
        self.source_data = source_df.copy()
        self.looker_data = looker_df.copy()
        
        # PASO 1: Preparar datos para matching con nombres consistentes
        logger.info("🔧 Preparando datos para matching...")
        source_prepared = self._prepare_source_for_matching(self.source_data)
        looker_prepared = self._prepare_looker_for_matching(self.looker_data)
        
        logger.info(f"   📊 {self.client_type}: {len(source_prepared)} registros preparados")
        logger.info(f"   📊 Looker: {len(looker_prepared)} registros preparados")
        
        # PASO 2: Realizar matching exacto
        logger.info("🎯 Realizando matching exacto...")
        exact_matches = self._perform_exact_matching(source_prepared, looker_prepared)
        logger.info(f"   ✅ {len(exact_matches)} matches exactos encontrados")
        
        # PASO 3: Realizar matching fuzzy para registros no encontrados
        logger.info("🔍 Realizando matching fuzzy...")
        fuzzy_matches = self._perform_fuzzy_matching(source_prepared, looker_prepared, exact_matches)
        logger.info(f"   🔍 {len(fuzzy_matches)} matches fuzzy encontrados")
        
        # PASO 4: Combinar resultados de matching
        all_matches = self._combine_matches(exact_matches, fuzzy_matches)
        
        # PASO 5: Identificar registros faltantes
        logger.info("❓ Identificando registros faltantes...")
        missing_records = self._identify_missing_records(source_prepared, looker_prepared, all_matches)
        logger.info(f"   ❌ {len(missing_records)} registros faltantes identificados")
        
        # PASO 6: Calcular diferencias con manejo robusto
        logger.info("📊 Calculando diferencias...")
        final_results = self._calculate_differences(all_matches, missing_records)
        
        # PASO 7: Categorizar resultados con tolerancias específicas del cliente
        logger.info("🏷️ Categorizando resultados...")
        categorized_results = self._categorize_results(final_results)
        
        # PASO 8: Calcular estadísticas resumen
        self.reconciliation_results = categorized_results
        self._calculate_summary_stats()
        
        # PASO 9: Generar resumen final
        self._log_reconciliation_summary()
        
        logger.info(f"✅ Conciliación {self.client_type} completada exitosamente")
        logger.info("=" * 60)
        
        return categorized_results
    
    def _validate_input_data(self, source_df: pd.DataFrame, looker_df: pd.DataFrame) -> bool:
        """Valida que los datos de entrada sean apropiados"""
        
        # Verificar que no estén vacíos
        if len(source_df) == 0:
            logger.error(f"❌ DataFrame {self.client_type} está vacío")
            return False
        
        if len(looker_df) == 0:
            logger.error("❌ DataFrame Looker está vacío")
            return False
        
        # Verificar campos requeridos básicos
        required_fields = ['id_matching', 'total_venta']
        
        for field in required_fields:
            if field not in source_df.columns:
                logger.error(f"❌ Campo requerido '{field}' faltante en datos {self.client_type}")
                return False
            
            if field not in looker_df.columns:
                logger.error(f"❌ Campo requerido '{field}' faltante en datos Looker")
                return False
        
        logger.info(f"✅ Validación de datos exitosa para {self.client_type}")
        return True
    
    def _prepare_source_for_matching(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara datos fuente para el proceso de matching (MEJORADO CON FIX KIOSKO)"""
        prepared = df.copy()
        
        # Estandarizar identificador único
        if 'id_matching' not in prepared.columns:
            # Intentar mapear desde campos específicos del cliente
            id_field = self.config['source_id_field']
            if id_field in prepared.columns:
                prepared['id_matching'] = prepared[id_field]
            else:
                logger.error(f"❌ No se puede identificar campo ID en {self.client_type}")
                raise ValueError(f"Campo de identificación no encontrado")
        
        # Limpiar y convertir ID
        if prepared['id_matching'].dtype == 'object':  # Es string
            prepared = prepared[prepared['id_matching'].notna()]
            prepared = prepared[prepared['id_matching'].astype(str).str.strip() != '']
            prepared = prepared[prepared['id_matching'].astype(str) != 'nan']
        else:
            prepared['id_matching'] = pd.to_numeric(prepared['id_matching'], errors='coerce')
            prepared = prepared.dropna(subset=['id_matching'])
            prepared = prepared[prepared['id_matching'] > 0]
        
        # 🔧 FIX KIOSKO: Estandarizar campo de valor CON LÓGICA CORREGIDA
        if 'total_venta' not in prepared.columns:
            # Intentar mapear desde campo específico del cliente
            value_field = self.config['source_value_field']
            if value_field in prepared.columns:
                prepared['total_venta'] = prepared[value_field]
                logger.info(f"🔧 Mapeando {value_field} → total_venta para {self.client_type}")
            else:
                logger.warning(f"⚠️ Campo de valor '{value_field}' no encontrado en {self.client_type}")
                # 🆕 NUEVO: Para KIOSKO, buscar campos alternativos conocidos
                if self.client_type == 'KIOSKO':
                    alternative_fields = ['Costo Total', 'costo_total', 'valor', 'importe']
                    for alt_field in alternative_fields:
                        if alt_field in prepared.columns:
                            prepared['total_venta'] = prepared[alt_field]
                            logger.info(f"🔧 KIOSKO: Usando campo alternativo {alt_field} → total_venta")
                            break
                    else:
                        logger.error(f"❌ KIOSKO: No se encontró campo de valor válido")
                        prepared['total_venta'] = 0
                else:
                    logger.warning(f"⚠️ Campo de valor no encontrado en {self.client_type}, usando 0")
                    prepared['total_venta'] = 0
        else:
            # 🆕 VALIDACIÓN ADICIONAL: Verificar que total_venta tenga valores válidos
            if prepared['total_venta'].isna().all() or (prepared['total_venta'] == 0).all():
                logger.warning(f"⚠️ {self.client_type}: total_venta existe pero todos los valores son 0 o nulos")
                
                # Para KIOSKO, intentar rescatar desde campos originales
                if self.client_type == 'KIOSKO':
                    rescue_fields = ['Costo Total', 'costo_total', 'valor']
                    for rescue_field in rescue_fields:
                        if rescue_field in prepared.columns:
                            rescue_values = pd.to_numeric(prepared[rescue_field], errors='coerce')
                            if not rescue_values.isna().all() and not (rescue_values == 0).all():
                                prepared['total_venta'] = rescue_values
                                logger.info(f"🆘 KIOSKO: Valores rescatados desde {rescue_field}")
                                break
        
        # Limpiar valores monetarios
        prepared['total_venta'] = pd.to_numeric(prepared['total_venta'], errors='coerce').fillna(0)
        
        # 🔧 VALIDACIÓN FINAL para KIOSKO
        if self.client_type == 'KIOSKO':
            total_amount = prepared['total_venta'].sum()
            non_zero_count = (prepared['total_venta'] != 0).sum()
            logger.info(f"🔍 KIOSKO Validación: {non_zero_count} registros con valor ≠ 0, Total: ${total_amount:,.2f}")
            
            if total_amount == 0 and len(prepared) > 0:
                logger.error(f"🚨 KIOSKO ERROR CRÍTICO: Todos los valores son 0 después del mapeo")
                logger.error(f"   Campos disponibles: {list(prepared.columns)}")
                logger.error(f"   source_value_field configurado: {self.config.get('source_value_field', 'N/A')}")
        
        # Metadata
        prepared['source'] = self.client_type
        prepared['source_original_columns'] = str(list(df.columns))
        
        logger.info(f"✅ {self.client_type} preparado: {len(prepared)} registros válidos")
        return prepared
    
    def _prepare_looker_for_matching(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara datos Looker para el proceso de matching (MEJORADO)"""
        prepared = df.copy()
        
        # Verificar campo identificador
        if 'id_matching' not in prepared.columns:
            # Buscar campo identificador alternativo
            possible_id_fields = ['identificador_unico', 'pedido', 'ticket', 'folio']
            for field in possible_id_fields:
                if field in prepared.columns:
                    prepared['id_matching'] = prepared[field]
                    logger.info(f"🔧 Usando '{field}' como identificador en Looker")
                    break
            else:
                logger.error("❌ No se encontró campo identificador en Looker")
                raise ValueError("Campo identificador requerido en Looker")
        
        # Limpiar y convertir ID
        if prepared['id_matching'].dtype == 'object':  # Es string
            # Para IDs string, filtrar solo no vacíos
            prepared = prepared[prepared['id_matching'].notna()]
            prepared = prepared[prepared['id_matching'].astype(str).str.strip() != '']
            prepared = prepared[prepared['id_matching'].astype(str) != 'nan']
        else:
            # Para IDs numéricos, usar lógica original
            prepared['id_matching'] = pd.to_numeric(prepared['id_matching'], errors='coerce')
            prepared = prepared.dropna(subset=['id_matching'])
            prepared = prepared[prepared['id_matching'] > 0]
        
        # Estandarizar campo de valor
        if 'total_venta' not in prepared.columns:
            # Buscar campos de valor alternativos
            possible_value_fields = ['venta', 'importe', 'costo_total', 'total']
            for field in possible_value_fields:
                if field in prepared.columns:
                    prepared['total_venta'] = prepared[field]
                    logger.info(f"🔧 Usando '{field}' como valor en Looker")
                    break
            else:
                logger.warning("⚠️ Campo de valor no encontrado en Looker, usando 0")
                prepared['total_venta'] = 0
        
        # Limpiar valores
        prepared['total_venta'] = pd.to_numeric(prepared['total_venta'], errors='coerce').fillna(0)
        
        # Metadata
        prepared['source'] = 'LOOKER'
        prepared['looker_original_columns'] = str(list(df.columns))
        
        logger.info(f"✅ Looker preparado: {len(prepared)} registros válidos")
        return prepared
    
    def _perform_exact_matching(self, source_df: pd.DataFrame, looker_df: pd.DataFrame) -> pd.DataFrame:
        """Realiza matching exacto por identificador único (MEJORADO SIN DUPLICACIÓN)"""
        logger.info(f"🎯 Realizando matching exacto...")
        logger.info(f"   📊 Source: {len(source_df)} registros, IDs únicos: {source_df['id_matching'].nunique()}")
        logger.info(f"   📊 Looker: {len(looker_df)} registros, IDs únicos: {looker_df['id_matching'].nunique()}")
        
        # 🔧 FIX: Verificar duplicados ANTES del merge
        source_duplicates = source_df['id_matching'].duplicated().sum()
        looker_duplicates = looker_df['id_matching'].duplicated().sum()
        
        if source_duplicates > 0:
            logger.warning(f"⚠️ {self.client_type}: {source_duplicates} IDs duplicados detectados")
            
            # Para KIOSKO: los duplicados pueden ser líneas de un mismo ticket
            if self.client_type == 'KIOSKO':
                logger.info(f"🔧 KIOSKO: Agrupando registros con mismo ID...")
                
                # Agrupar por ID y sumar valores
                source_grouped = source_df.groupby('id_matching').agg({
                    'total_venta': 'sum',  # Sumar valores
                    'source': 'first',     # Tomar primer valor para campos de texto
                    'client_type': 'first',
                    'source_original_columns': 'first'
                }).reset_index()
                
                # Agregar otros campos numéricos si existen
                numeric_fields = source_df.select_dtypes(include=[np.number]).columns
                for field in numeric_fields:
                    if field not in ['total_venta'] and field in source_df.columns:
                        if field not in source_grouped.columns:
                            source_grouped[field] = source_df.groupby('id_matching')[field].sum().values
                
                # Agregar campos de texto (tomar primero)
                text_fields = source_df.select_dtypes(include=['object']).columns
                for field in text_fields:
                    if field not in ['id_matching', 'source', 'client_type', 'source_original_columns']:
                        if field not in source_grouped.columns:
                            source_grouped[field] = source_df.groupby('id_matching')[field].first().values
                
                logger.info(f"✅ KIOSKO agrupado: {len(source_df)} → {len(source_grouped)} registros únicos")
                source_for_merge = source_grouped
            else:
                source_for_merge = source_df.drop_duplicates(subset=['id_matching'], keep='first')
                logger.info(f"✅ Duplicados eliminados: {len(source_df)} → {len(source_for_merge)} registros")
        else:
            source_for_merge = source_df
        
        if looker_duplicates > 0:
            logger.warning(f"⚠️ Looker: {looker_duplicates} IDs duplicados detectados")
            looker_grouped = looker_df.groupby('id_matching').agg({
                'total_venta': 'sum',
                'source': 'first',
                'client_type': 'first'
            }).reset_index()
            
            # Agregar otros campos
            for col in looker_df.columns:
                if col not in ['id_matching', 'total_venta', 'source', 'client_type']:
                    if looker_df[col].dtype in ['int64', 'float64']:
                        looker_grouped[col] = looker_df.groupby('id_matching')[col].sum().values
                    else:
                        looker_grouped[col] = looker_df.groupby('id_matching')[col].first().values
            
            logger.info(f"✅ Looker agrupado: {len(looker_df)} → {len(looker_grouped)} registros únicos")
            looker_for_merge = looker_grouped
        else:
            looker_for_merge = looker_df
        
        # Merge por identificador único SIN DUPLICACIÓN
        exact_matches = pd.merge(
            source_for_merge, 
            looker_for_merge, 
            on='id_matching', 
            how='inner',
            suffixes=(f'_{self.client_type.lower()}', '_looker')
        )
        
        if len(exact_matches) > 0:
            exact_matches['match_type'] = 'EXACT'
            exact_matches['match_confidence'] = 100.0
            logger.info(f"   ✅ {len(exact_matches)} matches exactos encontrados")
            
            # Validar totales
            source_total = exact_matches[f'total_venta_{self.client_type.lower()}'].sum()
            looker_total = exact_matches['total_venta_looker'].sum()
            logger.info(f"   💰 Totales en matches: {self.client_type} ${source_total:,.2f} vs Looker ${looker_total:,.2f}")
        else:
            exact_matches = pd.DataFrame()
        
        return exact_matches    
    def _perform_fuzzy_matching(self, source_df: pd.DataFrame, looker_df: pd.DataFrame, 
                               exact_matches: pd.DataFrame) -> pd.DataFrame:
        """Realiza matching fuzzy para identificadores similares (MEJORADO)"""
        
        # Identificar IDs ya matcheados
        matched_ids = set()
        if len(exact_matches) > 0:
            matched_ids = set(exact_matches['id_matching'].unique())
        
        # Filtrar registros no matcheados
        unmatched_source = source_df[~source_df['id_matching'].isin(matched_ids)]
        unmatched_looker = looker_df[~looker_df['id_matching'].isin(matched_ids)]
        
        if len(unmatched_source) == 0 or len(unmatched_looker) == 0:
            return pd.DataFrame()
        
        fuzzy_matches = []
        threshold = self.config['fuzzy_threshold']
        
        logger.info(f"   🔍 Buscando matches fuzzy (umbral: {threshold}%)")
        
        # Realizar matching fuzzy optimizado
        for _, source_row in unmatched_source.iterrows():
            source_id = str(int(source_row['id_matching']))
            best_match = None
            best_score = 0
            
            for _, looker_row in unmatched_looker.iterrows():
                looker_id = str(int(looker_row['id_matching']))
                
                # Calcular múltiples tipos de similitud
                scores = [
                    fuzz.ratio(source_id, looker_id),
                    fuzz.partial_ratio(source_id, looker_id),
                    fuzz.token_sort_ratio(source_id, looker_id)
                ]
                
                max_score = max(scores)
                
                if max_score > best_score and max_score >= threshold:
                    best_score = max_score
                    best_match = looker_row.copy()
            
            if best_match is not None:
                # Crear registro de match fuzzy
                match_row = {}
                
                # Combinar datos de ambas fuentes
                for col in source_row.index:
                    match_row[f"{col}_{self.client_type.lower()}"] = source_row[col]
                
                for col in best_match.index:
                    match_row[f"{col}_looker"] = best_match[col]
                
                match_row['match_type'] = 'FUZZY'
                match_row['match_confidence'] = best_score
                match_row['id_matching'] = source_row['id_matching']
                
                fuzzy_matches.append(match_row)
                
                # Remover de candidatos para evitar matches múltiples
                unmatched_looker = unmatched_looker[unmatched_looker['id_matching'] != best_match['id_matching']]
        
        fuzzy_df = pd.DataFrame(fuzzy_matches) if fuzzy_matches else pd.DataFrame()
        
        if len(fuzzy_df) > 0:
            avg_confidence = fuzzy_df['match_confidence'].mean()
            logger.info(f"   📊 Confianza promedio fuzzy: {avg_confidence:.1f}%")
        
        return fuzzy_df
    
    def _combine_matches(self, exact_matches: pd.DataFrame, fuzzy_matches: pd.DataFrame) -> pd.DataFrame:
        """Combina matches exactos y fuzzy de manera segura"""
        
        matches = []
        
        if len(exact_matches) > 0:
            matches.append(exact_matches)
        
        if len(fuzzy_matches) > 0:
            matches.append(fuzzy_matches)
        
        if matches:
            combined = pd.concat(matches, ignore_index=True, sort=False)
            logger.info(f"   📊 Total matches combinados: {len(combined)}")
            return combined
        else:
            return pd.DataFrame()
    
    def _identify_missing_records(self, source_df: pd.DataFrame, looker_df: pd.DataFrame, 
                                 matches_df: pd.DataFrame) -> pd.DataFrame:
        """Identifica registros que no tienen match (MEJORADO)"""
        
        matched_ids = set()
        if len(matches_df) > 0:
            matched_ids = set(matches_df['id_matching'].unique())
        
        missing_records = []
        
        # Registros en fuente pero no en Looker
        missing_in_looker = source_df[~source_df['id_matching'].isin(matched_ids)]
        for _, row in missing_in_looker.iterrows():
            missing_record = self._create_missing_record(row, 'source', 'MISSING_IN_LOOKER')
            missing_records.append(missing_record)
        
        # Registros en Looker pero no en fuente
        missing_in_source = looker_df[~looker_df['id_matching'].isin(matched_ids)]
        for _, row in missing_in_source.iterrows():
            missing_record = self._create_missing_record(row, 'looker', f'MISSING_IN_{self.client_type}')
            missing_records.append(missing_record)
        
        missing_df = pd.DataFrame(missing_records) if missing_records else pd.DataFrame()
        
        if len(missing_df) > 0:
            missing_source = len(missing_in_source)
            missing_looker = len(missing_in_looker)
            logger.info(f"   ❌ Faltantes en Looker: {missing_looker}")
            logger.info(f"   ❌ Faltantes en {self.client_type}: {missing_source}")
        
        return missing_df
    
    def _create_missing_record(self, row: pd.Series, source_type: str, match_type: str) -> Dict:
        """Crea registro para datos faltantes de manera consistente"""
        
        missing_record = {
            'id_matching': row['id_matching'],
            'match_type': match_type,
            'match_confidence': 0
        }
        
        # Agregar campos con naming consistente
        if source_type == 'source':
            for col in row.index:
                missing_record[f"{col}_{self.client_type.lower()}"] = row[col]
                missing_record[f"{col}_looker"] = np.nan
        else:  # looker
            for col in row.index:
                missing_record[f"{col}_looker"] = row[col]
                missing_record[f"{col}_{self.client_type.lower()}"] = np.nan
        
        return missing_record
    
    def _calculate_differences(self, matches_df: pd.DataFrame, missing_df: pd.DataFrame) -> pd.DataFrame:
        """Calcula diferencias en valores con manejo robusto (MEJORADO)"""
        
        # Combinar todos los registros
        all_records = self._combine_matches(matches_df, missing_df) if len(missing_df) > 0 else matches_df
        
        if len(all_records) == 0:
            return pd.DataFrame()
        
        # Identificar columnas de valor con manejo flexible
        source_value_col = f'total_venta_{self.client_type.lower()}'
        looker_value_col = 'total_venta_looker'
        
        # Extraer valores con manejo de errores
        valor_source = self._extract_numeric_values(all_records, source_value_col)
        valor_looker = self._extract_numeric_values(all_records, looker_value_col)
        
        # Calcular diferencias
        all_records['valor_source_clean'] = valor_source
        all_records['valor_looker_clean'] = valor_looker
        all_records['diferencia_valor'] = valor_source - valor_looker
        all_records['diferencia_absoluta'] = abs(all_records['diferencia_valor'])
        
        # Calcular diferencia porcentual con manejo de división por cero
        all_records['diferencia_porcentaje'] = np.where(
            valor_source != 0,
            (all_records['diferencia_valor'] / valor_source) * 100,
            np.where(valor_looker != 0, 
                    np.where(valor_looker > 0, 100, -100), 
                    0)
        )
        
        return all_records
    
    def _extract_numeric_values(self, df: pd.DataFrame, column_name: str) -> pd.Series:
        """Extrae valores numéricos de una columna con manejo robusto"""
        
        if column_name in df.columns:
            values = pd.to_numeric(df[column_name], errors='coerce').fillna(0)
        else:
            # Buscar columnas similares
            possible_cols = [col for col in df.columns if 'total_venta' in col.lower()]
            if possible_cols:
                values = pd.to_numeric(df[possible_cols[0]], errors='coerce').fillna(0)
                logger.warning(f"⚠️ Usando columna alternativa: {possible_cols[0]} para {column_name}")
            else:
                values = pd.Series([0] * len(df))
                logger.warning(f"⚠️ Columna {column_name} no encontrada, usando valores 0")
        
        return values
    
    def _categorize_results(self, results_df: pd.DataFrame) -> pd.DataFrame:
        """Categoriza los resultados según las tolerancias del cliente (MEJORADO)"""
        
        if len(results_df) == 0:
            return results_df
        
        tolerance_pct = self.config['tolerance_percentage']
        tolerance_abs = self.config['tolerance_absolute']
        
        def categorize_row(row):
            if row['match_type'].startswith('MISSING_'):
                return row['match_type']
            
            diff_abs = abs(row.get('diferencia_valor', 0))
            diff_pct = abs(row.get('diferencia_porcentaje', 0))
            
            if diff_abs == 0:
                return 'EXACT_MATCH'
            elif diff_pct <= tolerance_pct or diff_abs <= tolerance_abs:
                return 'WITHIN_TOLERANCE'
            elif diff_pct <= tolerance_pct * 3:  # 3x la tolerancia para diferencias menores
                return 'MINOR_DIFFERENCE'
            else:
                return 'MAJOR_DIFFERENCE'
        
        results_df['categoria'] = results_df.apply(categorize_row, axis=1)
        
        # Agregar descripción personalizada por cliente
        results_df['descripcion_categoria'] = results_df['categoria'].map(self.config['categories'])
        
        # Estadísticas por categoría
        category_counts = results_df['categoria'].value_counts()
        logger.info(f"   📊 Categorización completada:")
        for category, count in category_counts.items():
            description = self.config['categories'].get(category, category)
            logger.info(f"      {description}: {count}")
        
        return results_df
    
    def _calculate_summary_stats(self):
        """Calcula estadísticas resumen con nombres personalizados (MEJORADO)"""
        
        if self.reconciliation_results is None or len(self.reconciliation_results) == 0:
            self.summary_stats = {}
            return
        
        df = self.reconciliation_results
        
        # Conteo por categorías
        category_counts = df['categoria'].value_counts().to_dict()
        
        # Estadísticas financieras
        total_source = df['valor_source_clean'].sum()
        total_looker = df['valor_looker_clean'].sum()
        total_diferencia = df['diferencia_valor'].sum()
        
        # Estadísticas de diferencias
        numeric_differences = df[df['categoria'].isin(['WITHIN_TOLERANCE', 'MINOR_DIFFERENCE', 'MAJOR_DIFFERENCE'])]
        avg_diff_pct = numeric_differences['diferencia_porcentaje'].mean() if len(numeric_differences) > 0 else 0
        max_diff_abs = df['diferencia_absoluta'].max() if len(df) > 0 else 0
        
        # Calcular tasa de conciliación
        successful_matches = category_counts.get('EXACT_MATCH', 0) + category_counts.get('WITHIN_TOLERANCE', 0)
        total_records = len(df)
        reconciliation_rate = (successful_matches / total_records * 100) if total_records > 0 else 0
        
        # Crear resumen con nombres personalizados
        self.summary_stats = {
            'client_type': self.client_type,
            'total_records': total_records,
            'exact_matches': category_counts.get('EXACT_MATCH', 0),
            'within_tolerance': category_counts.get('WITHIN_TOLERANCE', 0),
            'minor_differences': category_counts.get('MINOR_DIFFERENCE', 0),
            'major_differences': category_counts.get('MAJOR_DIFFERENCE', 0),
            f'missing_in_{self.client_type.lower()}': category_counts.get(f'MISSING_IN_{self.client_type}', 0),
            'missing_in_looker': category_counts.get('MISSING_IN_LOOKER', 0),
            f'total_valor_{self.client_type.lower()}': total_source,
            'total_valor_looker': total_looker,
            'total_diferencia': total_diferencia,
            'avg_diferencia_porcentaje': avg_diff_pct,
            'max_diferencia_abs': max_diff_abs,
            'reconciliation_rate': reconciliation_rate,
            'successful_matches': successful_matches,
            'tolerance_percentage': self.config['tolerance_percentage'],
            'tolerance_absolute': self.config['tolerance_absolute']
        }
    
    def _log_reconciliation_summary(self):
        """Registra resumen detallado de la conciliación"""
        
        if not self.summary_stats:
            return
        
        stats = self.summary_stats
        unit_name = self.config['unit_name']
        
        logger.info(f"📈 RESUMEN DE CONCILIACIÓN {self.client_type}")
        logger.info("-" * 50)
        logger.info(f"📊 Total {unit_name}: {stats['total_records']}")
        logger.info(f"✅ Conciliados exactos: {stats['exact_matches']}")
        logger.info(f"🟢 Dentro de tolerancia: {stats['within_tolerance']}")
        logger.info(f"🟡 Diferencias menores: {stats['minor_differences']}")
        logger.info(f"🔴 Diferencias mayores: {stats['major_differences']}")
        logger.info(f"❌ Faltantes en Looker: {stats['missing_in_looker']}")
        logger.info(f"❌ Faltantes en {self.client_type}: {stats[f'missing_in_{self.client_type.lower()}']}")
        logger.info(f"🎯 Tasa de éxito: {stats['reconciliation_rate']:.1f}%")
        
        currency = self.config['currency_symbol']
        logger.info(f"💰 Total {self.client_type}: {currency}{stats[f'total_valor_{self.client_type.lower()}']:,.2f}")
        logger.info(f"💰 Total Looker: {currency}{stats['total_valor_looker']:,.2f}")
        logger.info(f"📊 Diferencia neta: {currency}{stats['total_diferencia']:,.2f}")
    
    # Métodos públicos para acceso a resultados
    def get_summary_stats(self) -> Dict:
        """Obtiene las estadísticas resumen de la conciliación"""
        return self.summary_stats or {}
    
    def get_results_by_category(self, category: str) -> pd.DataFrame:
        """Obtiene resultados filtrados por categoría"""
        if self.reconciliation_results is None:
            return pd.DataFrame()
        
        return self.reconciliation_results[self.reconciliation_results['categoria'] == category]
    
    def get_billing_ready_records(self) -> pd.DataFrame:
        """Obtiene registros listos para facturación (exactos + dentro de tolerancia)"""
        if self.reconciliation_results is None:
            return pd.DataFrame()
        
        approved_categories = ['EXACT_MATCH', 'WITHIN_TOLERANCE']
        return self.reconciliation_results[
            self.reconciliation_results['categoria'].isin(approved_categories)
        ]
    
    def get_differences_requiring_attention(self) -> pd.DataFrame:
        """Obtiene registros con diferencias que requieren atención"""
        if self.reconciliation_results is None:
            return pd.DataFrame()
        
        attention_categories = ['MAJOR_DIFFERENCE', 'MISSING_IN_LOOKER', f'MISSING_IN_{self.client_type}']
        return self.reconciliation_results[
            self.reconciliation_results['categoria'].isin(attention_categories)
        ]
    
    def export_reconciliation_summary(self) -> Dict:
        """Exporta un resumen completo para reportes"""
        
        if not self.summary_stats:
            return {}
        
        summary = self.summary_stats.copy()
        summary.update({
            'client_config': self.config,
            'timestamp': datetime.now().isoformat(),
            'unit_name': self.config['unit_name'],
            'identifier_display': self.config['identifier_display']
        })
        
        return summary