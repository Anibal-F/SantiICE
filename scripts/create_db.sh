#!/bin/bash

# Crear la base de datos PostgreSQL para SantiICE OCR
echo "Creando base de datos PostgreSQL para SantiICE OCR..."

# Verificar si PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL no está instalado. Por favor, instálalo primero."
    exit 1
fi

# Solicitar contraseña de PostgreSQL
echo -n "Ingresa la contraseña para el usuario postgres: "
read -s PGPASSWORD
echo ""

# Exportar la contraseña para psql
export PGPASSWORD

# Crear la base de datos
psql -U postgres -c "CREATE DATABASE santiice;" || {
    echo "Error al crear la base de datos. Verifica que PostgreSQL esté en ejecución y que la contraseña sea correcta."
    unset PGPASSWORD
    exit 1
}

# Limpiar la variable de entorno por seguridad
unset PGPASSWORD

echo "Base de datos 'santiice' creada correctamente."

# Actualizar el archivo .env con la contraseña
echo "Actualizando archivo .env con la configuración de la base de datos..."
sed -i.bak "s/DATABASE_URL=postgresql:\/\/postgres:postgres@localhost\/santiice/DATABASE_URL=postgresql:\/\/postgres:$PGPASSWORD@localhost\/santiice/g" ../.env

echo "Configuración completada. Ahora puedes ejecutar la aplicación con 'uvicorn app.main:app --reload'"