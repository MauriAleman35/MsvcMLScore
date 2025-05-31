from sqlalchemy import create_engine, MetaData, Table, select, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Crear engine para PostgreSQL (ERP)
pg_engine = create_engine(settings.postgres_url)
PgSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)
metadata = MetaData()

# Definir tablas ERP usando reflexión (inspección automática del esquema)
def get_pg_table():
    """Carga dinámicamente las tablas desde la base de datos ERP"""
    try:
        metadata.reflect(bind=pg_engine)
        return {
            'users': metadata.tables.get('user'),
            'loans': metadata.tables.get('loan'),
            'monthly_payments': metadata.tables.get('monthly_payment'),
            'solicitudes': metadata.tables.get('solicitude'),
            'offers': metadata.tables.get('offer')
        }
    except Exception as e:
        logger.error(f"Error al cargar tablas PostgreSQL: {str(e)}")
        return {}

def pg_session_local():
    """Crea y devuelve una sesión PostgreSQL"""
    session = PgSessionLocal()
    try:
        yield session
    finally:
        session.close()