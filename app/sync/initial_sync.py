import asyncio
import logging
from datetime import datetime,timezone
from sqlalchemy import select
from typing import Dict, Any, List

# Importar modelos Beanie
from app.db.models.user import UserDocument
from app.db.models.loan import LoanDocument
from app.db.models.monthly_payment import MonthlyPaymentDocument
from app.db.models.solicitude import SolicitudeDocument
from app.db.models.offer import OfferDocument
from app.sync.pg_conector import get_pg_table,pg_session_local


logger = logging.getLogger(__name__)

async def sync_users():
    """Sincroniza usuarios desde PostgreSQL a MongoDB"""
    logger.info("Iniciando sincronización de usuarios")
    
    # Obtener tablas PostgreSQL
    pg_tables = get_pg_table()
    users_table = pg_tables.get('users')
    
    if not users_table:
        logger.error("No se pudo encontrar la tabla 'users' en PostgreSQL")
        return
    
    # Crear sesión PostgreSQL
    session = pg_session_local()
    
    try:
        # Consultar usuarios de tipo prestatario
        query = select(users_table).where(users_table.c.user_type == 'prestatario')
        result = session.execute(query)
        
        # Contador para seguimiento
        count = 0
        
        # Procesar cada usuario
        for row in result:
            user_data = dict(row._mapping)
            
            # Crear o actualizar documento MongoDB
            user_doc = await UserDocument.find_one({"id": user_data["id"]})
            
            if user_doc:
                # Actualizar documento existente
                user_doc.name = user_data.get("name", user_doc.name)
                user_doc.last_name = user_data.get("last_name", user_doc.last_name)
                user_doc.email = user_data.get("email", user_doc.email)
                user_doc.adress_verified = user_data.get("adress_verified", user_doc.adress_verified)
                user_doc.identity_verified = user_data.get("identity_verified", user_doc.identity_verified)
                user_doc.updated_at = datetime.utcnow()
                await user_doc.save()
                logger.debug(f"Usuario actualizado: {user_data['id']}")
            else:
                # Crear nuevo documento
                new_user = UserDocument(
                    id=user_data["id"],
                    name=user_data.get("name", ""),
                    last_name=user_data.get("last_name", ""),
                    user_type=user_data.get("user_type", "prestatario"),
                    email=user_data.get("email"),
                    adress_verified=user_data.get("adress_verified", False),
                    identity_verified=user_data.get("identity_verified", False),
                    created_at=user_data.get("created_at", datetime.utcnow()),
                    updated_at=datetime.utcnow()
                )
                await new_user.insert()
                logger.debug(f"Usuario creado: {user_data['id']}")
            
            count += 1
        
        logger.info(f"Sincronización de usuarios completada: {count} usuarios procesados")
    
    except Exception as e:
        logger.error(f"Error en sincronización de usuarios: {str(e)}")
    finally:
        session.close()

async def sync_loans():
    """Sincroniza préstamos desde PostgreSQL a MongoDB"""
    logger.info("Iniciando sincronización de préstamos")
    
    # Obtener tablas PostgreSQL
    pg_tables = get_pg_table()
    loans_table = pg_tables.get('loans')
    
    if not loans_table:
        logger.error("No se pudo encontrar la tabla 'loans' en PostgreSQL")
        return
    
    # Crear sesión PostgreSQL
    session = pg_session_local()
    
    try:
        # Consultar todos los préstamos
        query = select(loans_table)
        result = session.execute(query)
        
        # Contador para seguimiento
        count = 0
        
        # Procesar cada préstamo
        for row in result:
            loan_data = dict(row._mapping)
            
            # Crear o actualizar documento MongoDB
            loan_doc = await LoanDocument.find_one({"id": loan_data["id"]})
            
            if loan_doc:
                # Actualizar documento existente
                loan_doc.current_status = loan_data.get("current_status", loan_doc.current_status)
                loan_doc.late_payment_count = loan_data.get("late_payment_count", loan_doc.late_payment_count)
                loan_doc.avg_days_late = loan_data.get("avg_days_late", loan_doc.avg_days_late)
                loan_doc.remaining_amount = loan_data.get("remaining_amount", loan_doc.remaining_amount)
                loan_doc.updated_at = datetime.utcnow()
                await loan_doc.save()
                logger.debug(f"Préstamo actualizado: {loan_data['id']}")
            else:
                # Crear nuevo documento
                new_loan = LoanDocument(
                    id=loan_data["id"],
                    id_offer=loan_data.get("id_offer"),
                    borrower_id=loan_data.get("borrower_id"),
                    current_status=loan_data.get("current_status", ""),
                    late_payment_count=loan_data.get("late_payment_count", 0),
                    avg_days_late=loan_data.get("avg_days_late", 0.0),
                    total_amount=loan_data.get("total_amount", 0.0),
                    remaining_amount=loan_data.get("remaining_amount", 0.0),
                    created_at=loan_data.get("created_at", datetime.utcnow()),
                    updated_at=datetime.utcnow()
                )
                await new_loan.insert()
                logger.debug(f"Préstamo creado: {loan_data['id']}")
            
            count += 1
        
        logger.info(f"Sincronización de préstamos completada: {count} préstamos procesados")
    
    except Exception as e:
        logger.error(f"Error en sincronización de préstamos: {str(e)}")
    finally:
        session.close()

async def sync_monthly_payments():
    """Sincroniza pagos mensuales desde PostgreSQL a MongoDB"""
    logger.info("Iniciando sincronización de pagos mensuales")
    
    # Obtener tablas PostgreSQL
    pg_tables = get_pg_table()
    payments_table = pg_tables.get('monthly_payments')
    
    if not payments_table:
        logger.error("No se pudo encontrar la tabla 'monthly_payments' en PostgreSQL")
        return
    
    # Crear sesión PostgreSQL
    session =pg_session_local()
    
    try:
        # Consultar todos los pagos
        query = select(payments_table)
        result = session.execute(query)
        
        # Contador para seguimiento
        count = 0
        
        # Procesar cada pago
        for row in result:
            payment_data = dict(row._mapping)
            
            # Crear o actualizar documento MongoDB
            payment_doc = await MonthlyPaymentDocument.find_one({"id": payment_data["id"]})
            
            if payment_doc:
                # Actualizar documento existente
                payment_doc.payment_status = payment_data.get("payment_status", payment_doc.payment_status)
                payment_doc.days_late = payment_data.get("days_late", payment_doc.days_late)
                payment_doc.penalty_amount = payment_data.get("penalty_amount", payment_doc.penalty_amount)
                payment_doc.updated_at = datetime.utcnow()
                await payment_doc.save()
                logger.debug(f"Pago actualizado: {payment_data['id']}")
            else:
                # Crear nuevo documento
                new_payment = MonthlyPaymentDocument(
                    id=payment_data["id"],
                    id_loan=payment_data.get("id_loan"),
                    payment_status=payment_data.get("payment_status", ""),
                    payment_date=payment_data.get("payment_date"),
                    amount=payment_data.get("amount", 0.0),
                    days_late=payment_data.get("days_late", 0),
                    penalty_amount=payment_data.get("penalty_amount", 0.0),
                    borrow_verified=payment_data.get("borrow_verified", False),
                    created_at=payment_data.get("created_at", datetime.utcnow()),
                    updated_at=datetime.utcnow()
                )
                await new_payment.insert()
                logger.debug(f"Pago creado: {payment_data['id']}")
            
            count += 1
        
        logger.info(f"Sincronización de pagos completada: {count} pagos procesados")
    
    except Exception as e:
        logger.error(f"Error en sincronización de pagos: {str(e)}")
    finally:
        session.close()

async def sync_solicitudes():
    """Sincroniza solicitudes de préstamos desde PostgreSQL a MongoDB"""
    logger.info("Iniciando sincronización de solicitudes de préstamos")
    
    # Obtener tablas PostgreSQL
    pg_tables = get_pg_table()
    solicitudes_table = pg_tables.get('solicitudes')
    
    if not solicitudes_table:
        logger.error("No se pudo encontrar la tabla 'solicitudes' en PostgreSQL")
        return
    
    # Crear sesión PostgreSQL
    session = pg_session_local()
    
    try:
        # Consultar todas las solicitudes
        query = select(solicitudes_table)
        result = session.execute(query)
        
        # Contador para seguimiento
        count = 0
        
        # Procesar cada solicitud
        for row in result:
            solicitude_data = dict(row._mapping)
            
            # Crear o actualizar documento MongoDB
            solicitude_doc = await SolicitudeDocument.find_one({"id": solicitude_data["id"]})
            
            if solicitude_doc:
                # Actualizar documento existente
                solicitude_doc.status = solicitude_data.get("status", solicitude_doc.status)
                solicitude_doc.loan_amount = solicitude_data.get("loan_amount", solicitude_doc.loan_amount)
                await solicitude_doc.save()
                logger.debug(f"Solicitud actualizada: {solicitude_data['id']}")
            else:
                # Crear nuevo documento
                new_solicitude = SolicitudeDocument(
                    id=int(solicitude_data["id"]),
                    borrower_id=int(solicitude_data.get("borrower_id", 0)),
                    loan_amount=float(solicitude_data.get("loan_amount", 0.0)),
                    status=solicitude_data.get("status", "pending"),
                    created_at=solicitude_data.get("created_at", datetime.now(timezone.utc))
                )
                await new_solicitude.insert()
                logger.debug(f"Solicitud creada: {solicitude_data['id']}")
            
            count += 1
        
        logger.info(f"Sincronización de solicitudes completada: {count} solicitudes procesadas")
    
    except Exception as e:
        logger.error(f"Error en sincronización de solicitudes: {str(e)}")
    finally:
        session.close()

async def sync_offers():
    """Sincroniza ofertas de préstamos desde PostgreSQL a MongoDB"""
    logger.info("Iniciando sincronización de ofertas de préstamos")
    
    # Obtener tablas PostgreSQL
    pg_tables = get_pg_table()
    offers_table = pg_tables.get('offers')
    
    if not offers_table:
        logger.error("No se pudo encontrar la tabla 'offers' en PostgreSQL")
        return
    
    # Crear sesión PostgreSQL
    session = pg_session_local()
    
    try:
        # Consultar todas las ofertas
        query = select(offers_table)
        result = session.execute(query)
        
        # Contador para seguimiento
        count = 0
        
        # Procesar cada oferta
        for row in result:
            offer_data = dict(row._mapping)
            
            # Crear o actualizar documento MongoDB
            offer_doc = await OfferDocument.find_one({"id": offer_data["id"]})
            
            if offer_doc:
                # Actualizar documento existente
                offer_doc.status = offer_data.get("status", offer_doc.status)
                offer_doc.interest = offer_data.get("interest", offer_doc.interest)
                offer_doc.monthly_payment = offer_data.get("monthly_payment", offer_doc.monthly_payment)
                await offer_doc.save()
                logger.debug(f"Oferta actualizada: {offer_data['id']}")
            else:
                # Crear nuevo documento
                new_offer = OfferDocument(
                    id=int(offer_data["id"]),
                    id_solicitude=int(offer_data.get("id_solicitude", 0)),
                    partner_id=int(offer_data.get("partner_id", 0)),
                    interest=float(offer_data.get("interest", 0.0)),
                    loan_term=int(offer_data.get("loan_term", 0)),
                    monthly_payment=float(offer_data.get("monthly_payment", 0.0)),
                    total_repayment_amount=float(offer_data.get("total_repayment_amount", 0.0)),
                    status=offer_data.get("status", "aceptada"),
                    created_at=offer_data.get("created_at", datetime.now(timezone.utc))
                )
                await new_offer.insert()
                logger.debug(f"Oferta creada: {offer_data['id']}")
            
            count += 1
        
        logger.info(f"Sincronización de ofertas completada: {count} ofertas procesadas")
    
    except Exception as e:
        logger.error(f"Error en sincronización de ofertas: {str(e)}")
    finally:
        session.close()

async def sync_all_data():
    """Ejecuta la sincronización completa de todos los datos"""
    logger.info("Iniciando sincronización completa de datos")
    
    try:
        # Sincronizar en secuencia para mantener integridad referencial
        await sync_users()
        await sync_loans()
        await sync_monthly_payments()
        await sync_offers()
        await sync_solicitudes()
        
        logger.info("Sincronización completa finalizada exitosamente")
    except Exception as e:
        logger.error(f"Error en sincronización completa: {str(e)}")