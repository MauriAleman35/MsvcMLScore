import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Variable global para guardar la conexión de MongoDB
_mongo_client = None
_mongo_db = None

async def init_mongodb():
    """Inicializa la conexión a MongoDB de forma asíncrona"""
    global _mongo_client, _mongo_db
    
    try:
        # Obtener configuración
        MONGO_URI = os.getenv("MONGO_URI")
        MONGO_DB = os.getenv("MONGO_DB", "loanData")
        
        # Crear cliente
        _mongo_client = AsyncIOMotorClient(
            MONGO_URI,
            maxPoolSize=100,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            retryWrites=True,
            w="majority"
        )
        _mongo_db = _mongo_client[MONGO_DB]
        
        # Verificar conexión
        await _mongo_client.admin.command('ping')
        logger.info(f"Conexión a MongoDB inicializada exitosamente para la base de datos '{MONGO_DB}'")
        
        return _mongo_db
    except Exception as e:
        logger.error(f"Error al inicializar MongoDB: {str(e)}")
        raise

def get_mongo_db():
    """Devuelve la base de datos MongoDB inicializada"""
    global _mongo_db
    if _mongo_db is None:
        raise RuntimeError("MongoDB no ha sido inicializado. Llama a init_mongodb() primero.")
    return _mongo_db