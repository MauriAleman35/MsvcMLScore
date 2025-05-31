import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter
import uvicorn
from app.sync.initial_sync import sync_all_data
from app.config.settings import settings
import asyncio

from app.config.database import init_mongodb
# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)



# Inicializar aplicación FastAPI
app = FastAPI(
    title="Microservicio ML de Scoring Crediticio",
    description="API para cálculo de scores crediticios basado en IA",
    version="1.0.0",
)
@app.on_event("startup")
async def startup_db_clients():
    # Inicializar MongoDB con Beanie (código que ya tienes)
    await init_mongodb()
    
    # Ejecutar sincronización inicial si está habilitada
    if settings.ENABLE_INITIAL_SYNC:
        logger.info("Iniciando sincronización inicial de datos")
        asyncio.create_task(sync_all_data())
# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción especificar orígenes exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # Verificar conexión a la base de datos
# @app.get("/health/db", tags=["Health"])
# async def check_db_health(db: Session = Depends(get_db)):
#     try:
#         # Intentar ejecutar una consulta simple
#         db.execute("SELECT 1")
#         return {"status": "ok", "message": "Database connection is healthy"}
#     except Exception as e:
#         logger.error(f"Database health check failed: {str(e)}")
#         return {"status": "error", "message": str(e)}

# Rutas básicas
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Microservicio ML de Scoring Crediticio",
        "version": "1.0.0",
        "environment": settings.API_ENV,
    }

# TODO: Implementar GraphQL Schema
# Por ahora dejamos un schema mínimo de ejemplo
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
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True if settings.API_ENV != "production" else False,
    )