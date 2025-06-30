#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos PostgreSQL.
"""
import sys
import os
import sqlalchemy
from dotenv import load_dotenv

# Agregar el directorio raíz al path para poder importar los módulos de la aplicación
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Cargar variables de entorno
load_dotenv()

# Obtener la URL de conexión a la base de datos
from app.database import DATABASE_URL

def test_connection():
    """Prueba la conexión a la base de datos."""
    print(f"Probando conexión a la base de datos...")
    print(f"URL de conexión: {DATABASE_URL}")
    
    try:
        # Crear un motor de SQLAlchemy
        engine = sqlalchemy.create_engine(DATABASE_URL)
        
        # Probar la conexión
        with engine.connect() as connection:
            result = connection.execute(sqlalchemy.text("SELECT 1"))
            for row in result:
                print(f"Conexión exitosa: {row[0]}")
        
        print("✅ Conexión a la base de datos establecida correctamente.")
        return True
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)