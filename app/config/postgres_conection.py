from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración desde variables de entorno
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Construir la URL de conexión
SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Crear el motor de SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

# Lista de tablas que queremos sincronizar
TABLES_TO_SYNC = ["user", "solicitude", "offer", "loan", "monthly_payment"]

# Crear un objeto Base automáticamente mapeado
Base = automap_base()

def init_postgres_models():
    """Inicializa los modelos reflejados de PostgreSQL"""
    # Reflejar solo las tablas específicas que queremos
    metadata.reflect(engine, only=TABLES_TO_SYNC)
    Base.prepare(engine, reflect=True)
    return {table_name: getattr(Base.classes, table_name) for table_name in TABLES_TO_SYNC if hasattr(Base.classes, table_name)}

def get_postgres_session():
    """Proporciona una sesión de base de datos PostgreSQL"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def get_table_data(table_name):
    """Obtiene todos los registros de una tabla específica"""
    try:
        # Iniciar sesión
        with SessionLocal() as session:
            # Consultar la tabla
            if table_name not in metadata.tables:
                metadata.reflect(bind=engine, only=[table_name])
            
            if table_name not in metadata.tables:
                logger.warning(f"La tabla {table_name} no existe en la base de datos")
                return []
                
            table = metadata.tables[table_name]
            result = session.query(table).all()
            
            # Convertir a diccionarios
            records = [dict(row._mapping) for row in result]
            return records
            
    except Exception as e:
        logger.error(f"Error al obtener datos de la tabla {table_name}: {str(e)}")
        return []
def get_table_data(table_name):
    """Obtiene todos los registros de una tabla específica"""
    if table_name not in TABLES_TO_SYNC:
        raise ValueError(f"La tabla {table_name} no está en la lista de tablas a sincronizar")
    
    with SessionLocal() as session:
        # Usar Table directamente desde metadata
        table = metadata.tables[table_name]
        result = session.query(table).all()
        # Convertir a diccionarios
        records = [dict(row._mapping) for row in result]
        return records