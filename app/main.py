import logging
import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter
import uvicorn
from dotenv import load_dotenv

# Importaciones para la sincronización
from app.config.database import init_mongodb, get_mongo_db
from app.config.postgres_conection import init_postgres_models
from app.sync.data_sync import sync_table_to_mongodb
from app.config.settings import settings

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Inicializar aplicación FastAPI
app = FastAPI(
    title="Microservicio ML de Scoring Crediticio",
    description="API para cálculo de scores crediticios basado en IA",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción especificar orígenes exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas básicas
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Microservicio ML de Scoring Crediticio",
        "version": "1.0.0",
        "environment": settings.API_ENV,
    }

# Endpoint para forzar la sincronización
@app.post("/sync", tags=["Sync"])
async def trigger_sync():
    try:
        logger.info("Iniciando sincronización manual de datos")
        await sync_all_data()
        return {"status": "success", "message": "Sincronización completada"}
    except Exception as e:
        logger.error(f"Error durante la sincronización: {str(e)}")
        return {"status": "error", "message": str(e)}

# Estado de la sincronización
@app.get("/sync/status", tags=["Sync"])
async def sync_status():
    try:
        # Obtener información de sincronización de MongoDB
        mongo_db = get_mongo_db()  # Usar get_mongo_db en lugar de initialize_mongodb
        status_doc = await mongo_db.system_info.find_one({"initialization": "completed"})
        if status_doc:
            return {
                "status": "success", 
                "last_sync": status_doc.get("last_sync", "Never"),
                "synced_tables": status_doc.get("synced_tables", [])
            }
        return {"status": "pending", "message": "No se ha realizado ninguna sincronización"}
    except Exception as e:
        logger.error(f"Error al verificar estado de sincronización: {str(e)}")
        return {"status": "error", "message": str(e)}

# Función de sincronización
async def sync_all_data():
    """Realiza la sincronización de todas las tablas configuradas"""
    try:
        logger.info("Iniciando sincronización de datos...")
        
        # Inicializar modelos y conexiones
        init_postgres_models()
        mongo_db = get_mongo_db()
        
        # Lista de tablas a sincronizar
        tables_to_sync = ["user", "solicitude", "offer", "loan", "monthly_payment"]
        
        # Sincronizar cada tabla
        synced_tables = []
        for table_name in tables_to_sync:
            logger.info(f"Sincronizando tabla {table_name}...")
            if await sync_table_to_mongodb(table_name, mongo_db):
                synced_tables.append(table_name)
                logger.info(f"Tabla {table_name} sincronizada exitosamente")
            else:
                logger.warning(f"Falló la sincronización de la tabla {table_name}")
        
        # Actualizar el estado de sincronización
        await mongo_db.system_info.update_one(
            {"initialization": "completed"},
            {
                "$set": {
                    "synced_with_postgres": True,
                    "last_sync": asyncio.get_event_loop().time(),
                    "synced_tables": synced_tables
                }
            },
            upsert=True
        )
        
        logger.info(f"Sincronización completada. {len(synced_tables)}/{len(tables_to_sync)} tablas sincronizadas.")
        return True
    
    except Exception as e:
        logger.error(f"Error en la sincronización: {str(e)}")
        return False

# Evento de inicio de la aplicación para la sincronización inicial
@app.on_event("startup")
async def startup_db_clients():
    # Inicializar MongoDB y PostgreSQL
    try:
        # Inicializar PostgreSQL
        init_postgres_models()
        
        # Inicializar MongoDB (con await)
        await init_mongodb()
        
        # Ejecutar sincronización inicial si está habilitada
        if os.getenv("ENABLE_INITIAL_SYNC", "false").lower() == "true":
            logger.info("Sincronización inicial habilitada, iniciando proceso...")
            # Ejecutar sincronización como tarea asíncrona para no bloquear el inicio
            asyncio.create_task(sync_all_data())
        else:
            logger.info("Sincronización inicial deshabilitada")
    except Exception as e:
        logger.error(f"Error al inicializar bases de datos: {str(e)}")

# Implementación GraphQL básica
@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

# Agregar GraphQL
app.include_router(graphql_app, prefix="/graphql")

# Iniciar aplicación con Uvicorn si se ejecuta directamente
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # Usa la ruta correcta para tu aplicación
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True if settings.API_ENV != "production" else False,
    )