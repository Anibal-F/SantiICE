"""
Procesador específico para archivos OXXO - VERSIÓN CORREGIDA
Adaptado para nueva estructura CON NORMALIZACIÓN DE CAMPOS
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import re

# Imports
try:
    from config import config
except ImportError:
    # Fallback para desarrollo
    import sys
    import os
    # Subir dos niveles desde src/processors/ hasta la raíz
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from config import config

logger = logging.getLogger(__name__)

class DataProcessor:
    """Clase principal para procesamiento de datos OXXO - VERSIÓN CORREGIDA"""
    
    def __init__(self):
        """Inicializa el procesador de datos OXXO"""
        self.client_name = "OXXO"
        self.oxxo_data = None
        self.looker_data = None
        self.processed_oxxo = None
        self.processed_looker = None
        self.processing_stats = {}
        
    def load_oxxo_file(self, file_path: str) -> pd.DataFrame:
        """Carga y limpia el archivo de OXXO"""
        logger.info(f"📁 Cargando archivo OXXO: {file_path}")
        
        try:
            df = pd.read_excel(file_path, header=None)
            logger.info(f"✅ Archivo OXXO cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
            
            cleaned_df = self._clean_oxxo_data(df)
            self.oxxo_data = cleaned_df
            
            self.processing_stats['oxxo_original_rows'] = len(df)
            self.processing_stats['oxxo_cleaned_rows'] = len(cleaned_df)
            
            logger.info(f"✅ OXXO procesado: {len(cleaned_df)} registros únicos")
            return cleaned_df
            
        except Exception as e:
            logger.error(f"❌ Error al cargar archivo OXXO: {e}")
            raise
    
    def _clean_oxxo_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia los datos del archivo OXXO"""
        logger.info("🧹 Limpiando datos OXXO...")
        
        try:
            valid_records = []
            
            for i, row in df.iterrows():
                try:
                    row_values = [str(val) if pd.notna(val) else '' for val in row]
                    
                    if len(row_values) > 0 and 'RECEPCIONES' in row_values[0]:
                        if len(row_values) >= 8:
                            pedido_val = row_values[4] if len(row_values) > 4 else ''
                            valor_val = row_values[7] if len(row_values) > 7 else ''
                            
                            if (pedido_val not in ['', 'nan', 'None'] and 
                                valor_val not in ['', 'nan', 'None']):
                                
                                try:
                                    pedido_num = float(str(pedido_val).replace(',', ''))
                                    valor_num = float(str(valor_val).replace(',', '').replace('$', ''))
                                    
                                    if pedido_num > 0 and valor_num >= 0:
                                        record = {
                                            'cve_movimiento': row_values[0],
                                            'tienda': row_values[1],
                                            'recibo': row_values[2],
                                            'orden': row_values[3],
                                            'pedido_adicional': pedido_num,
                                            'remision': row_values[5],
                                            'fecha': row_values[6],
                                            'valor': valor_num,
                                            'iva': float(str(row_values[8]).replace(',', '')) if len(row_values) > 8 and str(row_values[8]) not in ['', 'nan', 'None'] else 0,
                                            'neto': float(str(row_values[9]).replace(',', '')) if len(row_values) > 9 and str(row_values[9]) not in ['', 'nan', 'None'] else 0
                                        }
                                        valid_records.append(record)
                                except (ValueError, TypeError):
                                    continue
                except Exception:
                    continue
            
            if valid_records:
                cleaned_df = pd.DataFrame(valid_records)
                
                # Limpiar nombres de tienda
                if 'tienda' in cleaned_df.columns:
                    cleaned_df['tienda'] = cleaned_df['tienda'].astype(str).str.replace(r'^\d+-', '', regex=True).str.strip()
                
                # Convertir fecha
                if 'fecha' in cleaned_df.columns:
                    try:
                        cleaned_df['fecha'] = pd.to_datetime(cleaned_df['fecha'], errors='coerce')
                    except:
                        pass
                
                logger.info(f"✅ OXXO limpieza completada: {len(cleaned_df)} registros válidos")
                return cleaned_df
            else:
                logger.warning("❌ No se encontraron registros válidos en OXXO")
                return pd.DataFrame(columns=['cve_movimiento', 'tienda', 'pedido_adicional', 'valor', 'iva', 'neto'])
                
        except Exception as e:
            logger.error(f"❌ Error en limpieza OXXO: {e}")
            return pd.DataFrame(columns=['cve_movimiento', 'tienda', 'pedido_adicional', 'valor', 'iva', 'neto'])
    
    def load_looker_file(self, file_path: str, client_filter: Optional[str] = None) -> pd.DataFrame:
        """Carga y procesa archivo de Looker CON AGRUPACIÓN CORREGIDA"""
        logger.info(f"📊 Cargando y agrupando archivo Looker: {file_path}")
        
        try:
            # Leer archivo Excel
            df = pd.read_excel(file_path, header=0)
            logger.info(f"✅ Archivo Looker cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
            
            self.processing_stats['looker_original_rows'] = len(df)
            
            # Filtrar por cliente ANTES de la agrupación
            if client_filter:
                if 'Cliente' in df.columns:
                    initial_count = len(df)
                    df = df[df['Cliente'].astype(str).str.upper() == client_filter.upper()]
                    logger.info(f"🎯 Filtrado por cliente {client_filter}: {len(df)} de {initial_count} registros")
            
            # APLICAR AGRUPACIÓN CORREGIDA
            logger.info("🔧 INICIANDO AGRUPACIÓN CORREGIDA...")
            processed_df = self._group_looker_data_fixed(df)
            
            self.looker_data = processed_df
            self.processing_stats['looker_processed_rows'] = len(processed_df)
            
            logger.info(f"✅ Looker procesado: {len(processed_df)} registros AGRUPADOS")
            return processed_df
            
        except Exception as e:
            logger.error(f"❌ Error al cargar archivo Looker: {e}")
            raise
    
    def _group_looker_data_fixed(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        AGRUPACIÓN CORREGIDA - Versión que realmente funciona
        """
        logger.info("🔧 EJECUTANDO AGRUPACIÓN CORREGIDA...")
        
        if len(df) == 0:
            logger.warning("❌ DataFrame Looker está vacío")
            return df
        
        try:
            # PASO 1: Identificar campo de agrupación
            group_field = self._find_grouping_field_fixed(df)
            if not group_field:
                logger.error("❌ No se pudo identificar campo de agrupación")
                return df
            
            logger.info(f"🎯 Campo de agrupación: '{group_field}'")
            
            # PASO 2: Limpiar datos
            df_clean = df.copy()
            df_clean[group_field] = pd.to_numeric(df_clean[group_field], errors='coerce')
            df_clean = df_clean.dropna(subset=[group_field])
            df_clean = df_clean[df_clean[group_field] > 0]
            
            original_count = len(df_clean)
            unique_count = df_clean[group_field].nunique()
            
            logger.info(f"📊 Registros para agrupar: {original_count}")
            logger.info(f"📊 IDs únicos detectados: {unique_count}")
            
            # PASO 3: AGRUPACIÓN CORREGIDA
            logger.info("🔧 Ejecutando agrupación pandas...")
            
            # Configurar agregaciones CORRECTAMENTE
            agg_functions = {}
            
            # Campos numéricos - SUMAR
            if 'Venta' in df_clean.columns:
                agg_functions['Venta'] = 'sum'  # SUMAR ventas
            
            if 'Número de piezas entregadas' in df_clean.columns:
                agg_functions['Número de piezas entregadas'] = 'sum'  # SUMAR piezas
            
            # Campos de texto - PRIMER valor
            text_fields = ['Cliente', 'Sucursal OXXO (Filtrado)', 'Sucursal KIOSKO (Filtrado)', 'Remisión (Filtrado)']
            for field in text_fields:
                if field in df_clean.columns:
                    agg_functions[field] = 'first'
            
            # Productos - CONCATENAR únicos
            if 'Producto' in df_clean.columns:
                agg_functions['Producto'] = lambda x: ' + '.join(sorted(x.dropna().astype(str).unique()))
            
            # Fechas
            if 'Submitted at' in df_clean.columns:
                agg_functions['Submitted at'] = 'first'
            
            # EJECUTAR AGRUPACIÓN
            logger.info(f"🔧 Agrupando por '{group_field}' con {len(agg_functions)} funciones...")
            grouped_df = df_clean.groupby(group_field).agg(agg_functions).reset_index()
            
            # PASO 4: Agregar columna de conteo DESPUÉS de la agrupación
            count_by_id = df_clean.groupby(group_field).size().reset_index(name='productos_agrupados')
            grouped_df = grouped_df.merge(count_by_id, on=group_field, how='left')
            
            # PASO 5: Renombrar columnas para consistencia
            rename_map = {group_field: 'identificador_unico'}
            
            if 'Venta' in grouped_df.columns:
                rename_map['Venta'] = 'total_venta'
            
            if 'Número de piezas entregadas' in grouped_df.columns:
                rename_map['Número de piezas entregadas'] = 'total_piezas'
            
            # Renombrar sucursal
            for col in grouped_df.columns:
                if 'Sucursal' in col and ('OXXO' in col or 'KIOSKO' in col):
                    rename_map[col] = 'sucursal'
                    break
            
            grouped_df = grouped_df.rename(columns=rename_map)
            
            # PASO 6: Validar tipos de datos
            if 'total_venta' in grouped_df.columns:
                grouped_df['total_venta'] = pd.to_numeric(grouped_df['total_venta'], errors='coerce').fillna(0)
            
            if 'total_piezas' in grouped_df.columns:
                grouped_df['total_piezas'] = pd.to_numeric(grouped_df['total_piezas'], errors='coerce').fillna(0)
            
            # PASO 7: VERIFICAR QUE LA AGRUPACIÓN FUNCIONÓ
            final_count = len(grouped_df)
            records_grouped = original_count - final_count
            
            logger.info(f"🎉 AGRUPACIÓN COMPLETADA:")
            logger.info(f"   📊 Registros originales: {original_count}")
            logger.info(f"   📊 Registros finales: {final_count}")
            logger.info(f"   📦 Registros consolidados: {records_grouped}")
            
            if records_grouped > 0:
                logger.info(f"✅ ¡AGRUPACIÓN EXITOSA! Se consolidaron {records_grouped} registros")
                
                # Mostrar ejemplos
                multi_product = grouped_df[grouped_df['productos_agrupados'] > 1]
                if len(multi_product) > 0:
                    logger.info(f"📦 Pedidos con múltiples productos: {len(multi_product)}")
                    
                    logger.info("🔍 Ejemplos de agrupación exitosa:")
                    for _, row in multi_product.head(3).iterrows():
                        logger.info(f"   ID: {row['identificador_unico']}, "
                                  f"Productos: {row['productos_agrupados']}, "
                                  f"Total: ${row.get('total_venta', 0):,.2f}")
            else:
                logger.warning("⚠️ NO se consolidaron registros - todos eran únicos")
            
            return grouped_df
            
        except Exception as e:
            logger.error(f"❌ ERROR CRÍTICO en agrupación: {e}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            
            # Retornar datos sin agrupar como fallback
            logger.warning("🔄 Retornando datos sin agrupar como fallback")
            return df
    
    def _find_grouping_field_fixed(self, df: pd.DataFrame) -> Optional[str]:
        """Encuentra el campo correcto para agrupación"""
        
        # Candidatos por prioridad
        candidates = [
            'No. Pedido (Filtrado)',
            'Folio del Ticket (Filtrado)',
            'No. Pedido',
            'Folio del Ticket',
            'identificador_unico'
        ]
        
        # Buscar por nombre exacto
        for candidate in candidates:
            if candidate in df.columns:
                logger.info(f"✅ Campo encontrado por nombre exacto: '{candidate}'")
                return candidate
        
        # Buscar por patrón
        for col in df.columns:
            col_lower = col.lower()
            if ('pedido' in col_lower or 'folio' in col_lower) and 'filtrado' in col_lower:
                logger.info(f"✅ Campo encontrado por patrón: '{col}'")
                return col
        
        logger.error("❌ No se encontró campo de agrupación")
        return None
    
    def _normalize_oxxo_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        🔧 NUEVO: Normaliza campos OXXO para el reconciler
        Convierte campos específicos de OXXO a campos estándar
        """
        logger.info("🔧 Normalizando campos OXXO...")
        
        df_normalized = df.copy()
        
        # 1. Crear id_matching desde pedido_adicional
        if 'pedido_adicional' in df.columns:
            df_normalized['id_matching'] = pd.to_numeric(df['pedido_adicional'], errors='coerce')
            logger.info(f"   ✅ id_matching creado desde pedido_adicional")
        else:
            logger.error(f"   ❌ Campo pedido_adicional no encontrado en OXXO")
            df_normalized['id_matching'] = range(1, len(df) + 1)  # Fallback
        
        # 2. Crear total_venta desde valor
        if 'valor' in df.columns:
            df_normalized['total_venta'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            logger.info(f"   ✅ total_venta creado desde valor")
        else:
            logger.error(f"   ❌ Campo valor no encontrado en OXXO")
            df_normalized['total_venta'] = 0  # Fallback
        
        # 3. Limpiar y validar id_matching
        df_normalized = df_normalized.dropna(subset=['id_matching'])
        df_normalized = df_normalized[df_normalized['id_matching'] > 0]
        
        # 4. Agregar metadata
        df_normalized['source'] = 'OXXO'
        df_normalized['client_type'] = 'OXXO'
        df_normalized['source_original_columns'] = str(list(df.columns))
        
        logger.info(f"   📊 OXXO normalizado: {len(df_normalized)} registros válidos")
        
        # Mostrar muestra
        if len(df_normalized) > 0:
            sample = df_normalized[['id_matching', 'total_venta']].head(3)
            logger.info(f"   🔍 Muestra normalizada:")
            for _, row in sample.iterrows():
                logger.info(f"      ID: {row['id_matching']}, Valor: ${row['total_venta']:,.2f}")
        
        return df_normalized

    def _normalize_looker_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        🔧 NUEVO: Normaliza campos Looker para el reconciler
        """
        logger.info("🔧 Normalizando campos Looker...")
        
        df_normalized = df.copy()
        
        # 1. Crear id_matching desde identificador_unico
        if 'identificador_unico' in df.columns:
            df_normalized['id_matching'] = pd.to_numeric(df['identificador_unico'], errors='coerce')
            logger.info(f"   ✅ id_matching creado desde identificador_unico")
        else:
            logger.error(f"   ❌ Campo identificador_unico no encontrado en Looker")
            
            # Buscar campos alternativos
            possible_id_fields = ['No. Pedido (Filtrado)', 'Folio del Ticket (Filtrado)', 'pedido', 'folio']
            for field in possible_id_fields:
                if field in df.columns:
                    df_normalized['id_matching'] = pd.to_numeric(df[field], errors='coerce')
                    logger.info(f"   ✅ id_matching creado desde {field}")
                    break
            else:
                logger.error(f"   ❌ No se encontró campo de identificación en Looker")
                df_normalized['id_matching'] = range(1, len(df) + 1)  # Fallback
        
        # 2. Usar total_venta si ya existe, sino crear desde 'Venta'
        if 'total_venta' not in df.columns:
            if 'Venta' in df.columns:
                df_normalized['total_venta'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
                logger.info(f"   ✅ total_venta creado desde Venta")
            else:
                logger.error(f"   ❌ Campo Venta no encontrado en Looker")
                df_normalized['total_venta'] = 0  # Fallback
        
        # 3. Limpiar y validar id_matching
        df_normalized = df_normalized.dropna(subset=['id_matching'])
        df_normalized = df_normalized[df_normalized['id_matching'] > 0]
        
        # 4. Agregar metadata
        df_normalized['source'] = 'LOOKER'
        df_normalized['client_type'] = 'OXXO'  # Cliente al que pertenecen los datos
        df_normalized['looker_original_columns'] = str(list(df.columns))
        
        logger.info(f"   📊 Looker normalizado: {len(df_normalized)} registros válidos")
        
        # Mostrar muestra
        if len(df_normalized) > 0:
            sample = df_normalized[['id_matching', 'total_venta']].head(3)
            logger.info(f"   🔍 Muestra normalizada:")
            for _, row in sample.iterrows():
                logger.info(f"      ID: {row['id_matching']}, Valor: ${row['total_venta']:,.2f}")
        
        return df_normalized
    
    def save_processed_data(self, timestamp: str = None) -> Dict[str, str]:
        """Guarda los datos procesados"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        saved_files = {}
        processed_dir = Path(config.get_processed_dir())
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar OXXO
        if self.processed_oxxo is not None and len(self.processed_oxxo) > 0:
            oxxo_path = processed_dir / f"oxxo_processed_{timestamp}.xlsx"
            self.processed_oxxo.to_excel(oxxo_path, index=False)
            saved_files['oxxo'] = str(oxxo_path)
            logger.info(f"💾 OXXO guardado: {oxxo_path}")
        
        # Guardar Looker
        if self.processed_looker is not None and len(self.processed_looker) > 0:
            looker_path = processed_dir / f"looker_processed_{timestamp}.xlsx"
            self.processed_looker.to_excel(looker_path, index=False)
            saved_files['looker'] = str(looker_path)
            logger.info(f"💾 Looker guardado: {looker_path}")
        
        return saved_files
    
    def get_processing_summary(self) -> Dict[str, any]:
        """Genera resumen del procesamiento"""
        summary = {
            'client_type': 'OXXO',
            'timestamp': datetime.now().isoformat(),
            'oxxo_records': len(self.processed_oxxo) if self.processed_oxxo is not None else 0,
            'looker_records': len(self.processed_looker) if self.processed_looker is not None else 0,
            'oxxo_columns': list(self.processed_oxxo.columns) if self.processed_oxxo is not None else [],
            'looker_columns': list(self.processed_looker.columns) if self.processed_looker is not None else [],
            'processing_stats': self.processing_stats.copy()
        }
        
        # Estadísticas de agrupación
        if self.processed_looker is not None and 'productos_agrupados' in self.processed_looker.columns:
            agrupados = self.processed_looker[self.processed_looker['productos_agrupados'] > 1]
            summary['looker_grouping_stats'] = {
                'registros_agrupados': len(agrupados),
                'registros_unicos': len(self.processed_looker[self.processed_looker['productos_agrupados'] == 1]),
                'total_productos_consolidados': agrupados['productos_agrupados'].sum() if len(agrupados) > 0 else 0,
                'agrupacion_exitosa': len(agrupados) > 0
            }
        
        return summary
    
    def process_files(self, oxxo_file: str, looker_file: str, client_filter: str = 'OXXO') -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Procesa ambos archivos con agrupación GARANTIZADA Y NORMALIZACIÓN"""
        
        logger.info("🚀 INICIANDO PROCESAMIENTO OXXO CON AGRUPACIÓN CORREGIDA")
        logger.info("=" * 60)
        
        # Procesar OXXO
        logger.info("📁 PROCESANDO ARCHIVO OXXO")
        logger.info("-" * 30)
        self.processed_oxxo = self.load_oxxo_file(oxxo_file)
        
        # Procesar Looker CON AGRUPACIÓN CORREGIDA
        logger.info("\n📊 PROCESANDO ARCHIVO LOOKER CON AGRUPACIÓN CORREGIDA")
        logger.info("-" * 50)
        self.processed_looker = self.load_looker_file(looker_file, client_filter)
        
        # 🔧 NUEVO: NORMALIZAR CAMPOS PARA RECONCILER
        logger.info("\n🔧 NORMALIZANDO CAMPOS PARA RECONCILER")
        logger.info("-" * 40)
        
        # Normalizar datos OXXO
        if self.processed_oxxo is not None and len(self.processed_oxxo) > 0:
            self.processed_oxxo = self._normalize_oxxo_fields(self.processed_oxxo)
            logger.info(f"✅ OXXO normalizado: {len(self.processed_oxxo)} registros")
        
        # Normalizar datos Looker
        if self.processed_looker is not None and len(self.processed_looker) > 0:
            self.processed_looker = self._normalize_looker_fields(self.processed_looker)
            logger.info(f"✅ Looker normalizado: {len(self.processed_looker)} registros")
        
        # Verificación final CRÍTICA
        logger.info("\n🔍 VERIFICACIÓN FINAL CRÍTICA")
        logger.info("-" * 30)
        
        summary = self.get_processing_summary()
        
        logger.info(f"📊 OXXO: {summary['oxxo_records']} registros")
        logger.info(f"📊 Looker: {summary['looker_records']} registros")
        
        # VERIFICAR QUE LA AGRUPACIÓN FUNCIONÓ
        original_looker = self.processing_stats.get('looker_original_rows', 0)
        final_looker = summary['looker_records']
        
        if original_looker > final_looker:
            logger.info(f"✅ AGRUPACIÓN CONFIRMADA: {original_looker} → {final_looker} registros")
            
            if 'looker_grouping_stats' in summary:
                grouping = summary['looker_grouping_stats']
                if grouping['agrupacion_exitosa']:
                    logger.info(f"✅ Registros con múltiples productos: {grouping['registros_agrupados']}")
                    logger.info(f"✅ Total productos consolidados: {grouping['total_productos_consolidados']}")
                else:
                    logger.warning("⚠️ No se detectaron productos múltiples")
        else:
            logger.error(f"❌ AGRUPACIÓN FALLÓ: {original_looker} = {final_looker} registros")
            logger.error("💡 Esto indica que NO se consolidaron registros duplicados")
        
        # 🔧 VERIFICAR CAMPOS PARA RECONCILER
        logger.info("\n🔍 VERIFICANDO CAMPOS PARA RECONCILER")
        logger.info("-" * 35)
        
        required_fields = ['id_matching', 'total_venta']
        
        for dataset_name, dataset in [('OXXO', self.processed_oxxo), ('Looker', self.processed_looker)]:
            if dataset is not None and len(dataset) > 0:
                for field in required_fields:
                    if field in dataset.columns:
                        sample_values = dataset[field].dropna().head(3).tolist()
                        logger.info(f"   ✅ {dataset_name}.{field}: {sample_values}")
                    else:
                        logger.error(f"   ❌ {dataset_name}.{field}: FALTANTE")
            else:
                logger.warning(f"   ⚠️ {dataset_name}: Dataset vacío")
        
        logger.info("\n🎉 PROCESAMIENTO COMPLETADO")
        logger.info("=" * 60)
        
        return self.processed_oxxo, self.processed_looker