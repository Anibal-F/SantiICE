#!/bin/bash

# Crear la base de datos PostgreSQL para SantiICE OCR
# Uso: ./create_db_with_password.sh <contraseña>

# Verificar si se proporcionó la contraseña
if [ -z "$1" ]; then
    echo "Error: Debes proporcionar la contraseña de PostgreSQL."
    echo "Uso: $0 <contraseña>"
    exit 1
fi

PGPASSWORD=$1

echo "Creando base de datos PostgreSQL para SantiICE OCR..."

# Verificar si PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL no está instalado. Por favor, instálalo primero."
    exit 1
fi

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
sed -i.bak "s/DATABASE_URL=postgresql:\/\/postgres:postgres@localhost\/santiice/DATABASE_URL=postgresql:\/\/postgres:$1@localhost\/santiice/g" ../.env

echo "Configuración completada. Ahora puedes ejecutar la aplicación con 'uvicorn app.main:app --reload'"