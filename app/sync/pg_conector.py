import logging
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
# Configurar logging
logger = logging.getLogger(__name__)

# Crear motor de conexión a PostgreSQL
try:
    pg_engine = create_engine(
        settings.postgres_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"connect_timeout": 10}
    )
    logger.info(f"Conexión a PostgreSQL establecida: {settings.POSTGRES_HOST}")
except Exception as e:
    logger.error(f"Error al conectar con PostgreSQL: {str(e)}")
    pg_engine = None

# Crear base para modelos declarativos
PgBase = declarative_base()

# Crear fábrica de sesiones (IMPORTANTE: Usa lowercase como función)
PgSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)
pg_session_local = PgSessionLocal  # Alias lowercase para compatibilidad
# Definir tablas ERP usando reflexión (inspección automática del esquema)
_pg_tables_cache = {}
def get_pg_table(table_name=None):
    """Obtiene una tabla específica de PostgreSQL o todas las tablas"""
    try:
        # Si ya tenemos las tablas en caché, retornarlas
        global _pg_tables_cache
        if _pg_tables_cache:
            if table_name:
                return {table_name: _pg_tables_cache.get(table_name)}
            return _pg_tables_cache
        
        # Si no hay conexión, retornar vacío
        if not pg_engine:
            logger.warning("No hay conexión a PostgreSQL disponible")
            return {} if table_name is None else None
        
        # Crear un objeto MetaData y reflejar el esquema
        metadata = MetaData()
        metadata.reflect(bind=pg_engine)
        
        # Construir diccionario de tablas
        tables = {table.name: table for table in metadata.tables.values()}
        
        # Guardar en caché
        _pg_tables_cache = tables
        
        logger.info(f"Se han cargado {len(tables)} tablas de PostgreSQL: {', '.join(tables.keys())}")
        
        if table_name:
            return {table_name: tables.get(table_name)}
        return tables
            
    except Exception as e:
        logger.error(f"Error al cargar tablas de PostgreSQL: {str(e)}")
        return {} if table_name is None else None

def pg_session_local():
    """Crea y devuelve una sesión PostgreSQL"""
    session = PgSessionLocal()
    try:
        yield session
    finally:
        session.close()

# Añade una función para debugging
def print_tables_info():
    """Imprime información sobre las tablas disponibles"""
    tables = get_pg_table()
    logger.info(f"Tablas disponibles: {list(tables.keys())}")
    
    for table_name, table_obj in tables.items():
        column_names = [c.name for c in table_obj.columns]
        logger.info(f"Tabla: {table_name}, Columnas: {column_names}")