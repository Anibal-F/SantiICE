import json
import boto3
from google.oauth2.service_account import Credentials
import os
import gspread

# 📌 Configuración de Google Sheets
SHEET_ID = "1fjyyofqYP36bGEzRKPhEtzzL1VLT4KkU8EFc4WbaeQM"  # ID de Google Sheet
SHEET_NAME = "Base de Datos"  # Nombre de la hoja
CREDENTIALS_PATH = "/Users/analistadesoporte/SantiICE-OCR/service_account.json"

def send_to_google_sheets(sucursal: str, data: list, precios_config: dict = None, origen: str = "extracción"):
    """
    Envía datos a Google Sheets y verifica si ya existen registros duplicados.
    
    Args:
        sucursal: String con el nombre de la sucursal ('OXXO' o 'KIOSKO')
        data: Lista de diccionarios con los datos a enviar
        
    Returns:
        dict: Diccionario con el resultado de la operación
    """
    print(f"🔍 Datos recibidos en send_to_google_sheets: {data}")
    print(f"📝 Origen del registro: {origen}")
    
    # Validar parámetros de entrada
    if not sucursal:
        print("❌ Error: No se proporcionó la sucursal.")
        return {"success": False, "message": "No se proporcionó la sucursal.", "duplicated": False}
    
    if not data or not isinstance(data, (dict, list)):
        print("❌ Error: Formato de datos no válido.")
        return {"success": False, "message": "Formato de datos no válido para Google Sheets.", "duplicated": False}

    # Convertir a lista si es un diccionario
    if isinstance(data, dict):
        data = [data]
        
    # Filtrar elementos que no sean diccionarios o no tengan las claves necesarias
    data = [item for item in data if isinstance(item, dict)]
    
    if not data:
        print("❌ Error: No hay datos válidos para procesar.")
        return {"success": False, "message": "No hay datos válidos para procesar.", "duplicated": False}
    
    try:
        # 🔐 Autenticación con la cuenta de servicio
        credentials_path = get_google_credentials()
        creds = Credentials.from_service_account_file(credentials_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

        # 📊 Obtener todos los datos actuales
        all_values = sheet.get_all_values()
        headers = all_values[0] if all_values else []
        
        # Procesamiento específico por tipo de sucursal
        if sucursal == "OXXO":
            return process_oxxo_tickets(data, all_values, headers, sheet, precios_config, origen)
        elif sucursal == "KIOSKO":
            return process_kiosko_tickets(data, all_values, headers, sheet, precios_config, origen)
        else:
            print(f"❌ Tipo de sucursal no reconocido: {sucursal}")
            return {"success": False, "message": f"Tipo de sucursal no reconocido: {sucursal}", "duplicated": False}

    except gspread.exceptions.APIError as api_error:
        print(f"❌ Error en API de Google Sheets: {api_error}")
        return {
            "success": False, 
            "message": f"APIError: {str(api_error)}",
            "duplicated": False
        }

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return {
            "success": False, 
            "message": str(e),
            "duplicated": False
        }


def process_oxxo_tickets(data, all_values, headers, sheet, precios_config=None, origen="extracción"):
    """
    Procesa tickets de OXXO para verificar duplicados y guardarlos.
    """
    if not data:
        return {"success": False, "message": "No hay datos para procesar", "duplicated": False}
    
    # Extraer información del primer elemento para identificar el ticket
    remision = str(data[0].get("remision", "")).strip()
    pedido = str(data[0].get("pedido_adicional", "")).strip()
    
    print(f"🔍 Procesando ticket OXXO - Remisión: {remision}, Pedido: {pedido}")
    
    # Crear índices de las columnas importantes
    col_indices = {}
    for i, header in enumerate(headers):
        col_indices[header] = i
    
    # Imprimir las columnas para diagnóstico
    print(f"📋 Columnas disponibles: {headers}")
    
    # Determinar los índices de las columnas relevantes
    remision_col = col_indices.get("Remisión", -1)
    pedido_col = col_indices.get("No. Pedido", -1)
    producto_col = col_indices.get("Producto", -1)
    
    # Imprimir los índices para depuración
    print(f"📊 Índices de columnas: Remisión={remision_col}, Pedido={pedido_col}, Producto={producto_col}")
    
    # Lista para guardar los registros encontrados que coinciden con este ticket
    registros_encontrados = []
    
    # Verificar qué productos ya existen en la base de datos
    if remision_col != -1 and pedido_col != -1 and producto_col != -1:
        # Buscar en todos los registros existentes
        print(f"🔍 Buscando registros con remisión '{remision}' y pedido '{pedido}'...")
        
        for row_idx, row in enumerate(all_values[1:], start=2):  # Omitir encabezados, empezar numerando desde 2
            if len(row) <= max(remision_col, pedido_col, producto_col):
                continue  # Fila demasiado corta, saltar
                
            record_remision = row[remision_col].strip() if remision_col < len(row) else ""
            record_pedido = row[pedido_col].strip() if pedido_col < len(row) else ""
            record_producto = row[producto_col].strip().lower() if producto_col < len(row) else ""
            
            # Verificar si este registro coincide con nuestro ticket
            if record_remision == remision and record_pedido == pedido:
                print(f"📋 Fila {row_idx}: Remisión='{record_remision}', Pedido='{record_pedido}', Producto='{record_producto}'")
                registros_encontrados.append(row)
    
    # Determinar qué productos existen
    productos_existentes = {"5kg": False, "15kg": False}
    
    for registro in registros_encontrados:
        producto = registro[producto_col].strip().lower()
        print(f"🔍 Analizando registro existente con producto: '{producto}'")
        
        # IMPORTANTE: Verificación mutualmente excluyente
        if "5kg" in producto and "15kg" not in producto:
            productos_existentes["5kg"] = True
            print(f"✅ Encontrado producto de 5kg existente en la base de datos")
        elif "15kg" in producto:
            productos_existentes["15kg"] = True
            print(f"✅ Encontrado producto de 15kg existente en la base de datos")
    
    # Imprimir un resumen de lo que encontramos
    print(f"📊 Resumen de productos existentes: 5kg={productos_existentes['5kg']}, 15kg={productos_existentes['15kg']}")
    
    # Clasificar los productos a insertar
    productos_a_insertar = []
    productos_duplicados = []
    
    # Imprimir los datos que estamos procesando
    print(f"📦 Procesando {len(data)} productos para insertar/verificar:")
    for idx, item in enumerate(data):
        print(f"  📦 Producto {idx+1}: {item}")
    
    for item in data:
        costo = item.get("costo", 0)
        
        if abs(costo - 17.5) < 0.1:
            tipo = "5kg"
            descripcion = "Bolsa de 5kg"
        elif abs(costo - 37.5) < 0.1:
            tipo = "15kg"
            descripcion = "Bolsa de 15kg"
        else:
            tipo = "otro"
            descripcion = f"Producto con costo {costo}"
            
        print(f"🔍 Analizando producto: {descripcion}, Costo: {costo}")
        
        # Verificar si este tipo de producto ya existe
        if tipo in productos_existentes and productos_existentes[tipo]:
            print(f"⚠️ Producto {descripcion} ya existe en la base de datos para este ticket")
            productos_duplicados.append(item)
        else:
            print(f"✅ Producto {descripcion} no existe en la base de datos para este ticket")
            productos_a_insertar.append(item)
    
    # Si todos son duplicados
    if not productos_a_insertar and productos_duplicados:
        # Verificar si encontramos ambos tipos
        if productos_existentes.get("5kg", False) and productos_existentes.get("15kg", False):
            print(f"⚠️ Ambos productos (5kg y 15kg) ya existen para el ticket remisión={remision}, pedido={pedido}")
            return {
                "success": False,
                "message": f"El ticket de OXXO con remisión {remision} y pedido {pedido} ya existe completo.",
                "duplicated": True
            }
        else:
            # Si no encontramos ambos tipos pero aún así no hay nada que insertar
            return {
                "success": False,
                "message": f"Los productos específicos que intentas insertar ya existen para este ticket.",
                "duplicated": True
            }
    
    # Si tenemos productos para guardar, procedemos
    if productos_a_insertar:
        # Obtener la última fila ocupada
        last_filled_row = len(all_values)
        initial_row_count = last_filled_row
        
        print(f"📄 Última fila ocupada: {last_filled_row}, insertando en: {initial_row_count}")
        
        successful_inserts = 0
        
        for item in productos_a_insertar:
            # Usar la descripción que viene del frontend
            descripcion = item.get("descripcion", "Producto desconocido")
            
            print(f"📝 Guardando: {descripcion} - Cantidad: {item['cantidad']} - Remisión: {remision} - Pedido: {pedido}")
            
            # Insertar una nueva fila
            initial_row_count += 1
            
            # Usar el precio que viene del frontend (campo 'costo')
            cantidad = item.get("cantidad", 0)
            precio_unitario = item.get("costo", 17.5)  # Usar el costo enviado desde el frontend
            
            total_venta = precio_unitario * cantidad
            
            print(f"💰 Calculando total: {cantidad} x {precio_unitario} = {total_venta}")
            
            # Actualizar celdas en Google Sheets
            sheet.update_cell(initial_row_count, 3, item["fecha"])
            sheet.update_cell(initial_row_count, 4, descripcion)
            sheet.update_cell(initial_row_count, 5, item["cantidad"])
            sheet.update_cell(initial_row_count, 6, "OXXO")
            sheet.update_cell(initial_row_count, 9, item["sucursal"])
            sheet.update_cell(initial_row_count, 10, item["remision"])
            sheet.update_cell(initial_row_count, 11, item["pedido_adicional"])
            sheet.update_cell(initial_row_count, 15, total_venta)  # Columna O (15)
            sheet.update_cell(initial_row_count, 16, origen)  # Columna P (16) - extraido/manual
            successful_inserts += 1
        
        if successful_inserts > 0:
            if productos_duplicados:
                return {
                    "success": True,
                    "message": f"Se guardaron {successful_inserts} productos. Se omitieron {len(productos_duplicados)} productos duplicados.",
                    "duplicated": False
                }
            else:
                return {
                    "success": True,
                    "message": f"Se guardaron {successful_inserts} productos correctamente.",
                    "duplicated": False
                }
    
    return {
        "success": False,
        "message": "No se pudo guardar ningún producto nuevo.",
        "duplicated": True
    }


def process_kiosko_tickets(data, all_values, headers, sheet, precios_config=None, origen="extracción"):
    """
    Procesa tickets de KIOSKO para verificar duplicados y guardarlos.
    """
    if not data:
        return {"success": False, "message": "No hay datos para procesar", "duplicated": False}
    
    # Crear índices de las columnas importantes
    col_indices = {}
    for i, header in enumerate(headers):
        col_indices[header] = i
    
    folio_col = col_indices.get("Folio del Ticket", -1)
    fecha_col = col_indices.get("Submitted at", -1)
    producto_col = col_indices.get("Producto", -1)
    
    # Lista para guardar productos a guardar o duplicados
    productos_a_insertar = []
    productos_duplicados = []
    
    # Conjunto para almacenar folios que ya han sido detectados como duplicados
    folios_duplicados = set()
    
    for item in data:
        print(f"🔍 Verificando producto KIOSKO: {item}")
        is_duplicate = False
        
        if "folio" in item:
            # Para KIOSKO, verificamos por folio
            folio_to_check = str(item.get("folio", "")).strip()
            
            # Si este folio ya fue detectado como duplicado, marcar este item como duplicado también
            if folio_to_check in folios_duplicados:
                print(f"⚠️ Folio '{folio_to_check}' ya marcado como duplicado anteriormente.")
                is_duplicate = True
                continue
            
            fecha_to_check = str(item.get("fecha", "")).strip()
            
            # Determinar el tipo de producto
            if "tipoProducto" in item and item["tipoProducto"]:
                tipo_producto_to_check = item["tipoProducto"]
            elif "descripcion" in item and "5" in item["descripcion"]:
                tipo_producto_to_check = "Bolsa de 5kg"
            elif "descripcion" in item and "15" in item["descripcion"]:
                tipo_producto_to_check = "Bolsa de 15kg"
            elif "importeUnitario" in item:
                importe = float(item["importeUnitario"])
                if importe == 15.0 or importe == 16.0:
                    tipo_producto_to_check = "Bolsa de 5kg"
                elif importe == 45.0:
                    tipo_producto_to_check = "Bolsa de 15kg"
                else:
                    tipo_producto_to_check = f"Producto con importe {importe}"
            else:
                tipo_producto_to_check = "Producto desconocido"
            
            print(f"🔎 Buscando ticket KIOSKO con folio: '{folio_to_check}', fecha: '{fecha_to_check}', tipo: '{tipo_producto_to_check}'")
            
            # Buscar en todos los registros existentes
            for row in all_values[1:]:  # Omitir encabezados
                if folio_col >= len(row) or fecha_col >= len(row) or producto_col >= len(row):
                    continue  # Fila demasiado corta, saltar
                    
                record_folio = row[folio_col].strip()
                record_fecha = row[fecha_col].strip()
                
                # Ignorar registros con folios vacíos
                if not record_folio:
                    continue
                
                # Verificar si es el mismo folio
                folio_match = (folio_to_check == record_folio) or (
                    len(folio_to_check) > 3 and len(record_folio) > 3 and 
                    (folio_to_check in record_folio or record_folio in folio_to_check)
                )
                
                if folio_match:
                    print(f"⚠️ Posible coincidencia de folio encontrada: '{folio_to_check}' vs '{record_folio}'")
                    
                    # También verificar la fecha
                    fecha_match = (fecha_to_check == record_fecha) or (
                        len(fecha_to_check) > 5 and len(record_fecha) > 5 and
                        (fecha_to_check in record_fecha or record_fecha in fecha_to_check)
                    )
                    
                    if fecha_match:
                        print(f"⚠️ Ticket KIOSKO duplicado encontrado: Folio '{folio_to_check}', Fecha '{fecha_to_check}'")
                        is_duplicate = True
                        folios_duplicados.add(folio_to_check)
                        break
        
        # Si no es duplicado, lo agregamos a la lista para guardar
        if not is_duplicate:
            productos_a_insertar.append(item)
        else:
            productos_duplicados.append(item)
    
    # Si no hay nada para guardar y todos son duplicados
    if not productos_a_insertar and productos_duplicados:
        return {
            "success": False, 
            "message": f"El ticket de KIOSKO con folio {productos_duplicados[0].get('folio', '')} ya existe.",
            "duplicated": True
        }
    
    # Si tenemos productos para guardar, procedemos
    if productos_a_insertar:
        # Obtener la última fila ocupada
        last_filled_row = len(all_values)
        initial_row_count = last_filled_row
        
        print(f"📄 Última fila ocupada: {last_filled_row}, insertando en: {initial_row_count}")
        
        successful_inserts = 0
        
        for item in productos_a_insertar:
            # Determinar el tipo de producto
            if "tipoProducto" in item and item["tipoProducto"]:
                descripcion = item["tipoProducto"]
            elif "descripcion" in item and item["descripcion"]:
                descripcion = item["descripcion"]
            elif "importeUnitario" in item:
                importe_unitario = float(item["importeUnitario"])
                if importe_unitario == 15.0 or importe_unitario == 16.0:
                    descripcion = "Bolsa de 5kg"
                elif importe_unitario == 45.0:
                    descripcion = "Bolsa de 15kg"
                else:
                    descripcion = f"Producto con importe {importe_unitario}"
            else:
                descripcion = "Producto desconocido"
            
            # Determinar la cantidad de piezas
            if "numeroPiezasCompradas" in item and item["numeroPiezasCompradas"]:
                cantidad = item["numeroPiezasCompradas"]
            else:
                # Cálculo de respaldo si no tenemos la cantidad directa
                importe_total = item.get("importeTotal", 0)
                importe_unitario = item.get("importeUnitario", 0)
                if importe_unitario > 0 and importe_total > 0:
                    cantidad = round(importe_total / importe_unitario)
                else:
                    cantidad = 0
            
            # Determinar tipo de producto
            sucursal_nombre = item.get("nombreTienda", "")
            
            if "tipoProducto" in item and item["tipoProducto"]:
                if "5kg" in item["tipoProducto"].lower():
                    tipo_producto = "5kg"
                elif "15kg" in item["tipoProducto"].lower():
                    tipo_producto = "15kg"
                else:
                    tipo_producto = "5kg"
            elif "descripcion" in item and item["descripcion"]:
                if "5" in item["descripcion"] and "15" not in item["descripcion"]:
                    tipo_producto = "5kg"
                elif "15" in item["descripcion"]:
                    tipo_producto = "15kg"
                else:
                    tipo_producto = "5kg"
            else:
                tipo_producto = "5kg"
            
            # Precios por defecto con excepciones específicas
            sucursales_44_pesos = ["Occidental", "Solidaridad", "Miguel Hidalgo", "Francisco Perez"]
            
            print(f"🔍 Debug precios - Sucursal: '{sucursal_nombre}', Tipo: '{tipo_producto}'")
            print(f"🔍 Sucursales $44: {sucursales_44_pesos}")
            print(f"🔍 ¿Está en lista?: {sucursal_nombre in sucursales_44_pesos}")
            
            if tipo_producto == "15kg" and sucursal_nombre in sucursales_44_pesos:
                precio_unitario = 44.0
                print(f"💰 Aplicando precio especial $44 para {sucursal_nombre}")
            elif tipo_producto == "15kg":
                precio_unitario = 45.0
                print(f"💰 Aplicando precio normal $45 para 15kg")
            else:
                precio_unitario = 16.0
                print(f"💰 Aplicando precio $16 para 5kg")
            
            total_venta = precio_unitario * cantidad
            
            print(f"💰 Calculando total KIOSKO: {cantidad} x {precio_unitario} = {total_venta}")
            
            # Insertar una nueva fila
            initial_row_count += 1
            
            # Actualizar celdas en Google Sheets
            sheet.update_cell(initial_row_count, 13, item["folio"])
            sheet.update_cell(initial_row_count, 3, item["fecha"])
            sheet.update_cell(initial_row_count, 4, descripcion)
            sheet.update_cell(initial_row_count, 5, cantidad)
            sheet.update_cell(initial_row_count, 6, "KIOSKO")
            sheet.update_cell(initial_row_count, 15, total_venta)  # Columna O (15)
            sheet.update_cell(initial_row_count, 16, origen)  # Columna P (16) - extraido/manual
            
            # Usar nombreTienda si está disponible
            if "nombreTienda" in item and item["nombreTienda"] and item["nombreTienda"] != "No encontrada":
                sheet.update_cell(initial_row_count, 12, item["nombreTienda"])
            
            successful_inserts += 1
        
        if successful_inserts > 0:
            if productos_duplicados:
                return {
                    "success": True,
                    "message": f"Se guardaron {successful_inserts} productos. Se omitieron {len(productos_duplicados)} productos duplicados.",
                    "duplicated": False
                }
            else:
                return {
                    "success": True,
                    "message": f"Se guardaron {successful_inserts} productos correctamente.",
                    "duplicated": False
                }
    
    return {
        "success": False,
        "message": "No se pudo guardar ningún producto nuevo.",
        "duplicated": True
    }


def get_google_credentials():
    """
    Obtiene las credenciales de Google desde AWS Secrets Manager o archivo local
    dependiendo del entorno.
    """
    # Verificar si estamos en Lambda
    is_lambda = os.environ.get('AWS_EXECUTION_ENV') is not None
    
    if is_lambda:
        # En Lambda, obtener las credenciales de Secrets Manager
        try:
            print("🔐 Obteniendo credenciales desde AWS Secrets Manager...")
            secret_name = os.environ.get('GOOGLE_CREDENTIALS_SECRET_NAME')
            if not secret_name:
                raise ValueError("La variable GOOGLE_CREDENTIALS_SECRET_NAME no está configurada")
                
            client = boto3.client('secretsmanager')
            response = client.get_secret_value(SecretId=secret_name)
            secret = response['SecretString']
            
            # Guardar temporalmente en un archivo para que gspread pueda usarlo
            temp_creds_path = "/tmp/google_credentials.json"
            with open(temp_creds_path, "w") as f:
                f.write(secret)
                
            return temp_creds_path
        except Exception as e:
            print(f"❌ Error obteniendo credenciales desde Secrets Manager: {e}")
            # Si falla, intentar con el archivo local en la carpeta de credenciales
            local_creds_path = '/app/credentials/credentials.json'
            if os.path.exists(local_creds_path):
                print(f"⚠️ Usando credenciales locales como fallback en: {local_creds_path}")
                return local_creds_path
            raise Exception(f"No se pudieron obtener las credenciales de Google: {e}")
    else:
        # En desarrollo local, usar el archivo de credenciales
        local_creds_path = '/app/credentials/credentials.json'
        if not os.path.exists(local_creds_path):
            raise Exception(f"Archivo de credenciales no encontrado en: {local_creds_path}")
        
        return local_creds_path

def get_credentials_path():
    """Retorna la ruta al archivo de credenciales según el entorno"""
    is_lambda = os.environ.get('AWS_EXECUTION_ENV') is not None
    
    if is_lambda:
        # En Lambda, el código se ejecuta desde el directorio raíz del paquete
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials', 'credentials.json')
    else:
        # En desarrollo local
        return os.path.join('app', 'credentials', 'credentials.json')