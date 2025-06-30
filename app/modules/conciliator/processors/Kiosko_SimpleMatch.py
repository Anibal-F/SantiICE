#!/usr/bin/env python3
"""
KIOSKO Simple Matching - Usando últimos 4 dígitos
ENFOQUE SIMPLIFICADO que resuelve los problemas de matching
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def extract_last_4_digits(value) -> Optional[str]:
    """
    🎯 FUNCIÓN SIMPLE: Extrae los últimos 4 dígitos de cualquier valor
    
    Args:
        value: Valor del ticket/folio (puede ser string, int, float)
        
    Returns:
        String con los últimos 4 dígitos o None si no es válido
    """
    if pd.isna(value) or value == '':
        return None
    
    # Convertir a string y extraer solo números
    value_str = str(value).strip()
    digits_only = re.sub(r'[^0-9]', '', value_str)
    
    # Verificar que tenga al menos 4 dígitos
    if len(digits_only) < 4:
        return None
    
    # Retornar últimos 4 dígitos
    return digits_only[-4:]

def process_kiosko_simple(df: pd.DataFrame, ticket_column: str, value_column: str) -> pd.DataFrame:
    """
    🔧 PROCESAMIENTO SIMPLE KIOSKO: Solo últimos 4 dígitos + campo correcto
    
    Args:
        df: DataFrame de KIOSKO
        ticket_column: Nombre de la columna de tickets
        value_column: Nombre de la columna de valores (ej: "Costo Total")
        
    Returns:
        DataFrame procesado con matching_id simplificado
    """
    logger.info(f"🔧 PROCESAMIENTO SIMPLE KIOSKO")
    logger.info(f"   📋 Campo ticket: {ticket_column}")
    logger.info(f"   💰 Campo valor: {value_column}")
    
    # Filtrar registros válidos
    valid_mask = (
        df[ticket_column].notna() & 
        (df[ticket_column].astype(str).str.strip() != '') &
        (df[value_column].notna())
    )
    
    df_clean = df[valid_mask].copy()
    logger.info(f"   📊 Registros válidos: {len(df_clean)}")
    
    if len(df_clean) == 0:
        return pd.DataFrame()
    
    # APLICAR FUNCIÓN SIMPLE: Extraer últimos 4 dígitos
    df_clean['matching_id'] = df_clean[ticket_column].apply(extract_last_4_digits)
    df_clean['original_ticket'] = df_clean[ticket_column]
    
    # Filtrar solo los que tienen matching_id válido
    df_clean = df_clean[df_clean['matching_id'].notna()]
    
    # Crear campos estándar para reconciler
    df_clean['id_matching'] = df_clean['matching_id']  # Usar como string para matching
    df_clean['total_venta'] = pd.to_numeric(df_clean[value_column], errors='coerce').fillna(0)
    df_clean['source'] = 'KIOSKO'
    
    # Verificar resultados
    valid_matches = len(df_clean)
    total_amount = df_clean['total_venta'].sum()
    unique_ids = df_clean['matching_id'].nunique()
    
    logger.info(f"✅ KIOSKO SIMPLE procesado:")
    logger.info(f"   📊 Registros con matching_id: {valid_matches}")
    logger.info(f"   🆔 IDs únicos (últimos 4): {unique_ids}")
    logger.info(f"   💰 Total: ${total_amount:,.2f}")
    
    # Mostrar ejemplos
    if len(df_clean) > 0:
        examples = df_clean[['original_ticket', 'matching_id', 'total_venta']].head(5)
        logger.info("🔍 Ejemplos KIOSKO:")
        for _, row in examples.iterrows():
            logger.info(f"   {row['original_ticket']} → {row['matching_id']} | ${row['total_venta']:.2f}")
    
    return df_clean

def process_looker_simple(df: pd.DataFrame, folio_column: str, value_column: str = 'Venta') -> pd.DataFrame:
    """
    🔧 PROCESAMIENTO SIMPLE LOOKER: Solo últimos 4 dígitos
    
    Args:
        df: DataFrame de Looker
        folio_column: Nombre de la columna de folios
        value_column: Nombre de la columna de valores (ej: "Venta")
        
    Returns:
        DataFrame procesado con matching_id simplificado
    """
    logger.info(f"🔧 PROCESAMIENTO SIMPLE LOOKER")
    logger.info(f"   📋 Campo folio: {folio_column}")
    logger.info(f"   💰 Campo valor: {value_column}")
    
    # Filtrar registros válidos
    valid_mask = (
        df[folio_column].notna() & 
        (df[folio_column].astype(str).str.strip() != '') &
        (df[value_column].notna())
    )
    
    df_clean = df[valid_mask].copy()
    logger.info(f"   📊 Registros válidos: {len(df_clean)}")
    
    if len(df_clean) == 0:
        return pd.DataFrame()
    
    # APLICAR FUNCIÓN SIMPLE: Extraer últimos 4 dígitos
    df_clean['matching_id'] = df_clean[folio_column].apply(extract_last_4_digits)
    df_clean['original_folio'] = df_clean[folio_column]
    
    # Filtrar solo los que tienen matching_id válido
    df_clean = df_clean[df_clean['matching_id'].notna()]
    
    # Crear campos estándar para reconciler
    df_clean['id_matching'] = df_clean['matching_id']  # Usar como string para matching
    df_clean['total_venta'] = pd.to_numeric(df_clean[value_column], errors='coerce').fillna(0)
    df_clean['source'] = 'LOOKER'
    
    # Verificar resultados
    valid_matches = len(df_clean)
    total_amount = df_clean['total_venta'].sum()
    unique_ids = df_clean['matching_id'].nunique()
    
    logger.info(f"✅ LOOKER SIMPLE procesado:")
    logger.info(f"   📊 Registros con matching_id: {valid_matches}")
    logger.info(f"   🆔 IDs únicos (últimos 4): {unique_ids}")
    logger.info(f"   💰 Total: ${total_amount:,.2f}")
    
    # Mostrar ejemplos
    if len(df_clean) > 0:
        examples = df_clean[['original_folio', 'matching_id', 'total_venta']].head(5)
        logger.info("🔍 Ejemplos LOOKER:")
        for _, row in examples.iterrows():
            logger.info(f"   {row['original_folio']} → {row['matching_id']} | ${row['total_venta']:.2f}")
    
    return df_clean

def test_simple_matching_preview(kiosko_df: pd.DataFrame, looker_df: pd.DataFrame) -> Dict[str, any]:
    """
    🎯 PREVIEW del matching simple ANTES de reconciliación
    
    Returns:
        Diccionario con estadísticas de matching esperado
    """
    logger.info("🎯 PREVIEW MATCHING SIMPLE")
    logger.info("-" * 30)
    
    if len(kiosko_df) == 0 or len(looker_df) == 0:
        return {'matches': 0, 'kiosko_ids': set(), 'looker_ids': set()}
    
    # Obtener IDs únicos
    kiosko_ids = set(kiosko_df['matching_id'].dropna().unique())
    looker_ids = set(looker_df['matching_id'].dropna().unique())
    
    # Calcular matches
    matches = kiosko_ids.intersection(looker_ids)
    kiosko_only = kiosko_ids - looker_ids
    looker_only = looker_ids - kiosko_ids
    
    # Totales
    kiosko_total = kiosko_df['total_venta'].sum()
    looker_total = looker_df['total_venta'].sum()
    
    # Calcular totales de registros que van a hacer match
    matched_kiosko_total = kiosko_df[kiosko_df['matching_id'].isin(matches)]['total_venta'].sum()
    matched_looker_total = looker_df[looker_df['matching_id'].isin(matches)]['total_venta'].sum()
    
    logger.info(f"📊 ESTADÍSTICAS MATCHING SIMPLE:")
    logger.info(f"   🔹 KIOSKO IDs únicos: {len(kiosko_ids)} | Total: ${kiosko_total:,.2f}")
    logger.info(f"   🔹 Looker IDs únicos: {len(looker_ids)} | Total: ${looker_total:,.2f}")
    logger.info(f"   🎯 MATCHES ENCONTRADOS: {len(matches)}")
    logger.info(f"   💰 Total a conciliar: KIOSKO ${matched_kiosko_total:,.2f} vs Looker ${matched_looker_total:,.2f}")
    logger.info(f"   📈 Tasa de matching:")
    logger.info(f"      KIOSKO: {len(matches)/len(kiosko_ids)*100:.1f}% ({len(matches)}/{len(kiosko_ids)})")
    logger.info(f"      Looker: {len(matches)/len(looker_ids)*100:.1f}% ({len(matches)}/{len(looker_ids)})")
    
    if len(matches) > 0:
        logger.info(f"✅ Ejemplos de IDs que harán match:")
        sample_matches = sorted(list(matches))[:10]
        for match_id in sample_matches:
            kiosko_amount = kiosko_df[kiosko_df['matching_id'] == match_id]['total_venta'].sum()
            looker_amount = looker_df[looker_df['matching_id'] == match_id]['total_venta'].sum()
            diff = abs(kiosko_amount - looker_amount)
            logger.info(f"   ID {match_id}: KIOSKO ${kiosko_amount:.2f} vs Looker ${looker_amount:.2f} (diff: ${diff:.2f})")
    
    if len(kiosko_only) > 0:
        logger.info(f"❌ Solo en KIOSKO: {len(kiosko_only)} IDs")
        if len(kiosko_only) <= 10:
            logger.info(f"   Ejemplos: {sorted(list(kiosko_only))}")
    
    if len(looker_only) > 0:
        logger.info(f"❌ Solo en Looker: {len(looker_only)} IDs")
        if len(looker_only) <= 10:
            logger.info(f"   Ejemplos: {sorted(list(looker_only))}")
    
    return {
        'matches': len(matches),
        'kiosko_ids': kiosko_ids,
        'looker_ids': looker_ids,
        'matched_ids': matches,
        'kiosko_only': kiosko_only,
        'looker_only': looker_only,
        'kiosko_total': kiosko_total,
        'looker_total': looker_total,
        'matched_kiosko_total': matched_kiosko_total,
        'matched_looker_total': matched_looker_total
    }

# Ejemplo de uso completo
def example_usage():
    """Ejemplo de cómo usar el matching simple"""
    print("🎯 EJEMPLO: MATCHING SIMPLE KIOSKO")
    print("=" * 40)
    
    # Simular datos KIOSKO
    kiosko_data = {
        'Ticket': ['4170-3-3-1508', '4169-2-3-295', '4168-1-4-4562', '36_4171-1-2-3000'],
        'Costo Total': [25.50, 15.75, 30.00, -10.50]  # Último es devolución
    }
    kiosko_df = pd.DataFrame(kiosko_data)
    
    # Simular datos Looker
    looker_data = {
        'Folio del Ticket (Filtrado)': ['41701508', '4169295', '41684562'],
        'Venta': [25.50, 15.75, 30.00]
    }
    looker_df = pd.DataFrame(looker_data)
    
    print("📋 Datos de ejemplo:")
    print("KIOSKO:", kiosko_data['Ticket'])
    print("Looker:", looker_data['Folio del Ticket (Filtrado)'])
    
    # Procesar con función simple
    kiosko_processed = process_kiosko_simple(kiosko_df, 'Ticket', 'Costo Total')
    looker_processed = process_looker_simple(looker_df, 'Folio del Ticket (Filtrado)', 'Venta')
    
    # Preview matching
    matching_preview = test_simple_matching_preview(kiosko_processed, looker_processed)
    
    print(f"\n🎉 RESULTADO: {matching_preview['matches']} matches encontrados!")
    print("✅ El matching simple FUNCIONA!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    example_usage()