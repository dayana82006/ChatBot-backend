#!/usr/bin/env python3
"""
Script para actualizar la base de datos con los cambios necesarios
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import add_metadata_column_to_pedido_detalles, execute_schema
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database():
    """Ejecuta todas las actualizaciones necesarias en la base de datos"""
    try:
        logger.info("🔄 Actualizando base de datos...")
        
        # Ejecutar schema principal
        execute_schema()
        
        # Agregar columna metadata si es necesario
        add_metadata_column_to_pedido_detalles()
        
        logger.info("✅ Base de datos actualizada correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error actualizando base de datos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_database()