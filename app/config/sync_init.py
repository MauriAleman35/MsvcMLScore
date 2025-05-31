import asyncio
import logging
from sqlalchemy.orm import Session
from app.db.postgres.session import SessionLocal
from app.db.postgres.models import User, Loan, MonthlyPayment, Solicitude, Offer
from app.db.mongodb.models.user import UserDocument
from app.db.mongodb.models.loan import LoanDocument
from app.db.mongodb.models.monthly_payment import MonthlyPaymentDocument
from app.db.mongodb.models.solicitude import SolicitudeDocument
from app.db.mongodb.models.offer import OfferDocument

logger = logging.getLogger(__name__)

async def sync_users():
    """Sincroniza usuarios de PostgreSQL a MongoDB"""
    logger.info("Iniciando sincronización de usuarios")
    
    # Obtener sesión PostgreSQL
    db = SessionLocal()
    try:
        # Obtener todos los usuarios prestatarios
        postgres_users = db.query(User).filter(User.user_type == "prestatario").all()
        
        # Convertir y guardar en MongoDB
        for pg_user in postgres_users:
            # Verificar si ya existe
            existing = await UserDocument.find_one({"id": pg_user.id})
            
            # Crear documento para MongoDB
            user_doc = UserDocument(
                id=pg_user.id,
                name=pg_user.name,
                last_name=pg_user.last_name,
                user_type=pg_user.user_type,
                email=pg_user.email,
                adress_verified=pg_user.adress_verified,
                identity_verified=pg_user.identity_verified,
                created_at=pg_user.created_at,
                updated_at=pg_user.updated_at
            )
            
            if existing:
                # Actualizar si existe
                user_doc.id = existing.id  # Preservar ID de MongoDB
                await existing.update({"$set": user_doc.dict(exclude={"id"})})
                logger.debug(f"Usuario actualizado: {pg_user.id}")
            else:
                # Crear nuevo
                await user_doc.insert()
                logger.debug(f"Usuario creado: {pg_user.id}")
                
        logger.info(f"Sincronización de usuarios completada: {len(postgres_users)} usuarios")
    
    finally:
        db.close()

async def sync_all_data():
    """Sincroniza todos los datos de PostgreSQL a MongoDB"""
    await sync_users()
    # Implementar funciones similares para loans, payments, etc.
    # await sync_loans()
    # await sync_monthly_payments()
    # await sync_solicitudes()
    # await sync_offers()
    
    logger.info("Sincronización completa de datos finalizada")