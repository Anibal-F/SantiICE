"""
Módulo para detectar automáticamente el tipo de ticket (OXXO o KIOSKO)
basado en patrones presentes en el texto OCR.
Versión mejorada con más patrones y mejor lógica de decisión.
"""

def validate_ticket_content(ocr_text, detected_type):
    """
    Valida que el contenido del ticket sea consistente con el tipo detectado.
    
    Args:
        ocr_text: Texto del OCR
        detected_type: Tipo detectado ("OXXO" o "KIOSKO")
        
    Returns:
        tuple: (es_valido, confianza, observaciones)
    """
    text_upper = ocr_text.upper()
    observaciones = []
    confianza = 100
    
    if detected_type == "KIOSKO":
        # Validaciones específicas para KIOSKO
        if "FOLIO:" not in text_upper:
            observaciones.append("Falta patrón 'FOLIO:' típico de KIOSKO")
            confianza -= 20
        
        if not any(codigo in text_upper for codigo in ["7500465096004", "7500465096011"]):
            observaciones.append("No se encontraron códigos de producto esperados")
            confianza -= 15
        
        if "GAS" not in text_upper:
            observaciones.append("Falta referencia a estación de gas")
            confianza -= 10
            
    elif detected_type == "OXXO":
        # Validaciones específicas para OXXO
        if "TIENDA:" not in text_upper and "PLAZA:" not in text_upper:
            observaciones.append("Falta información de tienda/plaza típica de OXXO")
            confianza -= 15
        
        if "REMISION" not in text_upper and "PEDIDO" not in text_upper:
            observaciones.append("Falta información de remisión/pedido")
            confianza -= 20
        
        if not any(patron in text_upper for patron in ["UDS", "U.COM", "VAL.TOT"]):
            observaciones.append("Falta estructura de columnas típica de OXXO")
            confianza -= 10
    
    es_valido = confianza >= 60
    
    if observaciones:
        print(f"⚠️ Validación del ticket {detected_type}:")
        for obs in observaciones:
            print(f"   - {obs}")
        print(f"   - Confianza final: {confianza}%")
    
    return es_valido, confianza, observaciones

def detect_ticket_type(ocr_text):
    """
    Detecta automáticamente si un ticket es de OXXO o KIOSKO basado en patrones en el texto.
    Versión mejorada con más patrones y mejor lógica de decisión.
    
    Args:
        ocr_text: Texto extraído del OCR
        
    Returns:
        str: "OXXO" o "KIOSKO"
    """
    # Convertir a mayúsculas para hacer la búsqueda insensible a mayúsculas/minúsculas
    text_upper = ocr_text.upper()
    
    # Patrones definitivos para KIOSKO (si aparece cualquiera, es KIOSKO seguro)
    kiosko_definitive = [
        "FOLIO:",
        "ENTRADA POR COMPRA",
        "GAS CARDONES",
        "GAS LOMAS",
        "SKUS",
        "TOTAL: UNIDADES"
    ]
    
    # Patrones definitivos para OXXO (si aparece cualquiera, es OXXO seguro)
    oxxo_definitive = [
        "PEDIDO ADICIONAL",
        "MOVTS. VALORIZADOS",
        "MOVIMIENTOS VALORIZADOS",
        "FOL-GOMA",
        "SUJETO A REVISION"
    ]
    
    # Verificar patrones definitivos primero
    for pattern in kiosko_definitive:
        if pattern in text_upper:
            print(f"🔍 Ticket detectado como KIOSKO (patrón definitivo: {pattern})")
            return "KIOSKO"
    
    for pattern in oxxo_definitive:
        if pattern in text_upper:
            print(f"🔍 Ticket detectado como OXXO (patrón definitivo: {pattern})")
            return "OXXO"
    
    # Patrones secundarios para KIOSKO
    kiosko_patterns = [
        "FOLIO ",
        "IMPUESTOS:",
        "SUBTOTAL:",
        "BOLSA DE HIELO SANTI ICE",
        "CODIGO DE BARRAS",
        "UNIDADES",
        "IMPORTE UNITARIO"
    ]
    
    # Patrones secundarios para OXXO
    oxxo_patterns = [
        "REMISION",
        "TIENDA:",
        "PLAZA:",
        "FECHA ADMVA",
        "ORDEN DE COMPRA",
        "UDS",
        "U.COM",
        "VAL.TOT",
        "VALTOT",
        "CUL"
    ]
    
    # Contar coincidencias para cada tipo
    kiosko_matches = sum(1 for pattern in kiosko_patterns if pattern in text_upper)
    oxxo_matches = sum(1 for pattern in oxxo_patterns if pattern in text_upper)
    
    # Calcular confianza (porcentaje de patrones que coinciden)
    kiosko_confidence = (kiosko_matches / len(kiosko_patterns)) * 100
    oxxo_confidence = (oxxo_matches / len(oxxo_patterns)) * 100
    
    # Imprimir información de diagnóstico
    print(f"📊 Detección automática:")
    print(f"   - KIOSKO: {kiosko_matches}/{len(kiosko_patterns)} patrones ({kiosko_confidence:.1f}%)")
    print(f"   - OXXO: {oxxo_matches}/{len(oxxo_patterns)} patrones ({oxxo_confidence:.1f}%)")
    
    # Análisis adicional por códigos de producto
    codigo_5kg = "7500465096004" in text_upper
    codigo_15kg = "7500465096011" in text_upper or "750046509601" in text_upper
    
    if codigo_5kg or codigo_15kg:
        print(f"🔍 Códigos de producto detectados: 5kg={codigo_5kg}, 15kg={codigo_15kg}")
        # Los códigos de producto aparecen más en tickets KIOSKO
        kiosko_matches += 2
        kiosko_confidence = (kiosko_matches / (len(kiosko_patterns) + 2)) * 100
    
    # Análisis por estructura de texto
    lines = text_upper.split('\n')
    
    # KIOSKO tiende a tener más líneas estructuradas
    if len(lines) > 20:
        kiosko_matches += 1
        print("🔍 Estructura de texto larga detectada (+1 KIOSKO)")
    
    # OXXO tiende a tener patrones de columnas específicos
    if any("UDS" in line and "COM" in line for line in lines):
        oxxo_matches += 2
        print("🔍 Estructura de columnas OXXO detectada (+2 OXXO)")
    
    # Recalcular confianzas
    kiosko_confidence = (kiosko_matches / (len(kiosko_patterns) + 3)) * 100
    oxxo_confidence = (oxxo_matches / (len(oxxo_patterns) + 2)) * 100
    
    print(f"📊 Confianza final: KIOSKO={kiosko_confidence:.1f}%, OXXO={oxxo_confidence:.1f}%")
    
    # Decisión final con umbral mínimo
    if kiosko_confidence > oxxo_confidence and kiosko_confidence > 15:
        print(f"🔍 Ticket detectado como KIOSKO ({kiosko_confidence:.1f}% confianza)")
        return "KIOSKO"
    elif oxxo_confidence > kiosko_confidence and oxxo_confidence > 15:
        print(f"🔍 Ticket detectado como OXXO ({oxxo_confidence:.1f}% confianza)")
        return "OXXO"
    else:
        # Si ambas confianzas son bajas, usar heurística adicional
        print("⚠️ Confianza baja en ambos tipos, aplicando heurística adicional...")
        
        # Heurística: OXXO es más común, usar como default si hay alguna evidencia
        if oxxo_matches > 0 or "TIENDA" in text_upper or "PLAZA" in text_upper:
            print("🔍 Ticket detectado como OXXO (heurística por defecto)")
            return "OXXO"
        else:
            print("🔍 Ticket detectado como KIOSKO (heurística alternativa)")
            return "KIOSKO"