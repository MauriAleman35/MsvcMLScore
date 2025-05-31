import logging
from sqlalchemy import create_engine, text
from app.config.settings import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_postgres_connection():
    """Prueba la conexión a PostgreSQL con una consulta mínima"""
    try:
        # Crear engine
        engine = create_engine(
            settings.postgres_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
        
        # Crear conexión
        with engine.connect() as connection:
            # Ejecutar consulta simple
            result = connection.execute(text("SELECT 1 AS test"))
            row = result.fetchone()
            logger.info(f"Test de conexión exitoso: {row.test}")
            
            # Verificar tablas
            tables_result = connection.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public'"
            ))
            tables = [row[0] for row in tables_result]
            logger.info(f"Tablas en la base de datos: {tables}")
            
            # Verificar columnas de la tabla user
            if 'user' in tables:
                cols_result = connection.execute(text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='user'"
                ))
                columns = [(row[0], row[1]) for row in cols_result]
                logger.info(f"Columnas de la tabla 'user': {columns}")
        
        return True
    except Exception as e:
        logger.error(f"Error al conectar con PostgreSQL: {str(e)}")
        return False

if __name__ == "__main__":
    test_postgres_connection()