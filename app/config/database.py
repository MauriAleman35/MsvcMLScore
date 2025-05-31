from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config.settings import settings

# Importamos modelos de MongoDB
from app.db.models.user import UserDocument
from app.db.models.loan import LoanDocument
from app.db.models.monthly_payment import MonthlyPaymentDocument
from app.db.models.solicitude import SolicitudeDocument
from app.db.models.offer import OfferDocument

# Cliente MongoDB
async def get_mongo_client():
    client = AsyncIOMotorClient(settings.mongo_connection_string)
    return client

# Inicialización de Beanie
async def init_mongodb():
    client = await get_mongo_client()
    
    # Inicializar Beanie con todos nuestros modelos de documento
    await init_beanie(
        database=client[settings.MONGO_DB],
        document_models=[
            UserDocument,
            LoanDocument, 
            MonthlyPaymentDocument,
            SolicitudeDocument,
            OfferDocument
        ]
    )