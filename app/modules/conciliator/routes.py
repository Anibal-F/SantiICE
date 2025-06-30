#!/usr/bin/env python3
"""
Rutas del módulo Conciliador
Integradas en el backend principal
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import pandas as pd
import uuid
import os
import shutil
import json
import asyncio
import logging
from datetime import datetime
import glob
from pathlib import Path

# Imports del sistema conciliador
try:
    from .processors.factory import ProcessorFactory, get_supported_clients
    from .reconciler import Reconciler
    from .report_generator import ReportGenerator
    from .config import config
except ImportError:
    # Fallback para demo sin dependencias
    class ProcessorFactory:
        @staticmethod
        def get_client_info(client_id):
            return {'display_name': client_id, 'description': f'Procesador {client_id}', 'capabilities': []}
        @staticmethod
        def validate_client_config(client_id):
            return True
        @staticmethod
        def create_processor(client_id):
            return None
    
    def get_supported_clients():
        return ['OXXO', 'KIOSKO']
    
    class Reconciler:
        def __init__(self, client_type):
            self.client_type = client_type
        def reconcile(self, source_data, looker_data):
            return None
        def get_summary_stats(self):
            return {}
    
    class ReportGenerator:
        def __init__(self, client_type):
            self.client_type = client_type
        def generate_complete_report(self, data, stats, filename):
            return f"/tmp/{filename}.xlsx"
        def generate_csv_reports(self, data, filename):
            return {"completo": f"/tmp/{filename}.csv"}
    
    config = {}

# Router para el módulo conciliador
router = APIRouter(prefix="/api/conciliator", tags=["conciliator"])

# Directorio para logs de sesiones
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Configurar logging
logger = logging.getLogger(__name__)

# Almacenamiento temporal de sesiones
sessions = {}
websocket_connections = {}

# Modelos Pydantic
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

class ReconciliationSummary(BaseModel):
    total_records: int
    exact_matches: int
    within_tolerance: int
    major_differences: int
    missing_records: int
    reconciliation_rate: float
    total_client_amount: float
    total_looker_amount: float
    total_difference: float

class ReconciliationRecord(BaseModel):
    id: str
    client_value: float
    looker_value: float
    difference: float
    status: str
    category: str
    fecha: Optional[str] = None
    editable: bool = True

class ProcessingResult(BaseModel):
    session_id: str
    success: bool
    summary: ReconciliationSummary
    records: List[ReconciliationRecord]
    reports_generated: List[str]
    processing_time: float
    timestamp: str

class WebSocketManager:
    """Gestor de conexiones WebSocket para updates en tiempo real"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket conectado para sesión: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket desconectado para sesión: {session_id}")
    
    async def send_progress(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error enviando mensaje WebSocket: {e}")
                self.disconnect(session_id)

manager = WebSocketManager()

# Crear directorios necesarios
def setup_directories():
    """Configura directorios necesarios para la aplicación"""
    directories = [
        "uploads/conciliator",
        "temp/conciliator", 
        "data/conciliator/output",
        "data/conciliator/processed"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

setup_directories()

# Endpoints del módulo conciliador

@router.get("/clients", response_model=List[ClientInfo])
async def get_clients():
    """Obtiene información de todos los clientes soportados"""
    try:
        supported_clients = get_supported_clients()
        clients_info = []
        
        for client_id in supported_clients:
            try:
                client_info = ProcessorFactory.get_client_info(client_id)
                
                try:
                    ProcessorFactory.validate_client_config(client_id)
                    status = "✅ Funcional"
                except:
                    status = "🔧 En configuración"
                
                tolerances = {"percentage": 5.0, "absolute": 50.0}
                if client_id == "KIOSKO":
                    tolerances = {"percentage": 3.0, "absolute": 25.0}
                
                clients_info.append(ClientInfo(
                    id=client_id,
                    name=client_info.get('display_name', client_id),
                    description=client_info.get('description', f'Procesador {client_id}'),
                    status=status,
                    tolerances=tolerances,
                    capabilities=client_info.get('capabilities', [])
                ))
                
            except Exception as e:
                logger.warning(f"Error obteniendo info de {client_id}: {e}")
                clients_info.append(ClientInfo(
                    id=client_id,
                    name=client_id,
                    description=f'Conciliación para {client_id}',
                    status="⚠️ Verificar configuración",
                    tolerances={"percentage": 5.0, "absolute": 50.0},
                    capabilities=[]
                ))
        
        return clients_info
        
    except Exception as e:
        logger.error(f"Error obteniendo clientes: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo clientes: {str(e)}")

@router.post("/session")
async def create_session():
    """Crea una nueva sesión de procesamiento"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "created_at": datetime.now(),
        "files": {},
        "status": "created",
        "results": None
    }
    
    logger.info(f"Nueva sesión creada: {session_id}")
    return {"session_id": session_id}

@router.post("/upload/{session_id}")
async def upload_file(
    session_id: str,
    file_type: str,  # 'source' o 'looker'
    file: UploadFile = File(...)
):
    """Sube un archivo para procesamiento"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    if file_type not in ['source', 'looker']:
        raise HTTPException(status_code=400, detail="Tipo de archivo debe ser 'source' o 'looker'")
    
    allowed_extensions = ['.xlsx', '.xls', '.csv']
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Extensión no permitida. Permitidas: {', '.join(allowed_extensions)}"
        )
    
    try:
        session_upload_dir = Path("uploads/conciliator") / session_id
        session_upload_dir.mkdir(exist_ok=True)
        
        file_path = session_upload_dir / f"{file_type}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        sessions[session_id]["files"][file_type] = {
            "filename": file.filename,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "uploaded_at": datetime.now().isoformat()
        }
        
        logger.info(f"Archivo {file_type} subido para sesión {session_id}: {file.filename}")
        
        return {
            "message": "Archivo subido exitosamente",
            "filename": file.filename,
            "size": file_path.stat().st_size,
            "type": file_type
        }
        
    except Exception as e:
        logger.error(f"Error subiendo archivo: {e}")
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {str(e)}")

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket para updates en tiempo real del procesamiento"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(session_id)

@router.post("/process/{session_id}")
async def process_files(
    session_id: str,
    background_tasks: BackgroundTasks,
    request: ProcessingRequest
):
    """Inicia el procesamiento de conciliación en background"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = sessions[session_id]
    
    if 'source' not in session['files'] or 'looker' not in session['files']:
        raise HTTPException(status_code=400, detail="Faltan archivos por subir")
    
    if request.client_type not in get_supported_clients():
        raise HTTPException(status_code=400, detail=f"Cliente {request.client_type} no soportado")
    
    sessions[session_id]["status"] = "processing"
    sessions[session_id]["client_type"] = request.client_type
    sessions[session_id]["date_range"] = request.date_range.dict()
    
    background_tasks.add_task(
        process_reconciliation_background,
        session_id,
        request.client_type
    )
    
    return {"message": "Procesamiento iniciado", "session_id": session_id}

async def process_reconciliation_background(session_id: str, client_type: str):
    """Procesa la conciliación en background con updates en tiempo real"""
    
    start_time = datetime.now()
    
    try:
        session = sessions[session_id]
        source_file = session['files']['source']['path']
        looker_file = session['files']['looker']['path']
        
        await manager.send_progress(session_id, {
            "type": "progress",
            "step": "init",
            "progress": 10,
            "message": f"Iniciando procesamiento {client_type}",
            "timestamp": datetime.now().isoformat()
        })
        
        # Crear procesador específico
        processor = ProcessorFactory.create_processor(client_type)
        
        await manager.send_progress(session_id, {
            "type": "progress", 
            "step": "processing",
            "progress": 40,
            "message": "Procesando archivos...",
            "timestamp": datetime.now().isoformat()
        })
        
        source_data, looker_data = processor.process_files(source_file, looker_file)
        
        if len(source_data) == 0 or len(looker_data) == 0:
            raise ValueError("No se pudieron procesar los archivos o están vacíos")
        
        # Realizar conciliación
        await manager.send_progress(session_id, {
            "type": "progress",
            "step": "reconciliation", 
            "progress": 60,
            "message": "Realizando conciliación...",
            "timestamp": datetime.now().isoformat()
        })
        
        reconciler = Reconciler(client_type)
        reconciliation_results = reconciler.reconcile(source_data, looker_data)
        summary_stats = reconciler.get_summary_stats()
        
        # Generar reportes
        await manager.send_progress(session_id, {
            "type": "progress",
            "step": "reports",
            "progress": 80, 
            "message": "Generando reportes...",
            "timestamp": datetime.now().isoformat()
        })
        
        report_generator = ReportGenerator(client_type)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        excel_report = report_generator.generate_complete_report(
            reconciliation_results, summary_stats, f"{client_type.lower()}_{session_id}_{timestamp}"
        )
        
        csv_reports = report_generator.generate_csv_reports(
            reconciliation_results, f"{client_type.lower()}_{session_id}_{timestamp}"
        )
        
        # Preparar datos para el frontend
        frontend_records = []
        for _, row in reconciliation_results.iterrows():
            try:
                client_value = 0
                looker_value = 0

                client_value_fields = [
                    f'valor_{client_type.lower()}_clean',
                    'valor_source_clean',
                    'valor_oxxo_clean'
                ]

                for field in client_value_fields:
                    if field in row and pd.notna(row[field]):
                        client_value = float(row[field])
                        break

                looker_value_fields = ['valor_looker_clean', 'total_venta_looker']
                for field in looker_value_fields:
                    if field in row and pd.notna(row[field]):
                        looker_value = float(row[field])
                        break

                difference = client_value - looker_value

                category_mapping = {
                    'EXACT_MATCH': 'Conciliado',
                    'WITHIN_TOLERANCE': 'Tolerancia',
                    'MINOR_DIFFERENCE': 'Diferencia Menor',
                    'MAJOR_DIFFERENCE': 'Diferencia Mayor',
                    'MISSING_IN_LOOKER': 'No Registrado',
                    f'MISSING_IN_{client_type}': f'Faltante en {client_type}'
                }

                category = category_mapping.get(row.get('categoria', ''), 'Desconocido')

                raw_fecha = None
                if 'Submitted at' in row:
                    raw_fecha = row['Submitted at']
                elif 'Fecha' in row:
                    raw_fecha = row['Fecha']

                fecha_val = None
                if raw_fecha is not None and pd.notna(raw_fecha):
                    if isinstance(raw_fecha, (pd.Timestamp, datetime)):
                        fecha_val = raw_fecha.isoformat()
                    else:
                        fecha_val = str(raw_fecha)

                frontend_records.append(ReconciliationRecord(
                    id=str(row.get('id_matching', '')),
                    client_value=client_value,
                    looker_value=looker_value,
                    difference=difference,
                    status=row.get('categoria', 'UNKNOWN'),
                    category=category,
                    fecha=fecha_val,
                ))

            except Exception as e:
                logger.warning(f"Error procesando registro: {e}")
                continue
        
        # Crear resumen
        summary = ReconciliationSummary(
            total_records=summary_stats.get('total_records', 0),
            exact_matches=summary_stats.get('exact_matches', 0),
            within_tolerance=summary_stats.get('within_tolerance', 0),
            major_differences=summary_stats.get('major_differences', 0),
            missing_records=(
                summary_stats.get('missing_in_looker', 0) + 
                summary_stats.get(f'missing_in_{client_type.lower()}', 0)
            ),
            reconciliation_rate=summary_stats.get('reconciliation_rate', 0),
            total_client_amount=summary_stats.get(f'total_valor_{client_type.lower()}', 0),
            total_looker_amount=summary_stats.get('total_valor_looker', 0),
            total_difference=summary_stats.get('total_diferencia', 0)
        )
        
        # Crear resultado final
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = ProcessingResult(
            session_id=session_id,
            success=True,
            summary=summary,
            records=frontend_records,
            reports_generated=[excel_report] + list(csv_reports.values()),
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
        # Guardar resultado en sesión
        sessions[session_id]["status"] = "completed"
        sessions[session_id]["results"] = result.dict()
        
        # Guardar en historial
        output_payload = {
            "client_type": client_type,
            "date_range": sessions[session_id].get("date_range"),
            "created_at": datetime.utcnow().isoformat(),
            "result": result.dict()
        }
        with open(os.path.join(LOGS_DIR, f"{session_id}.json"), "w") as f:
            json.dump(output_payload, f)
        
        # Enviar resultado final vía WebSocket
        await manager.send_progress(session_id, {
            "type": "completed",
            "result": result.dict()
        })
        
        logger.info(f"Procesamiento completado para sesión {session_id} en {processing_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Error en procesamiento de sesión {session_id}: {e}")
        
        sessions[session_id]["status"] = "error"
        sessions[session_id]["error"] = str(e)
        
        await manager.send_progress(session_id, {
            "type": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        })

@router.get("/status/{session_id}")
async def get_session_status(session_id: str):
    """Obtiene el estado actual de una sesión"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "status": session["status"],
        "created_at": session["created_at"],
        "files_uploaded": list(session["files"].keys()),
        "results_available": session.get("results") is not None,
        "error": session.get("error")
    }

@router.get("/results/{session_id}")
async def get_results(session_id: str):
    """Obtiene los resultados de una sesión completada"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = sessions[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Procesamiento no completado")
    
    if "results" not in session:
        raise HTTPException(status_code=404, detail="Resultados no encontrados")
    
    return session["results"]

@router.get("/download/{session_id}/{report_type}")
async def download_report(session_id: str, report_type: str):
    """Descarga un reporte generado"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = sessions[session_id]
    
    if session["status"] != "completed" or "results" not in session:
        raise HTTPException(status_code=400, detail="Resultados no disponibles")
    
    try:
        if report_type in ['excel', 'xlsx']:
            file_extension = 'xlsx'
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif report_type in ['csv']:
            file_extension = 'csv'
            media_type = 'text/csv'
        else:
            raise HTTPException(status_code=400, detail="Tipo de reporte no soportado")
        
        reports = session["results"].get("reports_generated", [])
        target_file = None
        
        for report_path in reports:
            if report_path.endswith(f'.{file_extension}'):
                target_file = report_path
                break
        
        if not target_file or not Path(target_file).exists():
            raise HTTPException(status_code=404, detail="Reporte no encontrado")
        
        client_type = session.get("client_type", "conciliacion")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conciliacion_{client_type.lower()}_{timestamp}.{file_extension}"
        
        file_path = Path(target_file)
        
        with open(file_path, 'rb') as file:
            content = file.read()
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': media_type,
            'Content-Length': str(len(content)),
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        logger.info(f"Descarga iniciada: {filename} ({len(content)} bytes)")
        
        return Response(
            content=content,
            media_type=media_type,
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en descarga de reporte: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno en descarga: {str(e)}")

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Elimina una sesión y limpia archivos temporales"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    try:
        session_upload_dir = Path("uploads/conciliator") / session_id
        if session_upload_dir.exists():
            shutil.rmtree(session_upload_dir)
        
        del sessions[session_id]
        manager.disconnect(session_id)
        
        logger.info(f"Sesión {session_id} eliminada")
        return {"message": "Sesión eliminada exitosamente"}
        
    except Exception as e:
        logger.error(f"Error eliminando sesión {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error eliminando sesión: {str(e)}")

@router.get("/sessions")
async def list_sessions():
    """Lista sesiones previas guardadas en logs"""
    sessions_list = []
    pattern = os.path.join(LOGS_DIR, "*.json")
    for fp in glob.glob(pattern):
        sid = os.path.splitext(os.path.basename(fp))[0]
        try:
            with open(fp, "r") as f:
                data = json.load(f)
            sessions_list.append({
                "session_id": sid,
                "client_type": data.get("client_type"),
                "date_range": data.get("date_range"),
                "created_at": data.get("created_at")
            })
        except:
            continue
    return sessions_list

@router.get("/session/{session_id}/results")
async def get_session_results(session_id: str):
    """Obtiene resultados de sesión histórica"""
    filepath = os.path.join(LOGS_DIR, f"{session_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Session not found")
    with open(filepath, "r") as f:
        return json.load(f)