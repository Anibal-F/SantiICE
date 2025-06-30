# 🐳 Containerización de SantiICE OCR

## Archivos creados para Docker:

### 1. **Dockerfile** - Imagen principal
- Multi-stage build (Node.js + Python)
- Optimizado para producción
- Incluye frontend construido

### 2. **docker-compose.yml** - Para desarrollo local
- Puerto 8000 expuesto
- Volúmenes para credenciales y uploads
- Healthcheck incluido

### 3. **requirements.txt** - Dependencias Python
- FastAPI, Uvicorn
- Google Sheets, Pandas
- Autenticación y OCR

### 4. **.dockerignore** - Archivos excluidos
- node_modules, __pycache__
- Archivos de desarrollo
- Logs y temporales

## 🚀 Comandos para usar:

### Construir imagen:
```bash
docker build -t santiice-ocr:latest .
```

### Ejecutar con docker-compose:
```bash
docker-compose up -d
```

### Ver logs:
```bash
docker-compose logs -f
```

### Detener:
```bash
docker-compose down
```

## 📋 Próximos pasos:
1. ✅ Containerización completada
2. ⏳ Instalar Docker en tu máquina
3. ⏳ Probar localmente
4. ⏳ Configurar EC2 en AWS
5. ⏳ Setup GitHub Actions

## 🔧 Instalación de Docker:
- **macOS**: Docker Desktop desde docker.com
- **Windows**: Docker Desktop desde docker.com
- **Linux**: `sudo apt install docker.io docker-compose`