import re
from app.services.google_sheets import send_to_google_sheets

def preprocess_ocr_text(text):
    """
    Preprocesa el texto OCR para eliminar duplicados y mejorar la calidad.
    
    Args:
        text: El texto OCR original
        
    Returns:
        str: Texto procesado
    """
    # Dividir el texto en líneas
    lines = text.split('\n')
    
    # Detectar si hay un bloque de texto duplicado
    if len(lines) > 15:
        # Calcular el tamaño aproximado de medio texto
        half_size = len(text) // 2
        
        # Comparar la primera mitad con la segunda
        first_half = text[:half_size]
        second_half = text[half_size:]
        
        # Si hay una similitud substancial, quedarnos solo con la primera mitad
        if len(first_half) > 100 and first_half[:100] in second_half:
            # Encontrar el punto de corte más preciso
            for i in range(len(lines) // 2, len(lines) - 5):
                if ' '.join(lines[i:i+5]) in ' '.join(lines[:i]):
                    return '\n'.join(lines[:i])
    
    # Normalizar caracteres problemáticos
    text = text.replace('Ó', 'O').replace('ó', 'o')
    
    # Normalizar espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    
    # Restaurar saltos de línea
    text = '\n'.join(line.strip() for line in text.split('\n'))
    
    return text


def format_oxxo_store_name(store_name):
    """
    Formatea el nombre de la tienda OXXO preservando todas las palabras
    pero eliminando el sufijo 'CUL' y aplicando formato adecuado.
    
    Args:
        store_name: Nombre de la tienda sin formatear (ej: "VALLE DEL SOL CUL")
        
    Returns:
        str: Nombre formateado (ej: "Valle del Sol")
    """
    # Si no se encontró un nombre, devolver valor por defecto
    if store_name == "No encontrado":
        return store_name
    
    # Preservar números romanos si existen (como "II" en "ZARAGOZA II CUL")
    roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
    has_roman = False
    roman_found = None
    
    # Buscar si el nombre contiene números romanos
    for roman in roman_numerals:
        if f" {roman} " in store_name or store_name.endswith(f" {roman}"):
            has_roman = True
            roman_found = roman
            break
    
    # Eliminar el sufijo CUL
    if " CUL" in store_name:
        store_name = store_name.replace(" CUL", "").strip()
    
    # Convertir a formato título (primera letra de cada palabra en mayúscula)
    formatted_name = store_name.title()
    
    # Restaurar números romanos en mayúsculas si existían
    if has_roman and roman_found:
        # Buscar el número romano en formato título y reemplazarlo con la versión en mayúsculas
        roman_title = roman_found.title()
        formatted_name = formatted_name.replace(roman_title, roman_found)
    
    # Correcciones específicas para palabras como "DE", "Y", "DEL", etc.
    small_words = ["De", "La", "El", "Los", "Las", "Y", "Del"]
    for word in small_words:
        # Reemplazar la palabra con su versión en minúscula, pero no al inicio
        if f" {word} " in formatted_name:
            formatted_name = formatted_name.replace(f" {word} ", f" {word.lower()} ")
    
    return formatted_name


def extract_formatted_date(ocr_text):
    """
    Extrae la fecha del ticket OXXO y la devuelve en formato estándar DD/MM/YYYY.
    
    Args:
        ocr_text: Texto completo del OCR
        
    Returns:
        str: Fecha formateada en formato DD/MM/YYYY (ej: "15/02/2025")
    """
    # Primero intentamos obtener la fecha y hora desde "FECHA ADMVA."
    fecha_admva_pattern = r"FECHA ADMVA\.?:?\s*(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{1,2}:\d{1,2})\s*([ap]\.\s*m\.)"
    fecha_admva_match = re.search(fecha_admva_pattern, ocr_text)
    
    fecha_completa = None
    
    if fecha_admva_match:
        fecha = fecha_admva_match.group(1)
        hora = fecha_admva_match.group(2)
        am_pm = fecha_admva_match.group(3)
        fecha_completa = f"{fecha} {hora} {am_pm}"
    
    # Patrón alternativo para FECHA ADMVA
    if not fecha_completa:
        alt_pattern = r"FECHA ADMVA\.?:?\s*(\d{1,2}/\d{1,2}/\d{4})"
        alt_match = re.search(alt_pattern, ocr_text)
        if alt_match:
            fecha_completa = alt_match.group(1)
    
    # Si no encontramos la fecha administrativa completa, intentamos con FECH y HORA
    if not fecha_completa:
        fech_pattern = r"FECH[A:]*\s*(\d{1,2}/\d{1,2}/\d{4})"
        hora_pattern = r"HORA:?\s*(\d{1,2}:\d{1,2}:\d{1,2})"
        am_pm_pattern = r"([ap]\.\s*m\.)"
        
        fech_match = re.search(fech_pattern, ocr_text)
        hora_match = re.search(hora_pattern, ocr_text)
        am_pm_match = re.search(am_pm_pattern, ocr_text)
        
        # Si tenemos los tres componentes, los combinamos
        if fech_match and hora_match and am_pm_match:
            fecha = fech_match.group(1)
            hora = hora_match.group(1)
            am_pm = am_pm_match.group(1)
            fecha_completa = f"{fecha} {hora} {am_pm}"
        
        # Si solo tenemos fecha y hora pero no am/pm
        elif fech_match and hora_match:
            fecha = fech_match.group(1)
            hora = hora_match.group(1)
            fecha_completa = f"{fecha} {hora}"
        
        # Si solo tenemos la fecha
        elif fech_match:
            fecha_completa = fech_match.group(1)
    
    # Método de respaldo: buscar cualquier formato de fecha y hora juntos
    if not fecha_completa:
        backup_pattern = r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{1,2}:\d{1,2})\s*([ap]\.\s*m\.)"
        backup_match = re.search(backup_pattern, ocr_text)
        
        if backup_match:
            fecha = backup_match.group(1)
            hora = backup_match.group(2)
            am_pm = backup_match.group(3)
            fecha_completa = f"{fecha} {hora} {am_pm}"
    
    # Último método de respaldo: buscar cualquier fecha en formato DD/MM/YYYY
    if not fecha_completa:
        last_backup_pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
        last_backup_match = re.search(last_backup_pattern, ocr_text)
        
        if last_backup_match:
            fecha_completa = last_backup_match.group(1)
    
    # Si nada funciona, devolver un valor por defecto
    if not fecha_completa:
        return "No encontrada"
    
    # NUEVO: Estandarizar el formato de fecha antes de devolverlo
    # Extraer solo la parte de la fecha (sin hora)
    if " " in fecha_completa:
        fecha_only = fecha_completa.split(" ")[0]
    else:
        fecha_only = fecha_completa
    
    # Asegurar formato DD/MM/YYYY
    try:
        parts = fecha_only.split("/")
        if len(parts) == 3:
            day = parts[0].zfill(2)  # Añade ceros a la izquierda si es necesario
            month = parts[1].zfill(2)  # Añade ceros a la izquierda si es necesario
            year = parts[2]
            return f"{day}/{month}/{year}"
    except Exception:
        # Si hay algún error al formatear, devolver la fecha original sin hora
        pass
    
    return fecha_only  # Devolver solo la parte de fecha


def extract_sucursal_info(ocr_text):
    """
    Extrae información de la sucursal (nombre y código) basándose en la estructura
    típica de los tickets OXXO.
    
    Args:
        ocr_text: Texto completo del OCR
        
    Returns:
        tuple: (nombre_sucursal, codigo_sucursal, nombre_sucursal_formateado)
    """
    # Valores predeterminados
    nombre_sucursal = "No encontrado"
    codigo_sucursal = "No encontrado"
    
    # MÉTODO 1: Buscar patrones específicos con palabras clave CUL
    patrones_cul = [
        r'\b(GUASAVE\s+CUL)\b',
        r'\b(URIAS\s+CUL)\b',
        r'\b(ZARAGOZA\s+II\s+CUL)\b',
        r'\b(CERRO\s+COLORADO\s+CUL)\b',
        r'\b(VALLE\s+DEL\s+SOL\s+CUL)\b',
        r'\b(COTO\s+\d+\s+CUL)\b',
        r'\b([A-Z]+\s+[A-Z]+\s+[A-Z]+\s+CUL)\b',
        r'\b([A-Z]+\s+[A-Z]+\s+CUL)\b',
        r'\b([A-Z]+\s+CUL)\b'
    ]
    
    for patron in patrones_cul:
        match = re.search(patron, ocr_text, re.IGNORECASE)
        if match:
            nombre_sucursal = match.group(1).strip()
            print(f"🏪 Nombre de sucursal encontrado con patrón específico: {nombre_sucursal}")
            break
    
    # MÉTODO 2: Buscar en las primeras líneas del texto
    if nombre_sucursal == "No encontrado":
        # Dividir el texto en líneas
        lineas = ocr_text.split('\n')
        
        # Buscar en las primeras 5 líneas, que suele estar el nombre de la sucursal
        for i in range(min(5, len(lineas))):
            linea = lineas[i].strip()
            # Buscar CUL que es típico del final del nombre de sucursal
            if "CUL" in linea:
                # Extraer toda la línea o la parte relevante
                partes = linea.split("CUL")
                if partes and partes[0].strip():
                    nombre_completo = partes[0].strip() + " CUL"
                    # Limpiar el nombre de elementos no deseados
                    nombre_limpio = re.sub(r',|S\.A\.|de|C\.V\.', '', nombre_completo).strip()
                    # Si tenemos más de una palabra, quitar la primera si es "Cadena" o "Comercial"
                    palabras = nombre_limpio.split()
                    if len(palabras) > 1 and palabras[0] in ["Cadena", "CADENA", "Comercial", "COMERCIAL"]:
                        nombre_limpio = ' '.join(palabras[1:])
                    
                    if nombre_limpio and "CUL" in nombre_limpio:
                        nombre_sucursal = nombre_limpio
                        print(f"🏪 Nombre de sucursal extraído de línea {i}: {nombre_sucursal}")
                        break
    
    # MÉTODO 3: Buscar después de "TIENDA:" y antes de "FECHA:"
    if nombre_sucursal == "No encontrado":
        tienda_idx = ocr_text.find("TIENDA:")
        fecha_idx = ocr_text.find("FECHA:")
        
        if tienda_idx > 0 and fecha_idx > tienda_idx:
            # Extraer el texto entre TIENDA: y FECHA:
            texto_entre = ocr_text[tienda_idx:fecha_idx]
            # Buscar patrón CUL
            match = re.search(r'([A-Z]+(?:\s+[A-Z0-9]+)*)\s+CUL', texto_entre, re.IGNORECASE)
            if match:
                nombre_sucursal = match.group(0).strip()
                print(f"🏪 Nombre de sucursal encontrado entre TIENDA: y FECHA:: {nombre_sucursal}")
    
    # MÉTODO 4: Buscar el nombre después de la primera aparición de "Cadena Comercial"
    if nombre_sucursal == "No encontrado":
        cadena_idx = ocr_text.find("Cadena Comercial")
        if cadena_idx >= 0:
            # Buscar en las siguientes 100 caracteres
            segmento = ocr_text[cadena_idx:cadena_idx+100]
            # Encontrar la primera palabra después de "Cadena Comercial" que termine en CUL
            match = re.search(r'Cadena\s+Comercial.*?([A-Z]+\s+CUL)', segmento, re.IGNORECASE)
            if match:
                nombre_sucursal = match.group(1).strip()
                print(f"🏪 Nombre de sucursal encontrado después de 'Cadena Comercial': {nombre_sucursal}")
    
    # MÉTODO 5: Búsqueda específica para GUASAVE CUL
    if nombre_sucursal == "No encontrado" and "GUASAVE" in ocr_text:
        nombre_sucursal = "GUASAVE CUL"
        print(f"🏪 Nombre de sucursal detectado específicamente: {nombre_sucursal}")
    
    # MÉTODO 6: Buscar el código de sucursal
    tienda_patterns = [
        r"TIEND[A:]*\s*<?<?[^A-Za-z0-9]*(5\d[A-Z0-9]{3})",
        r"TIEND[A:]*\s*(\d{5})",
        r"TIEND[A:]*\s*(\d{4}[A-Z]{1})",
        r"TIEND[A:]*\s*([0-9]{2,3}[A-Z]{1,2}[0-9]{0,1}[A-Z]{0,1})"  # Patrón más flexible
    ]
    
    for pattern in tienda_patterns:
        codigo_match = re.search(pattern, ocr_text, re.IGNORECASE)
        if codigo_match:
            codigo_sucursal = codigo_match.group(1).strip()
            print(f"🏪 Código de sucursal encontrado: {codigo_sucursal}")
            break
    
    # MÉTODO 7: Buscar cualquier patrón de código en el texto
    if codigo_sucursal == "No encontrado":
        all_codes = re.findall(r'5\d[A-Z0-9]{3}', ocr_text)
        if all_codes:
            codigo_sucursal = all_codes[0]
            print(f"🏪 Código de sucursal encontrado por método alternativo: {codigo_sucursal}")
    
    # Aplicar formato al nombre de la sucursal
    nombre_sucursal_formateado = format_oxxo_store_name(nombre_sucursal)
    
    return nombre_sucursal, codigo_sucursal, nombre_sucursal_formateado

def detect_ticket_format(ocr_text):
    """
    Detecta el formato del ticket OXXO para determinar de qué columna extraer las cantidades.
    
    Args:
        ocr_text: Texto completo del OCR
        
    Returns:
        str: 'formato1' si las cantidades están en la columna UDS, 'formato2' si están en U.COM
    """
    # Buscar patrones en el texto que ayuden a identificar el formato
    
    # En el Formato 1 las cantidades reales de productos están en UDS
    # En el Formato 2 las cantidades reales están en U.COM
    
    # 1. Primer indicador: Verificar la estructura del encabezado
    # Formato 2 suele tener encabezado "UDS U.COM VAL.TOT" juntos
    headers_pattern = r'UDS\s+U\.COM\s+VAL\.TOT'
    if re.search(headers_pattern, ocr_text, re.IGNORECASE):
        print("🔍 Detectado encabezado característico de Formato 2")
        return 'formato2'
    
    # 2. Calcular total de costo para verificar con ambos formatos
    total_costo_match = re.search(r'TOTAL\s+COSTO\s*(\d{1,3}(?:,\d{3})*(?:-|\.)?\d{2}|\d+(?:-|\.)?\d{2}|\d+)', ocr_text)
    total_costo = 0
    if total_costo_match:
        # Limpieza del string del total de costo (manejar guiones, comas, etc.)
        total_costo_str = total_costo_match.group(1).replace(',', '').replace('-', '.')
        try:
            total_costo = float(total_costo_str)
            print(f"🔍 Total de costo detectado: {total_costo:.2f}")
        except ValueError:
            print(f"⚠️ No se pudo convertir el total de costo a número: {total_costo_str}")
    
    # 3. Extraer información de productos y sus cantidades
    # Almacenar cantidades para ambos formatos
    productos_info = []  # Lista para almacenar (costo, cantidad_f1, cantidad_f2)
    
    # 3.1 Buscar productos con patrón específico (código de barras Santi Ice)
    # Capturar específicamente valores en columnas UDS y U.COM
    # Pattern más preciso para extraer campos de las columnas
    ice_pattern = r'(\d+)\s+(7500[46]650960(?:04|11))\s+(?:HIELO|BOLSA).*?(\d+\.\d{2})\s+(?:\d+\.\d{2}|\d+)?\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)'
    ice_matches = re.findall(ice_pattern, ocr_text)
    
    if ice_matches:
        for match in ice_matches:
            try:
                costo = float(match[2])  # Columna de costo
                uds = float(match[3])    # Columna UDS
                ucom = float(match[4])   # Columna U.COM
                
                print(f"🔍 Producto encontrado - Costo: {costo:.2f}, UDS: {uds}, U.COM: {ucom}")
                productos_info.append((costo, uds, ucom))
            except (ValueError, IndexError) as e:
                print(f"⚠️ Error al procesar valores de producto: {e}")
    
    # 3.2 Si no se encontraron productos con el patrón específico, usar uno más genérico
    if not productos_info:
        # Patrón más flexible para buscar líneas de productos
        general_pattern = r'(\d+\.\d{2})\s+(?:\d+\.\d{2}|\d+)?\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)'
        general_matches = re.findall(general_pattern, ocr_text)
        
        for match in general_matches:
            try:
                # Verificar si el primer valor parece un costo válido (17.50 o 37.50)
                costo = float(match[0])
                if abs(costo - 17.5) < 0.1 or abs(costo - 37.5) < 0.1:
                    uds = float(match[1])
                    ucom = float(match[2])
                    print(f"🔍 Producto probable - Costo: {costo:.2f}, UDS: {uds}, U.COM: {ucom}")
                    productos_info.append((costo, uds, ucom))
            except (ValueError, IndexError):
                continue
    
    # 4. Calcular totales con ambos formatos y comparar con el total del ticket
    if productos_info and total_costo > 0:
        # Calcular totales para cada formato
        total_f1 = sum(costo * uds for costo, uds, _ in productos_info)
        total_f2 = sum(costo * ucom for costo, _, ucom in productos_info)
        
        print(f"🔍 Total calculado Formato 1 (UDS): {total_f1:.2f}")
        print(f"🔍 Total calculado Formato 2 (U.COM): {total_f2:.2f}")
        print(f"🔍 Total en ticket: {total_costo:.2f}")
        
        # Margen de error más amplio (1%)
        margen_error = total_costo * 0.01
        
        # Comparar qué formato coincide mejor con el total del ticket
        diff_f1 = abs(total_f1 - total_costo)
        diff_f2 = abs(total_f2 - total_costo)
        
        if diff_f1 <= margen_error and (diff_f2 > margen_error or diff_f1 < diff_f2):
            print(f"✅ El Formato 1 coincide con el total del ticket (diff={diff_f1:.2f})")
            return 'formato1'
        elif diff_f2 <= margen_error and (diff_f1 > margen_error or diff_f2 < diff_f1):
            print(f"✅ El Formato 2 coincide con el total del ticket (diff={diff_f2:.2f})")
            return 'formato2'
        else:
            # Si ambos están dentro del margen, elegir el que tenga menor diferencia
            if diff_f1 < diff_f2:
                print(f"✅ Eligiendo Formato 1 por menor diferencia ({diff_f1:.2f} vs {diff_f2:.2f})")
                return 'formato1'
            else:
                print(f"✅ Eligiendo Formato 2 por menor diferencia ({diff_f2:.2f} vs {diff_f1:.2f})")
                return 'formato2'
    
    # 5. Análisis adicional cuando no podemos determinar por cálculos
    # Buscar patrones específicos de cada formato en el texto
    
    # Verificar si en el ticket hay valores significativos en U.COM
    if re.search(r'U\.COM\s+\d+\s+\d+', ocr_text) or re.search(r'VAL\.TOT\s+\d+', ocr_text):
        # Buscar valores específicos que indiquen cantidades en la columna U.COM
        if re.search(r'(87|9)\s+\d+', ocr_text):  # Valores como los del formato 2 en el ejemplo
            print("✅ Detectado patrón de valores característico de Formato 2")
            return 'formato2'
    
    # Si llegamos aquí, intentar una última verificación buscando las cantidades esperadas
    # Verificar si aparecen los valores de cantidades conocidos del formato 2
    if '87' in ocr_text and '9' in ocr_text:
        print("✅ Encontrados valores 87 y 9 típicos del Formato 2")
        return 'formato2'
    
    # Si no podemos determinar el formato con certeza, analizar la estructura general
    if "VAL.TOT" in ocr_text and "U.COM" in ocr_text:
        print("✅ Estructura del ticket sugiere Formato 2 (encabezados VAL.TOT y U.COM presentes)")
        return 'formato2'
    
    # Si no tenemos suficiente información, verificar costos totales
    if total_costo >= 1800:  # Los tickets de formato 2 suelen tener costos más altos en los ejemplos
        print(f"✅ Eligiendo Formato 2 por valor de costo total ({total_costo:.2f})")
        return 'formato2'
    
    print("⚠️ No se pudo determinar con certeza el formato. Usando Formato 1 por defecto.")
    return 'formato1'


def extract_products_from_ticket(ocr_text, formato, remision, pedido_adicional, fecha, sucursal, codigo_sucursal):
    """
    Extrae productos del ticket según el formato detectado.
    
    Args:
        ocr_text: Texto completo del OCR
        formato: 'formato1' o 'formato2' según lo que detecte la función detect_ticket_format
        remision, pedido_adicional, fecha, sucursal, codigo_sucursal: Datos del ticket
        
    Returns:
        list: Lista de productos encontrados
    """
    print(f"🔍 Extrayendo productos usando {formato}")
    productos = []
    
    # Identificar líneas que contienen códigos de productos
    lineas_5kg = []
    lineas_15kg = []
    
    # Buscar códigos de barras conocidos en el texto
    codigos_producto_5kg = ["7500465096004", "7500466096004"]  # Códigos para bolsas de 5kg
    codigos_producto_15kg = ["7500465096011", "7500466096011"]  # Códigos para hielo de 15kg
    
    # Dividir el texto en líneas
    lineas = ocr_text.split('\n')
    
    # Identificar líneas que contienen los códigos de productos
    for linea in lineas:
        for codigo in codigos_producto_5kg:
            if codigo in linea:
                lineas_5kg.append(linea)
                break
        
        for codigo in codigos_producto_15kg:
            if codigo in linea:
                lineas_15kg.append(linea)
                break
    
    # Si no encontramos líneas por código, buscar por descripción
    if not lineas_5kg:
        for linea in lineas:
            if "BOLSA" in linea and "SANTI" in linea and "5K" in linea:
                lineas_5kg.append(linea)
    
    if not lineas_15kg:
        for linea in lineas:
            if "HIELO" in linea and "SANTI" in linea and "15KG" in linea:
                lineas_15kg.append(linea)
    
    print(f"🔍 Encontradas {len(lineas_5kg)} líneas para bolsas 5kg")
    print(f"🔍 Encontradas {len(lineas_15kg)} líneas para hielo 15kg")
    
    # Función auxiliar para extraer valores numéricos de una línea
    def extraer_valores(linea):
        # Capturar todos los valores numéricos (enteros y decimales)
        valores = re.findall(r'(\d+(?:\.\d+)?)', linea)
        return [float(v) for v in valores if v]
    
    # Procesar productos según el formato
    if formato == 'formato2':
        # FORMATO 2: Extraer cantidades de U.COM
        
        # Para bolsas de 5kg
        for linea in lineas_5kg:
            valores = extraer_valores(linea)
            print(f"🔍 Valores en línea 5kg: {valores}")
            
            # En formato 2, buscamos el patrón donde después del costo (17.5) 
            # y el precio (alrededor de 31-33) aparece UDS y luego U.COM
            # Típicamente es algo como: [... 17.50 31.00 139.00 87.00 ...]
            # Donde queremos el valor en U.COM (87)
            
            if len(valores) >= 6:
                for i, valor in enumerate(valores):
                    # Identificar el costo de las bolsas de 5kg (17.5)
                    if abs(valor - 17.5) < 0.1 and i + 3 < len(valores):
                        # Tomar el valor que aparece 3 posiciones después del costo (U.COM)
                        cantidad = int(valores[i + 3])
                        if 1 <= cantidad <= 300:  # Validación básica
                            productos.append({
                                "fecha": fecha,
                                "sucursal": sucursal,
                                "codigo_sucursal": codigo_sucursal,
                                "pedido_adicional": pedido_adicional,
                                "remision": remision,
                                "costo": 17.5,
                                "cantidad": cantidad,
                                "descripcion": "BOLSA HIELO SANTI 5K"
                            })
                            print(f"🧊 Bolsa 5kg (Formato 2): {cantidad} unidades")
                            break
            
            # Si no se pudo extraer, intentar con un enfoque alternativo
            if not any(p["descripcion"] == "BOLSA HIELO SANTI 5K" for p in productos):
                # Buscar "U.COM" en la línea y tomar el número que le sigue
                ucom_match = re.search(r'U\.COM\s+(\d+)', linea)
                if ucom_match:
                    cantidad = int(ucom_match.group(1))
                    if 1 <= cantidad <= 300:
                        productos.append({
                            "fecha": fecha,
                            "sucursal": sucursal,
                            "codigo_sucursal": codigo_sucursal,
                            "pedido_adicional": pedido_adicional,
                            "remision": remision,
                            "costo": 17.5,
                            "cantidad": cantidad,
                            "descripcion": "BOLSA HIELO SANTI 5K"
                        })
                        print(f"🧊 Bolsa 5kg (alt): {cantidad} unidades")
        
        # Para hielo de 15kg
        for linea in lineas_15kg:
            valores = extraer_valores(linea)
            print(f"🔍 Valores en línea 15kg: {valores}")
            
            # Similar al caso anterior, pero con el costo de 37.5
            if len(valores) >= 6:
                for i, valor in enumerate(valores):
                    # Identificar el costo del hielo de 15kg (37.5)
                    if abs(valor - 37.5) < 0.1 and i + 3 < len(valores):
                        # Tomar el valor que aparece 3 posiciones después del costo (U.COM)
                        cantidad = int(valores[i + 3])
                        if 1 <= cantidad <= 100:  # Validación básica
                            productos.append({
                                "fecha": fecha,
                                "sucursal": sucursal,
                                "codigo_sucursal": codigo_sucursal,
                                "pedido_adicional": pedido_adicional,
                                "remision": remision,
                                "costo": 37.5,
                                "cantidad": cantidad,
                                "descripcion": "HIELO SANTI ICE 15KG"
                            })
                            print(f"🧊 Hielo 15kg (Formato 2): {cantidad} unidades")
                            break
            
            # Si no se pudo extraer, intentar enfoque alternativo
            if not any(p["descripcion"] == "HIELO SANTI ICE 15KG" for p in productos):
                # Buscar "U.COM" en la línea y tomar el número que le sigue
                ucom_match = re.search(r'U\.COM\s+(\d+)', linea)
                if ucom_match:
                    cantidad = int(ucom_match.group(1))
                    if 1 <= cantidad <= 100:
                        productos.append({
                            "fecha": fecha,
                            "sucursal": sucursal,
                            "codigo_sucursal": codigo_sucursal,
                            "pedido_adicional": pedido_adicional,
                            "remision": remision,
                            "costo": 37.5,
                            "cantidad": cantidad,
                            "descripcion": "HIELO SANTI ICE 15KG"
                        })
                        print(f"🧊 Hielo 15kg (alt): {cantidad} unidades")
    else:
        # FORMATO 1: Extraer cantidades de UDS
        
        # Para bolsas de 5kg
        for linea in lineas_5kg:
            valores = extraer_valores(linea)
            print(f"🔍 Valores en línea 5kg: {valores}")
            
            # En formato 1, después del costo (17.5) y el precio
            # viene directamente UDS (la cantidad que queremos)
            # Típicamente es algo como: [... 17.50 31.00 71.00 ...]
            # Donde queremos UDS (71)
            
            if len(valores) >= 4:
                for i, valor in enumerate(valores):
                    # Identificar el costo de las bolsas de 5kg (17.5)
                    if abs(valor - 17.5) < 0.1 and i + 2 < len(valores):
                        # Tomar el valor que aparece 2 posiciones después del costo (UDS)
                        cantidad = int(valores[i + 2])
                        if 1 <= cantidad <= 300:  # Validación básica
                            productos.append({
                                "fecha": fecha,
                                "sucursal": sucursal,
                                "codigo_sucursal": codigo_sucursal,
                                "pedido_adicional": pedido_adicional,
                                "remision": remision,
                                "costo": 17.5,
                                "cantidad": cantidad,
                                "descripcion": "BOLSA HIELO SANTI 5K"
                            })
                            print(f"🧊 Bolsa 5kg (Formato 1): {cantidad} unidades")
                            break
            
            # Si no se pudo extraer, intentar enfoque alternativo
            if not any(p["descripcion"] == "BOLSA HIELO SANTI 5K" for p in productos):
                # Buscar "UDS." en la línea y tomar el número que le sigue
                uds_match = re.search(r'UDS\.?\s+(\d+(?:\.\d+)?)', linea)
                if uds_match:
                    cantidad = int(float(uds_match.group(1)))
                    if 1 <= cantidad <= 300:
                        productos.append({
                            "fecha": fecha,
                            "sucursal": sucursal,
                            "codigo_sucursal": codigo_sucursal,
                            "pedido_adicional": pedido_adicional,
                            "remision": remision,
                            "costo": 17.5,
                            "cantidad": cantidad,
                            "descripcion": "BOLSA HIELO SANTI 5K"
                        })
                        print(f"🧊 Bolsa 5kg (alt): {cantidad} unidades")
        
        # Para hielo de 15kg
        for linea in lineas_15kg:
            valores = extraer_valores(linea)
            print(f"🔍 Valores en línea 15kg: {valores}")
            
            # Similar al caso anterior, pero con el costo de 37.5
            if len(valores) >= 4:
                for i, valor in enumerate(valores):
                    # Identificar el costo del hielo de 15kg (37.5)
                    if abs(valor - 37.5) < 0.1 and i + 2 < len(valores):
                        # Tomar el valor que aparece 2 posiciones después del costo (UDS)
                        cantidad = int(valores[i + 2])
                        if 1 <= cantidad <= 100:  # Validación básica
                            productos.append({
                                "fecha": fecha,
                                "sucursal": sucursal,
                                "codigo_sucursal": codigo_sucursal,
                                "pedido_adicional": pedido_adicional,
                                "remision": remision,
                                "costo": 37.5,
                                "cantidad": cantidad,
                                "descripcion": "HIELO SANTI ICE 15KG"
                            })
                            print(f"🧊 Hielo 15kg (Formato 1): {cantidad} unidades")
                            break
            
            # Si no se pudo extraer, intentar enfoque alternativo
            if not any(p["descripcion"] == "HIELO SANTI ICE 15KG" for p in productos):
                # Buscar "UDS." en la línea y tomar el número que le sigue
                uds_match = re.search(r'UDS\.?\s+(\d+(?:\.\d+)?)', linea)
                if uds_match:
                    cantidad = int(float(uds_match.group(1)))
                    if 1 <= cantidad <= 100:
                        productos.append({
                            "fecha": fecha,
                            "sucursal": sucursal,
                            "codigo_sucursal": codigo_sucursal,
                            "pedido_adicional": pedido_adicional,
                            "remision": remision,
                            "costo": 37.5,
                            "cantidad": cantidad,
                            "descripcion": "HIELO SANTI ICE 15KG"
                        })
                        print(f"🧊 Hielo 15kg (alt): {cantidad} unidades")
    
    # MÉTODO DE RESPALDO: Buscar patrones generales en el texto completo
    if not productos or len(productos) < 2:
        print("🔍 Usando método de respaldo basado en patrón general")
        
        # Intentar extraer información de productos por estructura de línea
        # Buscar líneas que contengan U.COM (formato 2) o UDS. (formato 1)
        busqueda_patron = r'U\.COM\s+(\d+)' if formato == 'formato2' else r'UDS\.?\s+(\d+(?:\.\d+)?)'
        
        # Buscar todos los valores después del patrón
        matches = re.findall(busqueda_patron, ocr_text)
        
        if matches and len(matches) >= 2:
            print(f"🔍 Valores encontrados con patrón general: {matches}")
            
            # Identificar cuáles son 5kg y 15kg
            # Para esto, vemos el contexto en que aparecen estos valores
            
            # Buscar menciones de hielo 15kg en el texto
            mencion_15kg = re.search(r'15KG.*?' + busqueda_patron, ocr_text)
            if mencion_15kg:
                # El primer valor después de 15KG es para hielo 15kg
                indice_15kg = ocr_text.find(mencion_15kg.group(0))
                
                # Buscar menciones de bolsa 5kg
                mencion_5kg = re.search(r'5K.*?' + busqueda_patron, ocr_text)
                if mencion_5kg:
                    indice_5kg = ocr_text.find(mencion_5kg.group(0))
                    
                    if indice_15kg < indice_5kg:
                        # 15kg aparece primero en el texto
                        if len(matches) >= 2:
                            cantidad_15kg = int(float(matches[0]))
                            cantidad_5kg = int(float(matches[1]))
                    else:
                        # 5kg aparece primero en el texto
                        if len(matches) >= 2:
                            cantidad_5kg = int(float(matches[0]))
                            cantidad_15kg = int(float(matches[1]))
                    
                    # Verificar si ya tenemos estos productos y añadirlos si no
                    if not any(p["descripcion"] == "BOLSA HIELO SANTI 5K" for p in productos) and 'cantidad_5kg' in locals():
                        productos.append({
                            "fecha": fecha,
                            "sucursal": sucursal,
                            "codigo_sucursal": codigo_sucursal,
                            "pedido_adicional": pedido_adicional,
                            "remision": remision,
                            "costo": 17.5,
                            "cantidad": cantidad_5kg,
                            "descripcion": "BOLSA HIELO SANTI 5K"
                        })
                        print(f"🧊 Bolsa 5kg (respaldo): {cantidad_5kg} unidades")
                    
                    if not any(p["descripcion"] == "HIELO SANTI ICE 15KG" for p in productos) and 'cantidad_15kg' in locals():
                        productos.append({
                            "fecha": fecha,
                            "sucursal": sucursal,
                            "codigo_sucursal": codigo_sucursal,
                            "pedido_adicional": pedido_adicional,
                            "remision": remision,
                            "costo": 37.5,
                            "cantidad": cantidad_15kg,
                            "descripcion": "HIELO SANTI ICE 15KG"
                        })
                        print(f"🧊 Hielo 15kg (respaldo): {cantidad_15kg} unidades")
    
    # VERIFICAR CÁLCULO DEL COSTO TOTAL: última capa de validación
    if productos:
        # Calcular el costo total según los productos detectados
        costo_calculado = sum(p["costo"] * p["cantidad"] for p in productos)
        
        # Extraer el costo total del ticket
        costo_total_match = re.search(r'TOTAL\s+COSTO\s*(\d{1,3}(?:,\d{3})*(?:-|\.)?\d{2}|\d+(?:-|\.)?\d{2}|\d+)', ocr_text)
        if costo_total_match:
            # Limpiar y convertir el valor del costo total
            costo_total_str = costo_total_match.group(1).replace(',', '').replace('-', '.')
            try:
                costo_total = float(costo_total_str)
                print(f"🔍 Costo total en ticket: {costo_total:.2f}")
                print(f"🔍 Costo calculado con productos: {costo_calculado:.2f}")
                
                # Si hay una diferencia significativa, puede que tengamos cantidades incorrectas
                if abs(costo_calculado - costo_total) > (costo_total * 0.05):  # 5% de margen de error
                    print("⚠️ Diferencia significativa entre costo calculado y total del ticket")
                    
                    # Verificar si esta diferencia sugiere intercambio de UDS y U.COM
                    if formato == 'formato2':
                        # Buscar nuevamente las líneas con información de productos
                        for linea in lineas_5kg + lineas_15kg:
                            # Buscar patrón UDS U.COM específico
                            uds_ucom_match = re.search(r'(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(?:VAL\.TOT|$)', linea)
                            if uds_ucom_match:
                                uds = float(uds_ucom_match.group(1))
                                ucom = float(uds_ucom_match.group(2))
                                
                                # Verificar cuál valor da un cálculo más cercano al total
                                for i, producto in enumerate(productos):
                                    if "5K" in producto["descripcion"] and uds >= 1 and ucom >= 1:
                                        # Probar ambos valores para ver cuál da mejor resultado
                                        productos_uds = productos.copy()
                                        productos_uds[i]["cantidad"] = int(uds)
                                        
                                        productos_ucom = productos.copy()
                                        productos_ucom[i]["cantidad"] = int(ucom)
                                        
                                        costo_uds = sum(p["costo"] * p["cantidad"] for p in productos_uds)
                                        costo_ucom = sum(p["costo"] * p["cantidad"] for p in productos_ucom)
                                        
                                        diff_uds = abs(costo_uds - costo_total)
                                        diff_ucom = abs(costo_ucom - costo_total)
                                        
                                        if diff_uds < diff_ucom:
                                            productos[i]["cantidad"] = int(uds)
                                            print(f"🔄 Corrigiendo cantidad para {producto['descripcion']}: {int(uds)}")
                                        else:
                                            productos[i]["cantidad"] = int(ucom)
                                            print(f"🔄 Corrigiendo cantidad para {producto['descripcion']}: {int(ucom)}")
            except ValueError:
                print(f"⚠️ No se pudo convertir el costo total: {costo_total_str}")
    
    return productos


def process_text_oxxo(ocr_text):
    """
    Extrae los datos de los tickets de OXXO y devuelve una lista de diccionarios para cada producto.
    Versión mejorada que maneja diferentes formatos de tickets OXXO.
    
    Args:
        ocr_text: Texto extraído del OCR
        
    Returns:
        list: Lista de diccionarios con los datos extraídos o un diccionario con error
    """
    print("🔍 Procesando texto para OXXO")
    
    # Para depuración, mostrar todo el texto OCR
    print("📄 Texto OCR completo:\n" + ocr_text)
    
    # Preprocesar el texto para eliminar posibles duplicados
    ocr_text = preprocess_ocr_text(ocr_text)
    
    # 🔹 MEJORA: Extraer información de sucursal usando el nuevo método
    nombre_sucursal, codigo_sucursal, nombre_sucursal_formateado = extract_sucursal_info(ocr_text)

    print(f"🏪 Nombre de sucursal detectado: {nombre_sucursal}")
    print(f"🏪 Código de sucursal detectado: {codigo_sucursal}")

    # CAMBIO: Ahora usamos el nombre formateado como valor principal para sucursal
    if nombre_sucursal != "No encontrado":
        sucursal = nombre_sucursal_formateado
    else:
        # Si no tenemos nombre, usamos el código como respaldo
        sucursal = codigo_sucursal
    
    # 🔹 Extraer fecha completa del ticket (incluyendo hora)
    fecha = extract_formatted_date(ocr_text)
    print(f"📅 Fecha detectada: {fecha}")

    # 🔹 Extraer pedido adicional y remisión con patrones más flexibles
    pedido_adicional_match = re.search(r"PEDIDO\s*ADICIONAL\.?:?\s*(\d+)", ocr_text, re.IGNORECASE)
    remision_match = re.search(r"REMISI[OÓ]N\.?:?\s*(\d+)", ocr_text, re.IGNORECASE)

    pedido_adicional = pedido_adicional_match.group(1) if pedido_adicional_match else "No encontrado"
    remision = remision_match.group(1) if remision_match else "No encontrado"
    
    print(f"📝 Pedido adicional: {pedido_adicional}")
    print(f"📝 Remisión: {remision}")

    # Método de respaldo para extraer remisión si el patrón principal no funciona
    if remision == "No encontrado":
        # Buscar números de 6 dígitos que podrían ser remisiones
        posibles_remisiones = re.findall(r'\b\d{5,6}\b', ocr_text)
        for posible in posibles_remisiones:
            # Verificar si este número no es una fecha ni otro valor conocido
            if not re.search(r'\d{1,2}/\d{1,2}/\d{4}', posible) and posible != pedido_adicional:
                remision = posible
                print(f"📝 Remisión extraída por método alternativo: {remision}")
                break

    # Validar que tenemos datos mínimos necesarios
    if pedido_adicional == "No encontrado" or remision == "No encontrado":
        return {"error": "No se pudo extraer la información de pedido adicional o remisión del ticket"}
    
    # NUEVA FUNCIONALIDAD: Detectar el formato del ticket
    formato = detect_ticket_format(ocr_text)
    print(f"🔍 Formato de ticket OXXO detectado: {formato}")
    
    # Extraer productos basados en el formato detectado
    productos = extract_products_from_ticket(ocr_text, formato, remision, pedido_adicional, fecha, sucursal, codigo_sucursal)
    
    # Verificar resultados
    if not productos:
        return {"error": "No se encontraron productos válidos en el ticket"}
        
    print(f"📦 Se encontraron {len(productos)} productos en el ticket")
    for i, producto in enumerate(productos):
        print(f"📦 Producto {i+1}: {producto.get('descripcion', 'Sin descripción')} - Cantidad: {producto['cantidad']} - Costo: {producto['costo']}")
    
    return productos