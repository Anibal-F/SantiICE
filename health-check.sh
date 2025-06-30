#!/bin/bash

echo "🔍 Verificando estado del sistema SantiICE-OCR..."
echo "=================================================="

# Verificar contenedores
echo "📦 Estado de contenedores:"
docker-compose ps

echo ""
echo "🌐 Verificando conectividad:"

# Verificar frontend
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
    echo "✅ Frontend: OK (http://localhost)"
else
    echo "❌ Frontend: ERROR"
fi

# Verificar backend
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs | grep -q "200"; then
    echo "✅ Backend: OK (http://localhost:8000)"
else
    echo "❌ Backend: ERROR"
fi

# Verificar proxy
if curl -s -o /dev/null -w "%{http_code}" http://localhost/auth/me | grep -q -E "(200|401)"; then
    echo "✅ Proxy Nginx: OK"
else
    echo "❌ Proxy Nginx: ERROR"
fi

echo ""
echo "💾 Uso de recursos:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "📊 Espacio en disco:"
df -h | grep -E "(Filesystem|/dev/)"

echo ""
echo "🔧 Versiones:"
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker-compose --version)"

echo ""
echo "📋 Logs recientes (últimas 5 líneas):"
echo "--- Backend ---"
docker-compose logs backend --tail=5 | tail -5

echo "--- Frontend ---"
docker-compose logs frontend --tail=5 | tail -5

echo ""
echo "✅ Verificación completada!"
echo "🌐 Accede a: http://localhost"