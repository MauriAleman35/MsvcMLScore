import logging
import asyncio
import decimal
import datetime
from bson import Decimal128
from app.config.postgres_conection import get_table_data, init_postgres_models
from app.config.database import get_mongo_db

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tablas a sincronizar
TABLES_TO_SYNC = ["user", "solicitude", "offer", "loan", "monthly_payment"]

def convert_postgres_record(record):
    """Convierte tipos de PostgreSQL a tipos compatibles con MongoDB"""
    if not record:
        return record
        
    result = {}
    for key, value in record.items():
        # Convertir Decimal a float
        if isinstance(value, decimal.Decimal):
            result[key] = float(value)
        
        # Convertir tipos de fecha/hora a ISO format
        elif isinstance(value, datetime.datetime):
            result[key] = value.isoformat()
        elif isinstance(value, datetime.date):
            result[key] = value.isoformat()
        
        # Manejar enumeraciones y tipos personalizados
        elif hasattr(value, 'value'):  # Para tipos Enum
            result[key] = str(value.value)
        
        # Para cualquier otro tipo, usarlo tal cual
        else:
            result[key] = value
            
    return result

async def sync_table_to_mongodb(table_name, mongo_db=None):
    """Sincroniza una tabla específica de PostgreSQL a MongoDB"""
    try:
        logger.info(f"Sincronizando tabla {table_name}...")
        
        # Si no se proporcionó un cliente MongoDB, obtenerlo
        if mongo_db is None:
            mongo_db = get_mongo_db()
        
        # Obtener datos de PostgreSQL
        postgres_records = get_table_data(table_name)
        if not postgres_records or len(postgres_records) == 0:
            logger.warning(f"No hay datos para sincronizar en la tabla {table_name}")
            return True
        
        # Convertir registros para hacerlos compatibles con MongoDB
        converted_records = [convert_postgres_record(record) for record in postgres_records]
        
        # Borrar documentos existentes en MongoDB (opcional)
        await mongo_db[table_name].delete_many({})
        
        # Insertar nuevos documentos
        await mongo_db[table_name].insert_many(converted_records)
        
        logger.info(f"Tabla {table_name} sincronizada exitosamente. {len(converted_records)} registros insertados.")
        return True
    
    except Exception as e:
        logger.error(f"Error al sincronizar la tabla {table_name}: {str(e)}")
        return False