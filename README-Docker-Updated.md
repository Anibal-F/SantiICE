# SantiICE-OCR - Configuración Docker

## 🐳 Contenedores Configurados

Este proyecto está configurado para ejecutarse en contenedores Docker separados:

- **Frontend**: React + Nginx (Puerto 80)
- **Backend**: FastAPI + Python (Puerto 8000)

## 🚀 Comandos Principales

### Construcción Inicial
```bash
# Construir y ejecutar por primera vez
./build-docker.sh
```

### Reconstrucción con Cambios
```bash
# Reconstruir completamente (recomendado después de cambios)
./rebuild-docker.sh
```

### Comandos Manuales
```bash
# Detener contenedores
docker-compose down

# Construir sin cache
docker-compose build --no-cache

# Iniciar servicios
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f backend
docker-compose logs -f frontend

# Ver estado de contenedores
docker-compose ps
```

## 🌐 Acceso a la Aplicación

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## 🔧 Configuración

### Variables de Entorno
- `.env.docker`: Variables para el backend en Docker
- `frontend/.env.production`: Variables para el frontend en producción

### Archivos de Configuración
- `docker-compose.yml`: Orquestación de servicios
- `Dockerfile.backend`: Imagen del backend
- `Dockerfile.frontend`: Imagen del frontend
- `nginx.conf`: Configuración del proxy reverso

## 📁 Volúmenes Persistentes

Los siguientes directorios se mantienen persistentes:
- `./uploads`: Archivos subidos
- `./logs`: Logs de la aplicación
- `./app/credentials`: Credenciales de servicios

## 🔍 Solución de Problemas

### Cambios no se Reflejan
```bash
# Reconstruir completamente
./rebuild-docker.sh
```

### Ver Logs Detallados
```bash
# Backend
docker-compose logs backend --tail=50

# Frontend
docker-compose logs frontend --tail=50
```

### Limpiar Todo
```bash
# Detener y limpiar
docker-compose down --remove-orphans
docker system prune -f
```

## 📦 Preparación para Producción

### Para AWS EC2:
1. Subir código a GitHub
2. Clonar en EC2
3. Instalar Docker y Docker Compose
4. Configurar variables de entorno
5. Ejecutar `./build-docker.sh`

### Configuración de Seguridad:
- Cambiar credenciales en `.env.docker`
- Configurar HTTPS con certificados SSL
- Configurar firewall para puertos 80 y 443

## 🔄 Flujo de Desarrollo

1. Hacer cambios en el código
2. Ejecutar `./rebuild-docker.sh`
3. Probar en http://localhost
4. Commit y push a GitHub
5. Deploy en EC2

## ⚠️ Notas Importantes

- El frontend usa proxy nginx para comunicarse con el backend
- Las credenciales de AWS deben estar configuradas en `.env.docker`
- Los archivos de credenciales JSON deben estar en el directorio raíz
- El sistema está optimizado para producción con cache y compresión