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

# Importaciones para el modelo ML
from app.ml.services.score_service import ScorePredictionService
from app.ml.schemas.score_schemas import ScorePredictionInput, ScorePredictionResult, InputFeatures

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Inicializar servicio de predicción
score_service = ScorePredictionService()

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
        mongo_db = get_mongo_db()
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

# Implementación GraphQL con queries y mutations
@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"
    
    @strawberry.field
    def version(self) -> str:
        return "1.0.0"

@strawberry.type
class Mutation:
    @strawberry.mutation
    def predict_score(self, input_data: ScorePredictionInput) -> ScorePredictionResult:
        """Predice el score crediticio basado en los datos de entrada"""
        try:
            # Convertir input a diccionario
            input_dict = {
                'adress_verified': input_data.adress_verified,
                'identity_verified': input_data.identity_verified,
                'loan_count': input_data.loan_count,
                'late_payment_count': input_data.late_payment_count,
                'avg_days_late': input_data.avg_days_late,
                'total_penalty': input_data.total_penalty,
                'payment_completion_ratio': input_data.payment_completion_ratio,
                'has_no_late_payments': input_data.has_no_late_payments,
                'has_penalty': input_data.has_penalty,
                'loans_al_dia_ratio': input_data.loans_al_dia_ratio,
                'days_late_per_loan': input_data.days_late_per_loan
            }
            
            # Log para debug
            logger.info(f"Prediciendo score con datos: {input_dict}")
            
            # Llamar al servicio de predicción
            result = score_service.predict_score(input_dict)
            
            # Log del resultado
            logger.info(f"Resultado de predicción: {result}")
            
            # Verificar si hay score en el resultado
            if "score" not in result or result["score"] is None:
                logger.warning("El modelo no retornó un score. Usando valor por defecto.")
                result["score"] = 50.0
            
            # Crear objeto InputFeatures desde el diccionario
            input_features = None
            if "input_features" in result and result["input_features"]:
                input_features = InputFeatures(
                    adress_verified=result["input_features"].get("adress_verified", 0),
                    identity_verified=result["input_features"].get("identity_verified", 0),
                    loan_count=result["input_features"].get("loan_count", 0),
                    late_payment_count=result["input_features"].get("late_payment_count", 0),
                    avg_days_late=result["input_features"].get("avg_days_late", 0.0),
                    total_penalty=result["input_features"].get("total_penalty", 0.0),
                    payment_completion_ratio=result["input_features"].get("payment_completion_ratio", 0.0),
                    has_no_late_payments=result["input_features"].get("has_no_late_payments", 0),
                    has_penalty=result["input_features"].get("has_penalty", 0),
                    loans_al_dia_ratio=result["input_features"].get("loans_al_dia_ratio", 0.0),
                    days_late_per_loan=result["input_features"].get("days_late_per_loan", 0.0)
                )
            
            # Devolver resultado enriquecido con categoría y explicación
            return ScorePredictionResult(
                score=float(result.get("score", 50.0)),
                confidence=result.get("confidence", 0.0),
                category=result.get("category", "N/A"),
                risk_level=result.get("risk_level", "N/A"),
                explanation=result.get("explanation", []),
                error=result.get("error"),
                input_features=input_features
            )
        except Exception as e:
            logger.error(f"Error al predecir score: {str(e)}")
            # Devolver un valor por defecto
            return ScorePredictionResult(
                score=50.0,
                confidence=0.0,
                category="Error",
                risk_level="No determinado",
                explanation=["Error en el servicio de predicción"],
                error=f"Error en el servicio: {str(e)}",
                input_features=None
            )


# Evento de inicio de la aplicación
@app.on_event("startup")
async def startup_db_clients():
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
        logger.error(f"Error al inicializar servicios: {str(e)}")

# Crear schema de GraphQL incluyendo Query y Mutation
schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

# Agregar GraphQL a la aplicación
app.include_router(graphql_app, prefix="/graphql")

# Iniciar aplicación con Uvicorn si se ejecuta directamente
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # Usa la ruta correcta para tu aplicación
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True if settings.API_ENV != "production" else False,
    )