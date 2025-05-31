import asyncio
import os
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.exc import ProgrammingError
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de PostgreSQL
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Configuración de MongoDB
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "ml_db")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")

def init_postgres_database():
    """Inicializa la base de datos PostgreSQL si no existe"""
    try:
        # Conectar a 'postgres' para poder crear la nueva base de datos
        postgres_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/postgres"
        engine = create_engine(postgres_url)
        
        # Verificar si la base de datos existe
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_DB}'"))
            exists = result.scalar() is not None
            
            if not exists:
                # Si no existe, crearla (cerramos la conexión transaccional primero)
                conn.execute(text("COMMIT"))
                conn.execute(text(f"CREATE DATABASE {POSTGRES_DB}"))
                logger.info(f"Base de datos PostgreSQL '{POSTGRES_DB}' creada exitosamente")
            else:
                logger.info(f"La base de datos PostgreSQL '{POSTGRES_DB}' ya existe")
                
        return True
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos PostgreSQL: {str(e)}")
        return False

async def init_mongodb_database():
    """Inicializa la base de datos MongoDB si no existe"""
    try:
        # Obtener la configuración de MongoDB desde variables de entorno
        MONGO_URI = os.getenv("MONGO_URI")
        MONGO_DB = os.getenv("MONGO_DB", "loanData")
        
        # Conectar a MongoDB Atlas usando la URI completa
        client = AsyncIOMotorClient(MONGO_URI)
        
        # La base de datos se crea automáticamente al ser utilizada
        db = client[MONGO_DB]
        
        # Podemos crear una colección para asegurarnos de que la DB existe
        await db.system_info.insert_one({
            "initialization": "completed",
            "timestamp": asyncio.get_event_loop().time(),
            "source": "data_sync_service"
        })
        
        logger.info(f"Base de datos MongoDB '{MONGO_DB}' inicializada exitosamente en cluster Atlas")
        return True
    
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos MongoDB: {str(e)}")
        return False
async def main():
    """Función principal de inicialización"""
    logger.info("Iniciando proceso de inicialización de bases de datos...")
    
    # Inicializar PostgreSQL
    postgres_init = init_postgres_database()
    
    # Inicializar MongoDB
    mongodb_init = await init_mongodb_database()
    
    if postgres_init and mongodb_init:
        logger.info("Proceso de inicialización completado exitosamente")
    else:
        logger.error("Proceso de inicialización completado con errores")

if __name__ == "__main__":
    # Ejecutar inicialización
    asyncio.run(main())