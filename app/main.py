import os
import sys
import boto3
import uuid
import base64
from typing import List
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Agregar directorio actual al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno
load_dotenv()

# Importar autenticación
from auth.routes import router as auth_router

# Importar dependencias del conciliador
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
    # Intentar importar tu sistema real
    try:
        import sys
        sys.path.append('modules/conciliator')
        from modules.conciliator.processors.factory import ProcessorFactory, get_supported_clients
        from modules.conciliator.reconciler import Reconciler
        from modules.conciliator.report_generator import ReportGenerator
        REAL_CONCILIATOR = True
        print("✅ Sistema de conciliación real cargado")
    except ImportError as e:
        print(f"⚠️ Sistema básico de conciliación: {e}")
        REAL_CONCILIATOR = False
except ImportError:
    PANDAS_AVAILABLE = False
    REAL_CONCILIATOR = False

# Crear rutas del conciliador directamente
from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import Response
from typing import Dict, List, Optional
import asyncio
import json
import shutil
from pathlib import Path

conciliator_router = APIRouter(prefix="/api/conciliator", tags=["conciliator"])

# Estados y configuración del conciliador
conciliator_sessions = {}
conciliator_websockets = {}

CONCILIATOR_AVAILABLE = True
print("✅ Módulo conciliador integrado directamente")
from services.textract import analyze_text, analyze_text_with_fallback
from services.ticket_detector import validate_ticket_content
from services.textprocess_KIOSKO import process_text_kiosko as process_kiosko
from services.textprocess_OXXO import process_text_oxxo as process_oxxo
from services.google_sheets import send_to_google_sheets
from services.ticket_detector import detect_ticket_type

# Modelos Pydantic
class TicketData(BaseModel):
    id: str
    filename: str
    sucursal: str
    fecha: str
    productos: List[dict]
    confidence: float
    status: str
    sucursal_type: str
    # Campos opcionales según el tipo
    remision: str = None
    pedido_adicional: str = None
    folio: str = None

class ConfirmTicketsRequest(BaseModel):
    tickets: List[TicketData]
    precios_config: dict = {}

# Verificar si estamos en entorno local o Lambda
IS_LAMBDA = os.environ.get('AWS_EXECUTION_ENV') is not None

# Solo importar Mangum si estamos en Lambda
if IS_LAMBDA:
    from mangum import Mangum

# Configuración para S3
s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'santiice-ocr-tickets')

app = FastAPI(
    title="SantiICE OCR System",
    description="Sistema de OCR para tickets con autenticación",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost", "http://localhost:80", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de autenticación
app.include_router(auth_router)

# Modelos del conciliador
class ClientInfo(BaseModel):
    id: str
    name: str
    description: str
    status: str
    tolerances: Dict[str, float]
    capabilities: List[str]

class DateRange(BaseModel):
    startDate: str
    endDate: str

class ProcessingRequest(BaseModel):
    session_id: str
    client_type: str
    date_range: DateRange

# Rutas del conciliador
@conciliator_router.get("/clients")
async def get_conciliator_clients():
    """Obtiene clientes disponibles para conciliación"""
    clients = [
        {
            "id": "OXXO",
            "name": "OXXO",
            "description": "Conciliación de tickets OXXO vs Looker",
            "status": "✅ Funcional",
            "tolerances": {"percentage": 5.0, "absolute": 50.0},
            "capabilities": ["grouping", "filtering", "validation"]
        },
        {
            "id": "KIOSKO",
            "name": "KIOSKO",
            "description": "Conciliación de tickets KIOSKO vs Looker",
            "status": "✅ Funcional",
            "tolerances": {"percentage": 3.0, "absolute": 25.0},
            "capabilities": ["mixed_ids", "product_grouping", "strict_validation"]
        }
    ]
    return clients

@conciliator_router.post("/session")
async def create_conciliator_session():
    """Crea una nueva sesión de conciliación"""
    session_id = str(uuid.uuid4())
    conciliator_sessions[session_id] = {
        "created_at": datetime.now(),
        "files": {},
        "status": "created",
        "results": None
    }
    print(f"🆕 Sesión creada: {session_id}")
    return {"session_id": session_id}

@conciliator_router.post("/upload/{session_id}")
async def upload_conciliator_file(
    session_id: str,
    file: UploadFile = File(...),
    file_type: str = Form("source")
):
    """Sube archivos para conciliación"""
    print(f"📤 Recibiendo archivo: {file.filename} como tipo: {file_type}")
    
    if session_id not in conciliator_sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    if file_type not in ['source', 'looker']:
        raise HTTPException(status_code=400, detail="Tipo debe ser 'source' o 'looker'")
    
    # Crear directorio
    upload_dir = Path("uploads/conciliator") / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar archivo
    file_path = upload_dir / f"{file_type}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Actualizar sesión
    if "files" not in conciliator_sessions[session_id]:
        conciliator_sessions[session_id]["files"] = {}
    
    conciliator_sessions[session_id]["files"][file_type] = {
        "filename": file.filename,
        "path": str(file_path),
        "size": file_path.stat().st_size,
        "uploaded_at": datetime.now().isoformat()
    }
    
    print(f"✅ Archivo {file_type} guardado en sesión {session_id}")
    print(f"📁 Archivos actuales: {list(conciliator_sessions[session_id]['files'].keys())}")
    
    return {
        "message": "Archivo subido exitosamente",
        "filename": file.filename,
        "size": file_path.stat().st_size,
        "type": file_type
    }

@conciliator_router.post("/process/{session_id}")
async def process_conciliator_files(
    session_id: str,
    background_tasks: BackgroundTasks,
    request: dict
):
    """Procesa conciliación en background"""
    try:
        print(f"🔍 Procesando sesión: {session_id}")
        print(f"📝 Request data: {request}")
        
        if session_id not in conciliator_sessions:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        session = conciliator_sessions[session_id]
        print(f"📁 Archivos en sesión: {list(session.get('files', {}).keys())}")
        print(f"📄 Detalles de archivos: {session.get('files', {})}")
        
        if 'source' not in session.get('files', {}) or 'looker' not in session.get('files', {}):
            missing = []
            if 'source' not in session.get('files', {}):
                missing.append('source')
            if 'looker' not in session.get('files', {}):
                missing.append('looker')
            raise HTTPException(status_code=400, detail=f"Faltan archivos: {', '.join(missing)}")
        
        client_type = request.get('client_type', 'OXXO')
        date_range = request.get('date_range', {})
        
        session["status"] = "processing"
        session["client_type"] = client_type
        session["date_range"] = date_range
        
        print(f"✅ Iniciando procesamiento para {client_type}")
        
        # Procesar en background
        background_tasks.add_task(process_conciliation_background, session_id, client_type)
        
        return {"message": "Procesamiento iniciado", "session_id": session_id}
        
    except Exception as e:
        print(f"❌ Error en process: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    """Procesa conciliación en background"""
    if session_id not in conciliator_sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = conciliator_sessions[session_id]
    if 'source' not in session['files'] or 'looker' not in session['files']:
        raise HTTPException(status_code=400, detail="Faltan archivos")
    
    session["status"] = "processing"
    session["client_type"] = request.client_type
    session["date_range"] = request.date_range.dict()
    
    # Procesar en background
    background_tasks.add_task(process_conciliation_background, session_id, request.client_type)
    
    return {"message": "Procesamiento iniciado", "session_id": session_id}

async def process_conciliation_background(session_id: str, client_type: str):
    """Procesa conciliación en background usando tu sistema real"""
    try:
        session = conciliator_sessions[session_id]
        source_file = session['files']['source']['path']
        looker_file = session['files']['looker']['path']
        
        print(f"📄 Procesando archivos reales:")
        print(f"   Source: {source_file}")
        print(f"   Looker: {looker_file}")
        
        if REAL_CONCILIATOR and PANDAS_AVAILABLE:
            # Usar tu sistema real de conciliación
            print(f"🚀 Usando sistema real de conciliación")
            
            # Crear procesador
            processor = ProcessorFactory.create_processor(client_type)
            source_data, looker_data = processor.process_files(source_file, looker_file)
            
            print(f"📈 Datos leídos - Source: {len(source_data)} filas, Looker: {len(looker_data)} filas")
            
            # Crear reconciliador
            reconciler = Reconciler(client_type)
            reconciliation_results = reconciler.reconcile(source_data, looker_data)
            summary_stats = reconciler.get_summary_stats()
            
            print(f"📉 Conciliación completada - {summary_stats.get('total_records', 0)} registros")
            
            # Convertir resultados a formato esperado por el frontend
            records = []
            for _, row in reconciliation_results.iterrows():
                records.append({
                    "id": str(row.get('id_matching', row.get('id_source', row.get('id_looker', 'N/A')))),
                    "client_value": float(row.get('valor_source_clean', 0)) if pd.notna(row.get('valor_source_clean', 0)) else 0.0,
                    "looker_value": float(row.get('valor_looker_clean', 0)) if pd.notna(row.get('valor_looker_clean', 0)) else 0.0,
                    "difference": float(row.get('diferencia', 0)) if pd.notna(row.get('diferencia', 0)) else 0.0,
                    "status": str(row.get('categoria', 'UNKNOWN')),
                    "category": str(row.get('categoria', 'Sin clasificar'))
                })
            
            # Usar estadísticas reales - convertir a tipos nativos de Python
            result = {
                "session_id": session_id,
                "success": True,
                "summary": {
                    "total_records": int(summary_stats.get('total_records', 0)),
                    "exact_matches": int(summary_stats.get('exact_matches', 0)),
                    "within_tolerance": int(summary_stats.get('within_tolerance', 0)),
                    "major_differences": int(summary_stats.get('major_differences', 0)),
                    "missing_records": int(summary_stats.get('missing_records', 0)),
                    "reconciliation_rate": float(summary_stats.get('reconciliation_rate', 0)),
                    "total_client_amount": float(summary_stats.get(f'total_valor_{client_type.lower()}', 0)),
                    "total_looker_amount": float(summary_stats.get('total_valor_looker', 0)),
                    "total_difference": float(summary_stats.get('total_diferencia', 0))
                },
                "records": records[:50],  # Limitar a 50 registros para el frontend
                "reports_generated": [],
                "processing_time": 2.5,
                "timestamp": datetime.now().isoformat()
            }
            
        elif PANDAS_AVAILABLE:
            # Fallback con pandas básico
            print(f"🔄 Usando procesamiento básico con pandas")
            
            # Leer archivos
            if source_file.endswith('.csv'):
                source_data = pd.read_csv(source_file)
            else:
                source_data = pd.read_excel(source_file)
            
            if looker_file.endswith('.csv'):
                looker_data = pd.read_csv(looker_file)
            else:
                looker_data = pd.read_excel(looker_file)
            
            print(f"📈 Archivos leídos - Source: {len(source_data)} filas, Looker: {len(looker_data)} filas")
            
            # Procesamiento básico de conciliación
            # Buscar columnas de ID y valor
            source_id_col = None
            source_val_col = None
            looker_id_col = None
            looker_val_col = None
            
            # Detectar columnas en archivo source
            for col in source_data.columns:
                col_lower = col.lower()
                if any(x in col_lower for x in ['id', 'folio', 'ticket', 'transaccion']) and source_id_col is None:
                    source_id_col = col
                if any(x in col_lower for x in ['total', 'importe', 'valor', 'amount', 'monto']) and source_val_col is None:
                    source_val_col = col
            
            # Detectar columnas en archivo looker
            for col in looker_data.columns:
                col_lower = col.lower()
                if any(x in col_lower for x in ['id', 'folio', 'ticket', 'transaccion']) and looker_id_col is None:
                    looker_id_col = col
                if any(x in col_lower for x in ['total', 'importe', 'valor', 'amount', 'monto']) and looker_val_col is None:
                    looker_val_col = col
            
            print(f"🔍 Columnas detectadas:")
            print(f"   Source ID: {source_id_col}, Valor: {source_val_col}")
            print(f"   Looker ID: {looker_id_col}, Valor: {looker_val_col}")
            
            if source_id_col and source_val_col and looker_id_col and looker_val_col:
                # Realizar merge
                merged = pd.merge(
                    source_data[[source_id_col, source_val_col]].rename(columns={source_id_col: 'id', source_val_col: 'source_value'}),
                    looker_data[[looker_id_col, looker_val_col]].rename(columns={looker_id_col: 'id', looker_val_col: 'looker_value'}),
                    on='id',
                    how='outer'
                )
                
                # Limpiar valores
                merged['source_value'] = pd.to_numeric(merged['source_value'], errors='coerce').fillna(0)
                merged['looker_value'] = pd.to_numeric(merged['looker_value'], errors='coerce').fillna(0)
                merged['difference'] = merged['source_value'] - merged['looker_value']
                
                # Categorizar
                def categorize(row):
                    if pd.isna(row['source_value']) or row['source_value'] == 0:
                        return 'MISSING_IN_SOURCE'
                    elif pd.isna(row['looker_value']) or row['looker_value'] == 0:
                        return 'MISSING_IN_LOOKER'
                    elif abs(row['difference']) == 0:
                        return 'EXACT_MATCH'
                    elif abs(row['difference']) <= 50:  # Tolerancia
                        return 'WITHIN_TOLERANCE'
                    else:
                        return 'MAJOR_DIFFERENCE'
                
                merged['status'] = merged.apply(categorize, axis=1)
                
                # Crear registros
                records = []
                for _, row in merged.iterrows():
                    records.append({
                        "id": str(row['id']),
                        "client_value": float(row['source_value']),
                        "looker_value": float(row['looker_value']),
                        "difference": float(row['difference']),
                        "status": row['status'],
                        "category": {
                            'EXACT_MATCH': 'Conciliado',
                            'WITHIN_TOLERANCE': 'Tolerancia',
                            'MAJOR_DIFFERENCE': 'Diferencia',
                            'MINOR_DIFFERENCE': 'Diferencia',
                            'MISSING_IN_SOURCE': 'Faltante',
                            'MISSING_IN_LOOKER': 'Faltante',
                            'MISSING_IN_OXXO': 'Faltante',
                            'MISSING_IN_KIOSKO': 'Faltante'
                        }.get(row['status'], 'Sin clasificar')
                    })
                
                # Calcular estadísticas
                total_records = len(merged)
                exact_matches = len(merged[merged['status'] == 'EXACT_MATCH'])
                within_tolerance = len(merged[merged['status'] == 'WITHIN_TOLERANCE'])
                major_differences = len(merged[merged['status'] == 'MAJOR_DIFFERENCE'])
                missing_records = len(merged[merged['status'].str.contains('MISSING')])
                
                result = {
                    "session_id": session_id,
                    "success": True,
                    "summary": {
                        "total_records": total_records,
                        "exact_matches": exact_matches,
                        "within_tolerance": within_tolerance,
                        "major_differences": major_differences,
                        "missing_records": missing_records,
                        "reconciliation_rate": ((exact_matches + within_tolerance) / total_records * 100) if total_records > 0 else 0,
                        "total_client_amount": float(merged['source_value'].sum()),
                        "total_looker_amount": float(merged['looker_value'].sum()),
                        "total_difference": float(merged['difference'].sum())
                    },
                    "records": records[:50],  # Limitar para el frontend
                    "reports_generated": [],
                    "processing_time": 2.5,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception("No se pudieron detectar las columnas necesarias en los archivos")
        else:
            raise Exception("Pandas no está disponible para procesar archivos Excel/CSV")
        
        # Guardar resultado
        session["status"] = "completed"
        session["results"] = result
        
        # Notificar via WebSocket si está conectado
        if session_id in conciliator_websockets:
            try:
                await conciliator_websockets[session_id].send_text(json.dumps({
                    "type": "completed",
                    "result": result
                }))
                print(f"📡 Resultados enviados via WebSocket para sesión {session_id}")
            except Exception as ws_error:
                print(f"❌ Error enviando WebSocket: {ws_error}")
        else:
            print(f"⚠️ No hay conexión WebSocket activa para sesión {session_id}")
        
        print(f"✅ Conciliación completada para sesión {session_id}")
        
    except Exception as e:
        print(f"❌ Error en conciliación {session_id}: {e}")
        session["status"] = "error"
        session["error"] = str(e)

@conciliator_router.get("/results/{session_id}")
async def get_conciliator_results(session_id: str):
    """Obtiene resultados de conciliación"""
    print(f"🔍 Solicitando resultados para sesión: {session_id}")
    
    if session_id not in conciliator_sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = conciliator_sessions[session_id]
    print(f"📋 Estado de la sesión: {session['status']}")
    
    if session["status"] == "processing":
        return {"status": "processing", "message": "Procesamiento en curso..."}
    elif session["status"] != "completed":
        return {"status": session["status"], "message": "Procesamiento no completado"}
    
    if "results" not in session or session["results"] is None:
        raise HTTPException(status_code=500, detail="Resultados no disponibles")
    
    print(f"✅ Enviando resultados para sesión {session_id}")
    return session["results"]

@conciliator_router.websocket("/ws/{session_id}")
async def conciliator_websocket(websocket: WebSocket, session_id: str):
    """WebSocket para actualizaciones en tiempo real"""
    await websocket.accept()
    conciliator_websockets[session_id] = websocket
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        if session_id in conciliator_websockets:
            del conciliator_websockets[session_id]

# Incluir rutas del conciliador
app.include_router(conciliator_router)
print("✅ Módulo conciliador cargado directamente")

# Solo usar StaticFiles en entorno local
if not IS_LAMBDA:
    # Configurar carpeta estática
    if not os.path.exists("static"):
        os.makedirs("static")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Servir logo desde frontend/public
    @app.get("/LOGO SANTI ICE.png")
    async def serve_logo():
        logo_path = "../frontend/public/LOGO SANTI ICE.png"
        if os.path.exists(logo_path):
            return FileResponse(logo_path)
        return JSONResponse({"error": "Logo no encontrado"}, status_code=404)
    
    @app.get("/")
    async def serve_index():
        return FileResponse("static/index.html")
else:
    # En Lambda, servir una respuesta simple para la ruta raíz
    @app.get("/")
    async def serve_index():
        return {"message": "SantiICE OCR API is running"}


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Procesa una imagen de un ticket, extrae su texto y lo envía a Google Sheets.
    El tipo de sucursal se detecta automáticamente.
    
    Args:
        file: Archivo de imagen del ticket
        
    Returns:
        JSONResponse con los resultados del procesamiento
    """
    try:
        # Validación del archivo
        if not file:
            raise HTTPException(status_code=400, detail="Archivo no recibido")

        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(status_code=400, detail="Archivo vacío")

        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Formato de archivo no permitido. Usa JPEG o PNG.")

        # Si estamos en Lambda, guardar el archivo en S3
        if IS_LAMBDA:
            s3_key = f"uploads/{file.filename}"
            s3.put_object(
                Body=image_bytes,
                Bucket=BUCKET_NAME,
                Key=s3_key,
                ContentType=file.content_type
            )
            print(f"📤 Archivo subido a S3: s3://{BUCKET_NAME}/{s3_key}")

        # Extracción de texto con OCR mejorado
        print(f"📝 Analizando imagen '{file.filename}'...")
        ocr_result = analyze_text_with_fallback(image_bytes)
        ocr_text = ocr_result.get('text', '')
        
        # Log de información del OCR
        confidence = ocr_result.get('confidence', 0)
        preprocessed = ocr_result.get('preprocessed', False)
        print(f"📊 OCR completado - Confianza: {confidence:.1f}%, Preprocesado: {preprocessed}")
        
        if not ocr_text or len(ocr_text.strip()) < 10:
            raise HTTPException(status_code=500, detail="No se pudo extraer texto suficiente del archivo.")

        # Detección automática del tipo de ticket
        sucursal = detect_ticket_type(ocr_text)
        print(f"🔍 Tipo de ticket detectado automáticamente: {sucursal} (archivo: {file.filename})")
        
        # Validar consistencia del ticket
        es_valido, confianza_validacion, observaciones = validate_ticket_content(ocr_text, sucursal)
        
        if not es_valido:
            print(f"⚠️ Advertencia: Baja confianza en tipo de ticket ({confianza_validacion}%)")
            for obs in observaciones:
                print(f"   - {obs}")

        # Procesamiento del texto según el tipo de sucursal
        print(f"🔍 Procesando texto para {sucursal} (archivo: {file.filename})")
        processed_data = process_kiosko(ocr_text) if sucursal == "KIOSKO" else process_oxxo(ocr_text)
        
        # Verificar si hubo errores en el procesamiento
        if isinstance(processed_data, dict) and "error" in processed_data:
            raise HTTPException(status_code=500, detail=processed_data["error"])

        # Asegurar que los datos estén en formato de lista
        if not isinstance(processed_data, list):
            processed_data = [processed_data]

        # Verificar que hay datos para procesar
        if not processed_data:
            raise HTTPException(status_code=400, detail="No se pudo extraer información válida del ticket.")
        
        # Validar confianza mínima para producción
        for item in processed_data:
            if sucursal == "OXXO":
                cantidad = item.get('cantidad', 0)
                if cantidad == 0:
                    raise HTTPException(
                        status_code=422, 
                        detail=f"Ticket requiere revisión manual: No se pudo extraer cantidad con suficiente confianza para {item.get('descripcion', 'producto')}."
                    )
            elif sucursal == "KIOSKO":
                cantidad = item.get('numeroPiezasCompradas', 0)
                if cantidad == 0:
                    raise HTTPException(
                        status_code=422, 
                        detail=f"Ticket requiere revisión manual: No se pudo extraer cantidad con suficiente confianza para {item.get('descripcion', 'producto')}."
                    )
        
        # Log de productos encontrados
        print(f"📄 Se encontraron {len(processed_data)} productos en el ticket {sucursal} (archivo: {file.filename})")
        for i, item in enumerate(processed_data):
            if sucursal == "OXXO":
                print(f"📄 Producto {i+1}: Costo={item.get('costo')}, Cantidad={item.get('cantidad')}")
            else:  # KIOSKO
                print(f"📄 Producto {i+1}: Tipo={item.get('tipoProducto')}, Cantidad={item.get('numeroPiezasCompradas')}")

        # Enviar datos a Google Sheets
        print(f"🛠️ Enviando datos a Google Sheets para archivo: {file.filename}")
        
        # Para tickets OXXO con múltiples productos, verificar duplicados solo para el primer producto
        if sucursal == "OXXO" and len(processed_data) > 1:
            # Primero verificamos si alguno de los productos ya está registrado
            first_product = processed_data[0]
            verify_response = send_to_google_sheets(sucursal, [first_product], origen="extracción")
            
            # Si el primer producto está duplicado, asumimos que todo el ticket está duplicado
            if verify_response.get("duplicated", False):
                print(f"🚫 Rechazando ticket duplicado ({file.filename}): {verify_response.get('message')}")
                return JSONResponse(
                    status_code=409,  # Código 409 Conflict para indicar duplicado
                    content={
                        "message": "Ticket duplicado detectado",
                        "details": verify_response.get("message", "Este ticket ya ha sido procesado anteriormente."),
                        "duplicated": True,
                        "rejected": True,
                        "detected_type": sucursal,
                        "filename": file.filename
                    }
                )
        
        # Si no hay duplicados, procedemos a guardar todos los productos
        google_sheets_response = send_to_google_sheets(sucursal, processed_data, origen="extracción")
        
        # Verificar si se detectó un duplicado y rechazar la solicitud
        if google_sheets_response.get("duplicated", False):
            print(f"🚫 Rechazando ticket duplicado ({file.filename}): {google_sheets_response.get('message')}")
            return JSONResponse(
                status_code=409,  # Código 409 Conflict para indicar duplicado
                content={
                    "message": "Ticket duplicado detectado",
                    "details": google_sheets_response.get("message", "Este ticket ya ha sido procesado anteriormente."),
                    "duplicated": True,
                    "rejected": True,
                    "detected_type": sucursal,
                    "filename": file.filename
                }
            )
        
        # Verificar si hubo algún otro error
        if not google_sheets_response.get("success", False):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Error al guardar en Google Sheets",
                    "details": google_sheets_response.get("message", "Error desconocido")
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Ticket procesado exitosamente",
                "success": True,
                "detected_type": sucursal,
                "filename": file.filename,
                "products_count": len(processed_data)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Error interno del servidor",
                "details": str(e)
            }
        )

@app.post("/process-tickets")
async def process_tickets(files: List[UploadFile] = File(...)):
    """
    Procesa múltiples tickets y devuelve los datos extraídos para revisión.
    NO envía los datos a Google Sheets.
    """
    results = []
    
    for file in files:
        try:
            if not file or not file.filename:
                continue
                
            image_bytes = await file.read()
            if not image_bytes or file.content_type not in ["image/jpeg", "image/png"]:
                continue
            
            ticket_id = str(uuid.uuid4())
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            ocr_result = analyze_text_with_fallback(image_bytes)
            ocr_text = ocr_result.get('text', '')
            confidence = ocr_result.get('confidence', 0)
            
            if len(ocr_text.strip()) < 10:
                results.append({
                    "id": ticket_id,
                    "filename": file.filename,
                    "status": "error",
                    "error": "No se pudo extraer texto suficiente",
                    "confidence": 0,
                    "image_base64": f"data:{file.content_type};base64,{image_base64}"
                })
                continue
            
            sucursal_type = detect_ticket_type(ocr_text)
            processed_data = process_kiosko(ocr_text) if sucursal_type == "KIOSKO" else process_oxxo(ocr_text)
            
            if isinstance(processed_data, dict) and "error" in processed_data:
                results.append({
                    "id": ticket_id,
                    "filename": file.filename,
                    "status": "error",
                    "error": processed_data["error"],
                    "confidence": confidence,
                    "image_base64": f"data:{file.content_type};base64,{image_base64}"
                })
                continue
            
            if not isinstance(processed_data, list):
                processed_data = [processed_data]
            
            first_item = processed_data[0] if processed_data else {}
            
            # Campos específicos según el tipo de ticket
            ticket_data = {
                "id": ticket_id,
                "filename": file.filename,
                "sucursal": first_item.get('sucursal', 'No detectada'),
                "fecha": first_item.get('fecha', 'No detectada'),
                "productos": processed_data,
                "confidence": confidence,
                "status": "processed",
                "sucursal_type": sucursal_type,
                "image_base64": f"data:{file.content_type};base64,{image_base64}"
            }
            
            # Agregar campos específicos según el tipo
            if sucursal_type == "OXXO":
                ticket_data.update({
                    "remision": first_item.get('remision', 'No detectada'),
                    "pedido_adicional": first_item.get('pedido_adicional', 'No detectado')
                })
            else:  # KIOSKO
                ticket_data.update({
                    "folio": first_item.get('folio', 'No detectado')
                })
            
            results.append(ticket_data)
            
        except Exception as e:
            results.append({
                "id": str(uuid.uuid4()),
                "filename": file.filename if file else "unknown",
                "status": "error",
                "error": str(e),
                "confidence": 0
            })
    
    return JSONResponse(content={
        "success": True,
        "total_files": len(files),
        "processed": len([r for r in results if r["status"] == "processed"]),
        "errors": len([r for r in results if r["status"] == "error"]),
        "results": results
    })

@app.post("/confirm-tickets")
async def confirm_tickets(request: ConfirmTicketsRequest):
    """
    Recibe los tickets validados por el usuario y los envía a Google Sheets.
    """
    import asyncio
    results = []
    
    for i, ticket in enumerate(request.tickets):
        try:
            # Usar el tipo de sucursal del ticket directamente
            sucursal_type = getattr(ticket, 'sucursal_type', None)
            if not sucursal_type:
                # Fallback: detectar por contenido de productos
                sucursal_type = "OXXO" if any('costo' in p for p in ticket.productos) else "KIOSKO"
            
            print(f"🔍 Confirmando ticket {ticket.filename} como {sucursal_type}")
            print(f"📝 Datos del ticket: Sucursal={ticket.sucursal}, Fecha={ticket.fecha}")
            
            # Log de los primeros productos para verificar sincronización
            if ticket.productos:
                primer_producto = ticket.productos[0]
                print(f"📝 Primer producto - Sucursal: {primer_producto.get('sucursal', 'N/A')}, NombreTienda: {primer_producto.get('nombreTienda', 'N/A')}")
            
            # Determinar el origen basado en si el ticket viene de procesamiento de imagen o entrada manual
            # Si el ticket tiene confidence < 100, viene de procesamiento de imagen (extracción)
            # Si tiene confidence = 100, es entrada manual
            origen = "manual" if ticket.confidence == 100 else "extracción"
            
            response = send_to_google_sheets(sucursal_type, ticket.productos, request.precios_config, origen=origen)
            
            results.append({
                "id": ticket.id,
                "filename": ticket.filename,
                "status": "success" if response.get("success") else "error",
                "message": response.get("message", "Procesado correctamente"),
                "duplicated": response.get("duplicated", False)
            })
            
            # Delay progresivo para evitar límites de cuota
            if i > 0:
                delay_seconds = min(i * 1.0, 5.0)  # Máximo 5 segundos
                print(f"⏳ Esperando {delay_seconds}s antes del siguiente ticket...")
                await asyncio.sleep(delay_seconds)
            
        except Exception as e:
            results.append({
                "id": ticket.id,
                "filename": ticket.filename,
                "status": "error",
                "message": str(e)
            })
    
    return JSONResponse(content={
        "success": True,
        "results": results,
        "summary": {
            "total": len(results),
            "success": len([r for r in results if r["status"] == "success"]),
            "errors": len([r for r in results if r["status"] == "error"]),
            "duplicated": len([r for r in results if r.get("duplicated")])
        }
    })
        

@app.post("/get-upload-url")
async def get_upload_url(request: Request):
    """
    Genera una URL prefirmada de S3 para subir un archivo directamente desde el frontend.
    
    Args:
        request: Solicitud que contiene el nombre del archivo
        
    Returns:
        JSONResponse con la URL prefirmada y la clave S3
    """
    try:
        data = await request.json()
        filename = data.get("filename")
        
        if not filename:
            return JSONResponse(
                status_code=400,
                content={"error": "Se requiere un nombre de archivo"}
            )
        
        # Generar un nombre de archivo único
        unique_filename = f"uploads/{uuid.uuid4()}-{filename}"
        
        # Crear URL prefirmada de S3
        s3_client = boto3.client('s3')
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': unique_filename,
                'ContentType': 'image/jpeg'  # Ajustar según el tipo de archivo
            },
            ExpiresIn=300  # URL válida por 5 minutos
        )
        
        return JSONResponse(content={
            "uploadUrl": presigned_url,
            "s3Key": unique_filename
        })
    except Exception as e:
        print(f"❌ Error generando URL de carga: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error interno: {str(e)}"}
        )


@app.post("/process-uploaded-file")
async def process_uploaded_file(request: Request):
    """
    Procesa un archivo previamente subido a S3.
    
    Args:
        request: Solicitud que contiene la clave S3 del archivo
        
    Returns:
        JSONResponse con los resultados del procesamiento
    """
    try:
        data = await request.json()
        s3_key = data.get("s3Key")
        
        if not s3_key:
            return JSONResponse(
                status_code=400, 
                content={"error": "Se requiere la clave S3 del archivo"}
            )
            
        print(f"🔍 Procesando archivo S3: {s3_key}")
            
        # Obtener el archivo de S3
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        image_bytes = response['Body'].read()
        
        # Extraer nombre de archivo de la clave S3
        filename = s3_key.split('/')[-1]
        if '-' in filename:
            # Si tiene formato UUID-nombrearchivo.jpg
            filename = filename.split('-', 1)[1]
        
        # Extracción de texto con OCR mejorado
        print(f"📝 Analizando imagen '{filename}'...")
        ocr_result = analyze_text_with_fallback(image_bytes)
        ocr_text = ocr_result.get('text', '')
        
        # Log de información del OCR
        confidence = ocr_result.get('confidence', 0)
        preprocessed = ocr_result.get('preprocessed', False)
        print(f"📊 OCR completado - Confianza: {confidence:.1f}%, Preprocesado: {preprocessed}")
        
        if not ocr_text or len(ocr_text.strip()) < 10:
            raise HTTPException(status_code=500, detail="No se pudo extraer texto suficiente del archivo.")
        
        # Detección automática del tipo de ticket
        sucursal = detect_ticket_type(ocr_text)
        print(f"🔍 Tipo de ticket detectado automáticamente: {sucursal} (archivo: {filename})")
        
        # Validar consistencia del ticket
        es_valido, confianza_validacion, observaciones = validate_ticket_content(ocr_text, sucursal)
        
        if not es_valido:
            print(f"⚠️ Advertencia: Baja confianza en tipo de ticket ({confianza_validacion}%)")
            for obs in observaciones:
                print(f"   - {obs}")
        
        # Procesamiento del texto según el tipo de sucursal
        print(f"🔍 Procesando texto para {sucursal} (archivo: {filename})")
        processed_data = process_kiosko(ocr_text) if sucursal == "KIOSKO" else process_oxxo(ocr_text)
        
        # Verificar si hubo errores en el procesamiento
        if isinstance(processed_data, dict) and "error" in processed_data:
            raise HTTPException(status_code=500, detail=processed_data["error"])
        
        # Asegurar que los datos estén en formato de lista
        if not isinstance(processed_data, list):
            processed_data = [processed_data]
        
        # Verificar que hay datos para procesar
        if not processed_data:
            raise HTTPException(status_code=400, detail="No se pudo extraer información válida del ticket.")
        
        # Validar confianza mínima para producción
        for item in processed_data:
            if sucursal == "OXXO":
                cantidad = item.get('cantidad', 0)
                if cantidad == 0:
                    raise HTTPException(
                        status_code=422, 
                        detail=f"Ticket requiere revisión manual: No se pudo extraer cantidad con suficiente confianza para {item.get('descripcion', 'producto')}."
                    )
            elif sucursal == "KIOSKO":
                cantidad = item.get('numeroPiezasCompradas', 0)
                if cantidad == 0:
                    raise HTTPException(
                        status_code=422, 
                        detail=f"Ticket requiere revisión manual: No se pudo extraer cantidad con suficiente confianza para {item.get('descripcion', 'producto')}."
                    )
        
        # Log de productos encontrados
        print(f"📄 Se encontraron {len(processed_data)} productos en el ticket {sucursal} (archivo: {filename})")
        for i, item in enumerate(processed_data):
            if sucursal == "OXXO":
                print(f"📄 Producto {i+1}: Costo={item.get('costo')}, Cantidad={item.get('cantidad')}")
            else:  # KIOSKO
                print(f"📄 Producto {i+1}: Tipo={item.get('tipoProducto')}, Cantidad={item.get('numeroPiezasCompradas')}")
        
        # Enviar datos a Google Sheets
        print(f"🛠️ Enviando datos a Google Sheets para archivo: {filename}")
        
        # Para tickets OXXO con múltiples productos, verificar duplicados solo para el primer producto
        if sucursal == "OXXO" and len(processed_data) > 1:
            # Primero verificamos si alguno de los productos ya está registrado
            first_product = processed_data[0]
            verify_response = send_to_google_sheets(sucursal, [first_product], origen="extracción")
            
            # Si el primer producto está duplicado, asumimos que todo el ticket está duplicado
            if verify_response.get("duplicated", False):
                print(f"🚫 Rechazando ticket duplicado ({filename}): {verify_response.get('message')}")
                return JSONResponse(
                    status_code=409,  # Código 409 Conflict para indicar duplicado
                    content={
                        "message": "Ticket duplicado detectado",
                        "details": verify_response.get("message", "Este ticket ya ha sido procesado anteriormente."),
                        "duplicated": True,
                        "rejected": True,
                        "detected_type": sucursal,
                        "filename": filename
                    }
                )
        
        # Si no hay duplicados, procedemos a guardar todos los productos
        google_sheets_response = send_to_google_sheets(sucursal, processed_data, origen="extracción")
        
        # Verificar si se detectó un duplicado y rechazar la solicitud
        if google_sheets_response.get("duplicated", False):
            print(f"🚫 Rechazando ticket duplicado ({filename}): {google_sheets_response.get('message')}")
            return JSONResponse(
                status_code=409,  # Código 409 Conflict para indicar duplicado
                content={
                    "message": "Ticket duplicado detectado",
                    "details": google_sheets_response.get("message", "Este ticket ya ha sido procesado anteriormente."),
                    "duplicated": True,
                    "rejected": True,
                    "detected_type": sucursal,
                    "filename": filename
                }
            )
        
        # Verificar si hubo algún otro error
        if not google_sheets_response.get("success", False):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Error al guardar en Google Sheets",
                    "details": google_sheets_response.get("message", "Error desconocido"),
                    "detected_type": sucursal,
                    "filename": filename
                }
            )
        
        # Si todo fue exitoso
        return JSONResponse(content={
            "message": "Procesamiento exitoso",
            "products_count": len(processed_data),
            "data": processed_data,
            "google_sheets_response": google_sheets_response,
            "detected_type": sucursal,
            "filename": filename
        })
    
    except HTTPException as e:
        # Re-lanzar las excepciones HTTP directamente
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.detail}
        )
    
    except Exception as e:
        # Capturar cualquier otra excepción no manejada
        print(f"❌ Error interno no manejado: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error interno: {str(e)}"}
        )


# Handler para Lambda (solo si estamos en entorno Lambda)
if IS_LAMBDA:
    handler = Mangum(app)