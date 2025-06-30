#!/bin/bash

echo "🐳 Construyendo contenedores Docker para SantiICE..."

# Detener contenedores existentes
echo "📦 Deteniendo contenedores existentes..."
docker-compose down

# Construir imágenes
echo "🔨 Construyendo imágenes..."
docker-compose build --no-cache

# Iniciar servicios
echo "🚀 Iniciando servicios..."
docker-compose up -d

# Mostrar estado
echo "📊 Estado de los contenedores:"
docker-compose ps

echo "✅ ¡Aplicación lista!"
echo "🌐 Frontend: http://localhost"
echo "🔧 Backend: http://localhost:8000"