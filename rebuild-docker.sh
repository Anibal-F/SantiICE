#!/bin/bash

echo "🔄 Reconstruyendo contenedores Docker para SantiICE..."

# Detener y eliminar contenedores existentes
echo "🛑 Deteniendo y eliminando contenedores existentes..."
docker-compose down --remove-orphans

# Eliminar imágenes existentes para forzar reconstrucción
echo "🗑️ Eliminando imágenes existentes..."
docker rmi $(docker images | grep santiice | awk '{print $3}') 2>/dev/null || true

# Limpiar cache de Docker
echo "🧹 Limpiando cache de Docker..."
docker system prune -f

# Construir imágenes desde cero
echo "🔨 Construyendo imágenes desde cero..."
docker-compose build --no-cache --pull

# Iniciar servicios
echo "🚀 Iniciando servicios..."
docker-compose up -d

# Esperar un momento para que los servicios se inicien
echo "⏳ Esperando que los servicios se inicien..."
sleep 10

# Mostrar estado
echo "📊 Estado de los contenedores:"
docker-compose ps

# Mostrar logs recientes
echo "📋 Logs recientes del backend:"
docker-compose logs backend --tail=5

echo "📋 Logs recientes del frontend:"
docker-compose logs frontend --tail=5

echo "✅ ¡Reconstrucción completada!"
echo "🌐 Frontend: http://localhost"
echo "🔧 Backend: http://localhost:8000"
echo ""
echo "💡 Para ver logs en tiempo real:"
echo "   docker-compose logs -f backend"
echo "   docker-compose logs -f frontend"