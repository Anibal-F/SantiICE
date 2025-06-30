# SantiICE OCR System

Sistema de procesamiento OCR para tickets de OXXO y KIOSKO con integración a Google Sheets.

## 🚀 Características

- **OCR Automático**: AWS Textract para extracción de texto
- **Detección Inteligente**: Identifica automáticamente tipo de ticket (OXXO/KIOSKO)
- **Google Sheets**: Integración directa con hojas de cálculo
- **Interfaz Web**: Frontend React moderno
- **API REST**: Backend FastAPI robusto
- **Docker**: Containerización completa

## 🛠️ Tecnologías

- **Backend**: Python, FastAPI, AWS Textract, AWS Bedrock
- **Frontend**: React, Tailwind CSS
- **Base de datos**: Google Sheets
- **Infraestructura**: Docker, AWS EC2
- **OCR**: AWS Textract (producción), Tesseract (fallback)

## 📦 Deployment en AWS EC2

### Prerrequisitos
- Instancia EC2 Ubuntu 22.04
- Credenciales AWS configuradas
- Archivo service_account.json para Google Sheets

### Deployment automático
```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/SantiICE-OCR.git
cd SantiICE-OCR

# Ejecutar script de deployment
chmod +x deploy.sh
./deploy.sh
```

### Configuración manual
```bash
# Instalar dependencias
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Construir y ejecutar
docker build -f Dockerfile.minimal -t santiice-ocr:latest .
docker run -d -p 80:8000 --name santiice-app santiice-ocr:latest
```

## 🔧 Configuración

### Variables de entorno
```bash
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### Credenciales Google Sheets
- Colocar `service_account.json` en la raíz del proyecto
- Configurar permisos en Google Sheets

## 📊 Uso

1. **Acceder**: http://tu-servidor-ec2
2. **Login**: admin/admin123 o user/user123
3. **Subir tickets**: Drag & drop o selección manual
4. **Revisión**: Validar datos extraídos
5. **Confirmación**: Envío automático a Google Sheets

## 🏗️ Desarrollo local

```bash
# Backend
cd app
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start
```

## 📝 API Endpoints

- `POST /upload` - Subir imagen de ticket
- `POST /process-tickets` - Procesar múltiples tickets
- `POST /confirm-tickets` - Confirmar y enviar a Sheets
- `GET /api/conciliator/clients` - Clientes de conciliación

## 🔒 Seguridad

- Autenticación básica implementada
- Permisos por módulo (tickets, conciliator, config)
- Credenciales no incluidas en repositorio
- HTTPS recomendado para producción

## 📞 Soporte

Sistema desarrollado para SantiICE por AF Consulting.