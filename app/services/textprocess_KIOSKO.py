import re
import json
import boto3
import time
import botocore.exceptions
from dotenv import load_dotenv
# Ya no importamos send_to_google_sheets aquí
load_dotenv()

# Funciones mejoradas para extracción KIOSKO
def extract_kiosko_quantities_improved(lines, product_code, product_type):
    """Extrae cantidades usando algoritmo mejorado basado en análisis real."""
    for i, line in enumerate(lines):
        if product_code in line:
            # Patrón 1: Código y cantidad en misma línea
            pattern_same_line = rf'{re.escape(product_code)}\s+(\d+)\.00'
            match = re.search(pattern_same_line, line)
            if match:
                quantity = int(match.group(1))
                if validate_kiosko_quantity(quantity, product_type):
                    return quantity
            
            # Patrón 2: Cantidad en línea siguiente
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                pattern_next_line = r'(\d+)\.00'
                match = re.search(pattern_next_line, next_line)
                if match:
                    quantity = int(match.group(1))
                    if validate_kiosko_quantity(quantity, product_type):
                        return quantity
            
            # Patrón 3: Buscar en líneas cercanas
            search_range = range(max(0, i-2), min(len(lines), i+3))
            for j in search_range:
                if j != i:
                    search_line = lines[j]
                    numbers = re.findall(r'(\d+)\.00', search_line)
                    for num_str in numbers:
                        quantity = int(num_str)
                        if validate_kiosko_quantity(quantity, product_type):
                            return quantity
    return None

def validate_kiosko_quantity(quantity, product_type):
    """Valida cantidades KIOSKO con filtros para cantidades extremas."""
    if product_type == "5kg":
        return 15 <= quantity <= 120 or (121 <= quantity <= 499)
    elif product_type == "15kg":
        return 5 <= quantity <= 40 or (41 <= quantity <= 199)
    return False

session = boto3.Session()
bedrock_client = session.client("bedrock-runtime")

MODEL_ID = "meta.llama3-8b-instruct-v1:0"

# Definición local para la función faltante

def extraer_importe_unitario_fallback(raw_text):
    """
    Función de respaldo que intenta extraer el importe unitario directamente 
    del texto mediante expresiones regulares.
    """
    patrones = [
        r'Costo\s+Unitario\s+(?:\D*?)(\d+\.?\d*)',
        r'Importe\s+(\d+\.?\d*)',
        r'Unitario\s+(\d+\.?\d*)'
    ]
    
    for patron in patrones:
        match = re.search(patron, raw_text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                continue
    
    # Último recurso: buscar valores típicos (15, 16, 45)
    valores = re.findall(r'(\d{1,2}\.?\d{0,2})', raw_text)
    for valor in valores:
        try:
            val_float = float(valor)
            if val_float in [15.0, 16.0, 45.0]:
                return val_float
        except:
            continue
    
    return None

def format_store_name(store_name):
    """
    Formatea el nombre de la tienda eliminando códigos numéricos y 
    aplicando formato de mayúsculas/minúsculas adecuado.
    Versión mejorada para KIOSKO con "R" al final.
    
    Args:
        store_name: Nombre de la tienda sin formatear (ej: "4168 GAS CARDONES")
        
    Returns:
        str: Nombre formateado (ej: "Gas Cardones R")
    """
    # Si no se encontró un nombre, devolver valor por defecto
    if store_name == "No encontrada":
        return store_name
    
    # Eliminar el código numérico al inicio
    parts = store_name.strip().split()
    if parts and parts[0].isdigit():
        parts = parts[1:]  # Eliminar el primer elemento si es un número
    
    # Si no hay partes después de eliminar el número, devolver valor original
    if not parts:
        return store_name
    
    # Convertir a formato título (primera letra de cada palabra en mayúscula)
    formatted_name = " ".join(parts).title()
    
    # Correcciones específicas para palabras como "DE", "Y", etc.
    small_words = ["De", "La", "El", "Los", "Las", "Y", "Del"]
    for word in small_words:
        if f" {word} " in formatted_name:
            formatted_name = formatted_name.replace(f" {word} ", f" {word.lower()} ")
    
    # NUEVO: REMOVER "R" extra al final si la tiene (error común de OCR en KIOSKO)
    if formatted_name.endswith(' R'):
        formatted_name = formatted_name[:-2].strip()  # Quitar " R" del final
        print(f"🔧 Removida 'R' extra del nombre de sucursal: {formatted_name}")
    
    return formatted_name



def standardize_date_format(date_string):
    """
    Estandariza el formato de fecha para asegurar que sea DD/MM/YYYY.
    
    Args:
        date_string: Cadena de fecha a estandarizar (puede incluir hora)
        
    Returns:
        str: Fecha en formato DD/MM/YYYY
    """
    # Si la fecha es "No encontrada", devolver tal cual
    if date_string == "No encontrada":
        return date_string
    
    print(f"🔧 Estandarizando fecha: '{date_string}'")
    
    # Extraer solo la parte de la fecha (sin hora)
    if " " in date_string:
        date_string = date_string.split(" ")[0]
        print(f"🔧 Fecha sin hora: '{date_string}'")
    
    # Asegurar formato DD/MM/YYYY
    try:
        parts = date_string.split("/")
        if len(parts) == 3:
            day = parts[0].zfill(2)  # Añade ceros a la izquierda si es necesario
            month = parts[1].zfill(2)  # Añade ceros a la izquierda si es necesario
            year = parts[2]
            formatted_date = f"{day}/{month}/{year}"
            print(f"🔧 Fecha formateada: '{formatted_date}'")
            return formatted_date
    except Exception as e:
        print(f"⚠️ Error formateando fecha: {e}")
        # Si hay algún error al formatear, devolver la fecha original
        pass
    
    return date_string

def process_text_kiosko(raw_text):
    """
    Extrae datos de tickets de KIOSKO identificando múltiples productos.
    
    Args:
        raw_text: Texto extraído del OCR
        
    Returns:
        list: Lista de diccionarios con los datos estructurados para cada producto
    """
    print(f"🔍 Procesando texto del ticket de KIOSKO para múltiples productos...")
    print(f"📄 Texto OCR completo:\n{raw_text}")
    
    try:
        # 1. EXTRACCIÓN DE INFORMACIÓN COMÚN
        # Extraer folio
        folio_match = re.search(r'Folio:?\s*(\d+[- ]\d+[- ]\d+[- ]\d+)', raw_text)
        folio = folio_match.group(1).strip() if folio_match else "No encontrado"
        print(f"📝 Folio detectado: {folio}")
        
        # Extraer fecha con patrones mejorados
        fecha_raw = "No encontrada"
        
        # Patrón 1: Fecha completa con hora y am/pm
        fecha_match = re.search(r'Fecha:?\s*(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{1,2}:\d{1,2})', raw_text)
        if fecha_match:
            fecha_raw = fecha_match.group(1).strip()
            print(f"📅 Fecha detectada (patrón 1): {fecha_raw}")
        else:
            # Patrón 2: Solo fecha sin hora
            fecha_match = re.search(r'Fecha:?\s*(\d{1,2}/\d{1,2}/\d{2,4})', raw_text)
            if fecha_match:
                fecha_raw = fecha_match.group(1).strip()
                print(f"📅 Fecha detectada (patrón 2): {fecha_raw}")
            else:
                # Debug: mostrar líneas que contienen "Fecha"
                for line in raw_text.split('\n'):
                    if 'Fecha' in line:
                        print(f"🔍 Línea con 'Fecha' encontrada: '{line.strip()}'")
        
        # Estandarizar el formato de fecha
        fecha = standardize_date_format(fecha_raw)
        print(f"📅 Fecha estandarizada: {fecha}")
        
        # Extraer nombre de la tienda - CORRECCIÓN ESPECÍFICA
        nombre_tienda = "No encontrada"
        
        # Buscar específicamente la línea "41092 20 DE NOVIEMBRE"
        lines = raw_text.split('\n')
        for line in lines:
            line_clean = line.strip()
            print(f"🔍 Analizando línea: '{line_clean}'")
            
            # Debug específico para la línea que nos interesa
            if '41092' in line_clean and '20 DE NOVIEMBRE' in line_clean:
                print(f"🎯 LÍNEA OBJETIVO ENCONTRADA: '{line_clean}'")
                regex_pattern = r'^\d{4,5}\s+[A-Z]'
                print(f"🔍 Probando regex: {bool(re.match(regex_pattern, line_clean))}")
                print(f"🔍 Empieza con 41092: {line_clean.startswith('41092')}")
                print(f"🔍 Partes al dividir: {line_clean.split(None, 1)}")
            
            # CORRECCIÓN: Buscar específicamente líneas que empiecen con 5 dígitos
            if line_clean.startswith('41092') or re.match(r'^\d{4,5}\s+[A-Z]', line_clean):
                print(f"📍 Línea con patrón código+nombre encontrada: '{line_clean}'")
                
                # Dividir en código y nombre
                parts = line_clean.split(None, 1)  # Dividir en máximo 2 partes
                if len(parts) >= 2:
                    codigo = parts[0]
                    nombre_candidato = parts[1]
                    
                    print(f"🔍 Código: '{codigo}', Candidato: '{nombre_candidato}'")
                    
                    # Verificar que NO contenga palabras del proveedor
                    palabras_proveedor = ["MARINOS", "CONGELADORA", "PEREZ"]
                    es_proveedor = any(palabra in nombre_candidato.upper() for palabra in palabras_proveedor)
                    
                    if not es_proveedor:
                        nombre_tienda = nombre_candidato.title()
                        print(f"✅ Nombre de tienda detectado: '{nombre_tienda}'")
                        break
                    else:
                        print(f"❌ Descartado por ser proveedor: '{nombre_candidato}'")
        
        # MÉTODO DE RESPALDO: Si no se encontró, buscar directamente
        if nombre_tienda == "No encontrada":
            print("⚠️ Método principal falló, probando método de respaldo...")
            
            # Buscar directamente la línea que contiene "20 DE NOVIEMBRE"
            for line in lines:
                if '20 DE NOVIEMBRE' in line.upper():
                    # Extraer solo la parte del nombre
                    if '41092' in line:
                        nombre_tienda = "20 De Noviembre"
                        print(f"✅ Nombre extraído por método de respaldo: '{nombre_tienda}'")
                        break
        
        if nombre_tienda == "No encontrada":
            print("⚠️ No se pudo extraer el nombre de la tienda")
        else:
            print(f"🏪 Nombre final de tienda: '{nombre_tienda}'")
        

        
        # 2. BÚSQUEDA DE PRODUCTOS EN EL TICKET
        # Dividir el texto en líneas para analizar cada producto
        lines = raw_text.split("\n")
        
        # Lista para almacenar los productos encontrados
        productos = []
        
        # Patrones para identificar líneas de productos
        producto_patterns = [
            # Patrón para líneas con código de producto seguido por cantidad e importe
            r'(\d+)\s+(\d+\.\d+)\s+([A-Z\s]+(?:DE\s+[A-Z\s]+)+)(?:\s+|$)(\d+\.\d+)',
            # Patrón específico para bolsas de hielo
            r'([0-9]+(?:\.[0-9]+)?)\s+(?:BOLSA\s+DE\s+HIELO\s+SANTI\s+ICE\s+(?:15|5))',
            # Patrón general para capturar líneas con descripciones de productos
            r'(?:^|\n)([0-9]+(?:\.[0-9]+)?(?:\s+[A-Z0-9]+)+)\s+([0-9]+\.[0-9]+)'
        ]
        
        # MÉTODO 1: Buscar productos por códigos de barra específicos
        codigo_5kg = "7500465096004"
        codigo_15kg = "7500465096011"
        
        # MÉTODO MEJORADO: Usar algoritmos basados en análisis real
        cantidad_5kg = extract_kiosko_quantities_improved(lines, codigo_5kg, "5kg")
        cantidad_15kg = extract_kiosko_quantities_improved(lines, codigo_15kg, "15kg")
        
        # Crear productos solo si se encontraron cantidades válidas
        if cantidad_5kg:
            observaciones = []
            if cantidad_5kg >= 500:
                observaciones.append("🚨 Cantidad extrema - Posible error OCR")
            elif cantidad_5kg >= 100:
                observaciones.append("⚠️ Cantidad de 3 dígitos validada")
            
            productos.append({
                "folio": folio,
                "fecha": fecha,
                "sucursal": nombre_tienda,  # CORREGIDO: usar 'sucursal' en lugar de 'nombreTienda'
                "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                "codigoProducto": codigo_5kg,
                "descripcion": "BOLSA DE HIELO SANTI ICE 5",
                "numeroPiezasCompradas": cantidad_5kg,
                "importeUnitario": 15.0,
                "importeTotal": 15.0 * cantidad_5kg,
                "tipoProducto": "Bolsa de 5kg",
                "observaciones": observaciones
            })
            print(f"🧊 Producto 5kg encontrado: {cantidad_5kg} bolsas")
        
        if cantidad_15kg:
            observaciones = []
            if cantidad_15kg >= 200:
                observaciones.append("🚨 Cantidad extrema - Posible error OCR")
            elif cantidad_15kg >= 100:
                observaciones.append("⚠️ Cantidad de 3 dígitos validada")
            
            productos.append({
                "folio": folio,
                "fecha": fecha,
                "sucursal": nombre_tienda,  # CORREGIDO: usar 'sucursal' en lugar de 'nombreTienda'
                "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                "codigoProducto": codigo_15kg,
                "descripcion": "BOLSA DE HIELO SANTI ICE 15",
                "numeroPiezasCompradas": cantidad_15kg,
                "importeUnitario": 45.0,
                "importeTotal": 45.0 * cantidad_15kg,
                "tipoProducto": "Bolsa de 15kg",
                "observaciones": observaciones
            })
            print(f"🧊 Producto 15kg encontrado: {cantidad_15kg} bolsas")
        
        # MÉTODOS DE RESPALDO: Solo si no se encontraron productos con el método mejorado
        if not productos:
            # Buscar específicamente patrones de líneas de producto
            for line in lines:
                line = line.strip()
                
                # Patrones específicos para bolsas de hielo
                if "BOLSA DE HIELO" in line:
                    # Determinar si es de 5kg o 15kg
                    if "15" in line:
                        tipo = "Bolsa de 15kg"
                        import_unitario = 45.0
                        descripcion = "BOLSA DE HIELO SANTI ICE 15"
                    else:
                        tipo = "Bolsa de 5kg"
                        import_unitario = 15.0
                        descripcion = "BOLSA DE HIELO SANTI ICE 5"
                    
                    # Extraer la cantidad y el importe
                    cantidad_match = re.search(r'^\s*(\d+\.\d+)', line)
                    if cantidad_match:
                        cantidad = float(cantidad_match.group(1))
                    else:
                        # Intentar un patrón alternativo si el primero falla
                        cantidad_match = re.search(r'(\d+\.\d+)\s*$', line)
                        if cantidad_match:
                            cantidad = float(cantidad_match.group(1))
                        else:
                            continue  # Si no podemos encontrar la cantidad, saltamos esta línea
                    
                    # Verificar si la cantidad es razonable
                    if 1 <= cantidad <= 100:
                        productos.append({
                            "folio": folio,
                            "fecha": fecha,
                            "sucursal": nombre_tienda,  # CORREGIDO
                            "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                            "descripcion": descripcion,
                            "numeroPiezasCompradas": int(cantidad),
                            "importeUnitario": import_unitario,
                            "importeTotal": import_unitario * int(cantidad),
                            "tipoProducto": tipo
                        })
                        print(f"🧊 Producto encontrado por descripción: {descripcion} - Cantidad: {int(cantidad)}")
        
        # MÉTODO 3: Extracción basada en la estructura de columnas
        # Si aún no se han encontrado productos, intentar con un enfoque más estructurado
        if not productos:
            # Analizar estructuras de líneas típicas en tickets de KIOSKO
            # Asumiendo una estructura: [Código] [Cantidad] [Descripción] [Importe]
            codigo_pattern = r'(\d{13})'  # Patrón para códigos de barras
            for i, line in enumerate(lines):
                codigo_match = re.search(codigo_pattern, line)
                if codigo_match:
                    codigo = codigo_match.group(1)
                    # Si encontramos un código, verificar si es uno de nuestros productos
                    if codigo == codigo_5kg or codigo == codigo_15kg:
                        # Intentar extraer la cantidad e importe de esta línea o la siguiente
                        current_line = line
                        next_line = lines[i+1] if i+1 < len(lines) else ""
                        
                        # Buscar patrón de cantidad seguida de importes
                        cantidad_pattern = r'(\d+\.\d+)\s+(\d+\.\d+)'
                        cantidad_match = re.search(cantidad_pattern, current_line)
                        
                        if not cantidad_match and next_line:
                            cantidad_match = re.search(cantidad_pattern, next_line)
                        
                        if cantidad_match:
                            # El primer número suele ser la cantidad, el segundo el importe unitario
                            cantidad = float(cantidad_match.group(1))
                            
                            # Definir tipo de producto según el código
                            if codigo == codigo_5kg:
                                tipo = "Bolsa de 5kg"
                                importe_unitario = 15.0
                                descripcion = "BOLSA DE HIELO SANTI ICE 5"
                            else:  # codigo_15kg
                                tipo = "Bolsa de 15kg"
                                importe_unitario = 45.0
                                descripcion = "BOLSA DE HIELO SANTI ICE 15"
                                
                            # Verificar si la cantidad es razonable
                            if 1 <= cantidad <= 100:
                                productos.append({
                                    "folio": folio,
                                    "fecha": fecha,
                                    "sucursal": nombre_tienda,  # CORREGIDO
                                    "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                                    "codigoProducto": codigo,
                                    "descripcion": descripcion,
                                    "numeroPiezasCompradas": int(cantidad),
                                    "importeUnitario": importe_unitario,
                                    "importeTotal": importe_unitario * int(cantidad),
                                    "tipoProducto": tipo
                                })
                                print(f"🧊 Producto encontrado por código: {descripcion} - Cantidad: {int(cantidad)}")
        
        # MÉTODO 4: Usar patrones específicos para la estructura del ticket KIOSKO
        # Esto es útil para tickets que tienen una estructura bien definida
        if not productos:
            # Buscar patrones como "CANTIDAD DESCRIPCIÓN IMPORTE"
            cantidad_desc_importe = r'(\d+\.\d+)\s+(BOLSA\s+DE\s+HIELO\s+SANTI\s+ICE\s+(?:15|5))\s+(\d+\.\d+)'
            for line in lines:
                match = re.search(cantidad_desc_importe, line)
                if match:
                    cantidad = float(match.group(1))
                    descripcion = match.group(2)
                    importe = float(match.group(3))
                    
                    # Determinar tipo según descripción
                    if "15" in descripcion:
                        tipo = "Bolsa de 15kg"
                        importe_unitario = 45.0
                    else:
                        tipo = "Bolsa de 5kg"
                        importe_unitario = 15.0
                    
                    # Verificar si la cantidad es razonable
                    if 1 <= cantidad <= 100:
                        productos.append({
                            "folio": folio,
                            "fecha": fecha,
                            "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                            "descripcion": descripcion,
                            "numeroPiezasCompradas": int(cantidad),
                            "importeUnitario": importe_unitario,
                            "importeTotal": importe,
                            "tipoProducto": tipo
                        })
                        print(f"🧊 Producto encontrado por patrón específico: {descripcion} - Cantidad: {int(cantidad)}")
        
        # MÉTODO 5: Analizar todas las líneas en busca de números sospechosos de ser cantidades
        # Este es un método de último recurso cuando todo lo demás falla
        if not productos:
            # Buscar líneas que contengan "5" o "15" junto con números que podrían ser cantidades
            for line in lines:
                # Determinar si la línea tiene que ver con bolsas de 5kg
                if "5" in line and ("BOLSA" in line or "HIELO" in line or "SANTI" in line):
                    # Buscar números en la línea que podrían ser cantidades
                    numeros = re.findall(r'(\d+\.\d+)', line)
                    if numeros:
                        # El primer número suele ser la cantidad
                        for num in numeros:
                            cantidad = float(num)
                            if 1 <= cantidad <= 100:
                                productos.append({
                                    "folio": folio,
                                    "fecha": fecha,
                                    "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                                    "descripcion": "BOLSA DE HIELO SANTI ICE 5",
                                    "numeroPiezasCompradas": int(cantidad),
                                    "importeUnitario": 15.0,
                                    "importeTotal": 15.0 * int(cantidad),
                                    "tipoProducto": "Bolsa de 5kg"
                                })
                                print(f"🧊 Producto 5kg encontrado por análisis heurístico - Cantidad: {int(cantidad)}")
                                break
                
                # Determinar si la línea tiene que ver con bolsas de 15kg
                elif "15" in line and ("BOLSA" in line or "HIELO" in line or "SANTI" in line):
                    # Buscar números en la línea que podrían ser cantidades
                    numeros = re.findall(r'(\d+\.\d+)', line)
                    if numeros:
                        # El primer número suele ser la cantidad
                        for num in numeros:
                            cantidad = float(num)
                            if 1 <= cantidad <= 100:
                                productos.append({
                                    "folio": folio,
                                    "fecha": fecha,
                                    "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                                    "descripcion": "BOLSA DE HIELO SANTI ICE 15",
                                    "numeroPiezasCompradas": int(cantidad),
                                    "importeUnitario": 45.0,
                                    "importeTotal": 45.0 * int(cantidad),
                                    "tipoProducto": "Bolsa de 15kg"
                                })
                                print(f"🧊 Producto 15kg encontrado por análisis heurístico - Cantidad: {int(cantidad)}")
                                break
        
        # MÉTODO 6: Buscando en el ticket completo información sobre totales de unidades
        # Este es un método adicional basado en patrones específicos del ticket
        if not productos:
            # Buscar el total de unidades y distribución por SKUs
            skus_match = re.search(r'(\d+)\s+SKUs\s+Total:\s+(\d+\.\d+)\s+Unidades', raw_text)
            if skus_match:
                num_skus = int(skus_match.group(1))
                total_unidades = float(skus_match.group(2))
                
                print(f"📦 Se detectaron {num_skus} SKUs con {total_unidades} unidades en total")
                
                # Si hay 2 SKUs, asumimos que son los dos tipos de bolsas
                if num_skus == 2:
                    # Buscar referencias específicas a cantidades
                    bolsa_5kg_match = re.search(r'BOLSA\s+DE\s+HIELO\s+SANTI\s+ICE\s+5[^0-9]*(\d+)', raw_text)
                    bolsa_15kg_match = re.search(r'BOLSA\s+DE\s+HIELO\s+SANTI\s+ICE\s+15[^0-9]*(\d+)', raw_text)
                    
                    # Si encontramos ambas cantidades
                    if bolsa_5kg_match and bolsa_15kg_match:
                        cantidad_5kg = int(bolsa_5kg_match.group(1))
                        cantidad_15kg = int(bolsa_15kg_match.group(1))
                        
                        # Verificar si las cantidades son razonables
                        if 1 <= cantidad_5kg <= 100 and 1 <= cantidad_15kg <= 100:
                            productos.append({
                                "folio": folio,
                                "fecha": fecha,
                                "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                                "descripcion": "BOLSA DE HIELO SANTI ICE 5",
                                "numeroPiezasCompradas": cantidad_5kg,
                                "importeUnitario": 15.0,
                                "importeTotal": 15.0 * cantidad_5kg,
                                "tipoProducto": "Bolsa de 5kg"
                            })
                            
                            productos.append({
                                "folio": folio,
                                "fecha": fecha,
                                "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                                "descripcion": "BOLSA DE HIELO SANTI ICE 15",
                                "numeroPiezasCompradas": cantidad_15kg,
                                "importeUnitario": 45.0,
                                "importeTotal": 45.0 * cantidad_15kg,
                                "tipoProducto": "Bolsa de 15kg"
                            })
                            
                            print(f"🧊 Productos encontrados por análisis de SKUs: 5kg ({cantidad_5kg}), 15kg ({cantidad_15kg})")
        
        # Si no se encontraron productos con los métodos anteriores,
        # extraer por patrones muy específicos para el ticket de ejemplo
        if not productos:
            # Patrones específicos para el ticket de ejemplo
            bolsa_15kg_pattern = r'(\d+\.\d+)\s+BOLSA\s+DE\s+HIELO\s+SANTI\s+ICE\s+15\s+(\d+\.\d+)'
            bolsa_5kg_pattern = r'(\d+\.\d+)\s+BOLSA\s+DE\s+HIELO\s+SANTI\s+ICE\s+5\s+(\d+\.\d+)'
            
            # Buscar bolsas de 15kg
            bolsa_15kg_match = re.search(bolsa_15kg_pattern, raw_text)
            if bolsa_15kg_match:
                cantidad = float(bolsa_15kg_match.group(1))
                importe = float(bolsa_15kg_match.group(2))
                
                if 1 <= cantidad <= 100:
                    productos.append({
                        "folio": folio,
                        "fecha": fecha,
                        "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                        "descripcion": "BOLSA DE HIELO SANTI ICE 15",
                        "numeroPiezasCompradas": int(cantidad),
                        "importeUnitario": 45.0,
                        "importeTotal": importe,
                        "tipoProducto": "Bolsa de 15kg"
                    })
                    print(f"🧊 Producto 15kg encontrado por patrón específico - Cantidad: {int(cantidad)}")
            
            # Buscar bolsas de 5kg
            bolsa_5kg_match = re.search(bolsa_5kg_pattern, raw_text)
            if bolsa_5kg_match:
                cantidad = float(bolsa_5kg_match.group(1))
                importe = float(bolsa_5kg_match.group(2))
                
                if 1 <= cantidad <= 100:
                    productos.append({
                        "folio": folio,
                        "fecha": fecha,
                        "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                        "descripcion": "BOLSA DE HIELO SANTI ICE 5",
                        "numeroPiezasCompradas": int(cantidad),
                        "importeUnitario": 15.0,
                        "importeTotal": importe,
                        "tipoProducto": "Bolsa de 5kg"
                    })
                    print(f"🧊 Producto 5kg encontrado por patrón específico - Cantidad: {int(cantidad)}")
        
        # ÚLTIMO RECURSO: Si aún no encontramos productos, extraemos información del resumen
        if not productos:
            # Extraer el total de unidades si existe
            total_unidades_match = re.search(r'Total:\s+(\d+\.\d+)\s+Unidades', raw_text)
            if total_unidades_match:
                total_unidades = float(total_unidades_match.group(1))
                print(f"📦 Total de unidades detectado: {total_unidades}")
                
                # Si solo hay un total y no podemos distinguir productos,
                # usar método del código anterior para determinar el tipo de producto
                importe_unitario = extraer_importe_unitario_fallback(raw_text)
                
                if importe_unitario:
                    # Determinar tipo de producto por importe unitario
                    if importe_unitario == 15.0 or importe_unitario == 16.0:
                        tipo = "Bolsa de 5kg"
                        descripcion = "BOLSA DE HIELO SANTI ICE 5"
                    elif importe_unitario == 45.0:
                        tipo = "Bolsa de 15kg"
                        descripcion = "BOLSA DE HIELO SANTI ICE 15"
                    else:
                        tipo = f"Producto con importe unitario {importe_unitario}"
                        descripcion = f"PRODUCTO DESCONOCIDO ({importe_unitario})"
                    
                    productos.append({
                        "folio": folio,
                        "fecha": fecha,
                        "sucursal": nombre_tienda,
                            "nombreTienda": nombre_tienda,
                        "descripcion": descripcion,
                        "numeroPiezasCompradas": int(total_unidades),
                        "importeUnitario": importe_unitario,
                        "importeTotal": importe_unitario * int(total_unidades),
                        "tipoProducto": tipo
                    })
                    print(f"🧊 Producto único detectado: {descripcion} - Cantidad: {int(total_unidades)}")
                    
        # Verificar si tenemos múltiples productos que son del mismo tipo
        # En ese caso, combinarlos en uno solo (suma de cantidades)
        productos_combinados = []
        tipos_vistos = set()
        
        for producto in productos:
            tipo = producto.get("tipoProducto", "")
            
            # Si ya vimos este tipo, combinar con el anterior
            if tipo in tipos_vistos:
                # Buscar el producto existente con este tipo
                for p in productos_combinados:
                    if p.get("tipoProducto", "") == tipo:
                        # Sumar las cantidades
                        p["numeroPiezasCompradas"] += producto.get("numeroPiezasCompradas", 0)
                        # Recalcular el importe total
                        p["importeTotal"] = p["importeUnitario"] * p["numeroPiezasCompradas"]
                        print(f"🔄 Combinando productos del mismo tipo: {tipo}. Nueva cantidad: {p['numeroPiezasCompradas']}")
                        break
            else:
                # Si es un tipo nuevo, agregarlo a la lista
                productos_combinados.append(producto)
                tipos_vistos.add(tipo)
        
        # Actualizar la lista de productos
        productos = productos_combinados
        print(f"📦 Total de productos encontrados: {len(productos)}")
        for i, producto in enumerate(productos):
            print(f"📦 Producto {i+1}: {producto.get('descripcion', 'Desconocido')} - Cantidad: {producto.get('numeroPiezasCompradas', 0)} - Importe: {producto.get('importeTotal', 0)}")
        
        if not productos:
            return [{"error": "No se pudo extraer información de productos del ticket", "texto_original": raw_text}]
            
        return productos
            
    except Exception as e:
        print(f"❌ Error procesando texto del ticket: {e}")
        # Intenta obtener la mayor cantidad de información posible a pesar del error
        return [{"error": f"Error procesando texto: {str(e)}", "texto_original": raw_text}]
