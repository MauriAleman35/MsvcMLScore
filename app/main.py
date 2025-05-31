import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.orm import Session
import uvicorn
import os

from app.config.settings import settings
from app.db.session import get_db, engine, Base
from app.db.models import User, Loan, MonthlyPayment, Solicitude, Offer

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Crear tablas en la base de datos (en producción usar Alembic para migraciones)
Base.metadata.create_all(bind=engine)

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

# Verificar conexión a la base de datos
@app.get("/health/db", tags=["Health"])
async def check_db_health(db: Session = Depends(get_db)):
    try:
        # Intentar ejecutar una consulta simple
        db.execute("SELECT 1")
        return {"status": "ok", "message": "Database connection is healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {"status": "error", "message": str(e)}

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