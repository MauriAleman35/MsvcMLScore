from email.utils import formatdate
import logging
import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, mongodb_client, db_name):
        """
        Inicializa el procesador de datos
        
        Args:
            mongodb_client: Cliente MongoDB ya conectado
            db_name: Nombre de la base de datos
        """
        self.db = mongodb_client[db_name]
        
    async def process_entity(self, entity_type: str, data: Dict[str, Any]) -> None:
        """
        Procesa una entidad recibida de RabbitMQ
        
        Args:
            entity_type: Tipo de entidad (user, loan, etc.)
            data: Datos del mensaje completo
        """
        try:
            # Extraer información importante del mensaje
            operation = data.get('operation')
            entity_data = data.get('data', {})
            entity_id = entity_data.get('id')
            
            if not entity_id:
                logger.warning(f"Mensaje recibido sin ID para {entity_type}, ignorando")
                return
                
            logger.info(f"Procesando {operation} para {entity_type} con ID {entity_id}")
            
            # Procesar según la operación
            if operation == 'delete':
                await self._handle_delete(entity_type, entity_id)
            elif operation in ['insert', 'update']:
                await self._handle_upsert(entity_type, entity_data)
            else:
                logger.warning(f"Operación desconocida: {operation}")
                
        except Exception as e:
            logger.error(f"Error procesando {entity_type}: {str(e)}")
    
    async def _handle_upsert(self, entity_type: str, data: Dict[str, Any]) -> None:
        """Maneja la inserción o actualización de una entidad"""
        try:
            # Transformar datos según el tipo de entidad y esquema Beanie
            transformed_data = self._transform_data(entity_type, data)
            
            # Obtener la colección correcta
            collection = self.db[entity_type]
            
            # Buscar si existe primero
            existing = await collection.find_one({'id': data.get('id')})
            
            if existing:
                # Actualizar existente, preservando _id de MongoDB
                transformed_data['_id'] = existing['_id']
                result = await collection.replace_one(
                    {'_id': existing['_id']}, 
                    transformed_data
                )
                logger.info(f"Actualizado {entity_type} con ID {data.get('id')}, matched: {result.matched_count}")
            else:
                # Insertar nuevo
                result = await collection.insert_one(transformed_data)
                logger.info(f"Insertado nuevo {entity_type} con ID {data.get('id')}, MongoDB ID: {result.inserted_id}")
                
        except Exception as e:
            logger.error(f"Error en upsert de {entity_type}: {str(e)}")
            raise
    
    async def _handle_delete(self, entity_type: str, entity_id: Any) -> None:
        """Maneja la eliminación de una entidad"""
        try:
            collection = self.db[entity_type]
            result = await collection.delete_one({'id': entity_id})
            logger.info(f"Eliminado {entity_type} con ID {entity_id}, matched: {result.deleted_count}")
        except Exception as e:
            logger.error(f"Error al eliminar {entity_type}: {str(e)}")
            raise
    
    def _transform_data(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma los datos según el tipo de entidad y esquema Beanie
        """
        if entity_type == 'user':
            return self._transform_user_data(data)
        elif entity_type == 'loan':
            return self._transform_loan_data(data)
        elif entity_type == 'solicitude':
            return self._transform_solicitude_data(data)
        elif entity_type == 'offer': # no cree este para rabbitmq
            return self._transform_offer_data(data)
        elif entity_type == 'monthly_payment': # no cree este para rabbitmq
            return self._transform_payment_data(data)
        else:
            # Para otros tipos, usar los datos directamente
            return data
    
    def _transform_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma datos de usuario según esquema UserDocument"""
        now = datetime.now(timezone.utc)
        return {
            'id': data.get('id'),
            'name': data.get('name', ''),
            'last_name': data.get('lastName', ''),  # Cambio de lastName a last_name
            'user_type': data.get('userType', 'prestatario'),  # Cambio de userType a user_type
            'email': data.get('email'),
            'adress_verified': data.get('adressVerified', False),
            'identity_verified': data.get('identityVerified', False),
            # 'created_at': now,
        }
    
    def _transform_loan_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma datos de préstamo según esquema LoanDocument"""
        now = datetime.now(timezone.utc)
        
        # Conversión de fechas (corrigiendo nombres de campos)
        start_date = self._parse_date(data.get('startDate', now))  # Corregido: startDdate → startDate
        end_date = self._parse_date(data.get('endDate', None))     # Corregido: end_date → endDate
        
        # Si tenemos un objeto offer completo, extraemos su ID
        offer_id = None
        if isinstance(data.get('offer'), dict):
            offer_id = data.get('offer', {}).get('id')
        else:
            # Si solo tenemos el ID directo
            offer_id = data.get('offer')
        
        return {
            'id': data.get('id'),
            'id_offer': offer_id,  # Corregido: acceso al ID de oferta
            'loan_amount': float(data.get('loanAmount', 0)),  # Corregido: amount → loanAmount
            'start_date': self._format_date_for_mongo(start_date),
            'end_date': self._format_date_for_mongo(end_date) if end_date else None,
            'hash_blockchain': data.get('hashBlockchain', ''),  # Corregido: hash_blockchain → hashBlockchain
            'current_status': data.get('currentStatus', 'al_dia'),  # Corregido: status → currentStatus
            'late_payment_count': int(data.get('latePaymentCount', 0)),  # Corregido: late_payment_count → latePaymentCount
            'last_status_update': self._format_date_for_mongo(data.get('lastStatusUpdate', now)),  # Añadido formato
        }
    
    def _transform_solicitude_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma datos de solicitud según esquema SolicitudeDocument"""
        now = datetime.now(timezone.utc)
        
        # Compatibilidad con ambos formatos de datos
        borrower_id = None
        if "borrower" in data and data["borrower"] is not None:
            # Formato antiguo (objeto anidado)
            borrower_id = data["borrower"].get("id")
        elif "borrowerId" in data:
            # Nuevo formato (valor directo)
            borrower_id = data["borrowerId"]
        
        return {
            "id": data["id"],
            "borrower_id": borrower_id,  # Usar el ID extraído
            "loan_amount": data.get("loanAmount"),
            "status": data["status"],
            "created_at": self._format_date_for_mongo(data.get("createdAt"))
        }
    
    def _transform_offer_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma datos de oferta según esquema OfferDocument"""
        now = datetime.now(timezone.utc)
        return {
            'id': data.get('id'),
            'id_solicitude': data.get('solicitude', {}).get('id'),  # Corregido: antes buscaba solicitude_id
            'partner_id': data.get('partnerId'),  # Corregido: antes buscaba lender_id
            'interest': float(data.get('interest', 0)),  # Corregido: antes buscaba interest_rate
            'loan_term': int(data.get('loanTerm', 0)),  # Corregido: antes buscaba term_months
            'monthly_payment': float(data.get('monthlyPayment', 0)),  # Corregido: cambiado a camelCase
            'total_repayment_amount': float(data.get('totalRepaymentAmount', 0)),  # Corregido: antes buscaba total_amount
            'status': data.get('status', 'pendiente'),
            'created_at': self._format_date_for_mongo(data.get("createdAt")) if data.get("createdAt") else self._format_date_for_mongo(datetime.now()),
        }
    
    def _transform_payment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma datos de pago mensual desde formato JSON (camelCase) 
        al esquema MonthlyPaymentDocument para MongoDB (snake_case)
        """
        now = datetime.now(timezone.utc)
        
        # Extraer ID de préstamo desde diferentes estructuras posibles
        loan_id = None
        if "loanId" in data:
            # Formato nuevo: campo directo loanId
            loan_id = data.get("loanId")
        elif isinstance(data.get('loan'), dict):
            # Formato anidado: objeto loan con propiedad id
            loan_id = data.get('loan', {}).get('id')
        else:
            # Formato alternativo: valor directo en loan
            loan_id = data.get('loan')
        
        # Crear documento con campos en snake_case para MongoDB
        return {
            'id': data.get('id'),
            'id_loan': loan_id,
            'due_date': self._format_date_for_mongo(data.get('dueDate', now)),
            'payment_date': self._format_date_for_mongo(data.get('paymentDate')) if data.get('paymentDate') else None,
            'borrow_verified': data.get('borrowVerified', False),
            'partner_verified': data.get('partnerVerified', False),
            'comprobant_file': data.get('comprobantFile', ''),
            'days_late': int(data.get('daysLate', 0)),
            'penalty_amount': float(data.get('penaltyAmount', 0)),
            'payment_status': data.get('paymentStatus', 'pendiente'),
        }
    
    def _parse_date(self, date_value):
        """Convierte diferentes formatos de fecha a datetime UTC"""
        if not date_value:
            return datetime.now(timezone.utc)
            
        if isinstance(date_value, datetime):
            # Asegurar que la fecha tenga zona horaria
            if date_value.tzinfo is None:
                return date_value.replace(tzinfo=timezone.utc)
            return date_value
            
        if isinstance(date_value, str):
            try:
                # Intentar diferentes formatos
                if 'T' in date_value:
                    parsed = datetime.fromisoformat(date_value)
                else:
                    parsed = datetime.fromisoformat(date_value.replace(' ', 'T'))
                
                # Asegurar que la fecha tenga zona horaria
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed
            except ValueError:
                logger.warning(f"No se pudo parsear la fecha: {date_value}")
                return datetime.now(timezone.utc)
            
        if isinstance(date_value, list):
            # Formato de timestamp como lista [año, mes, día, hora, minuto, segundo, microsegundo]
            try:
                dt = datetime(*date_value[:7])
                return dt.replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.warning(f"Error al parsear fecha de lista: {date_value} - {str(e)}")
                return datetime.now(timezone.utc)
                
        # Valor por defecto
        return datetime.now(timezone.utc)
    
 
    def _format_date_for_mongo(self, date_value):
        """
        Convierte una fecha al formato estándar para MongoDB: YYYY-MM-DDThh:mm:ss
        """
        # Primero asegurar que tenemos un objeto datetime
        dt = self._parse_date(date_value)
        
        # Formatear a string en formato YYYY-MM-DDThh:mm:ss
        return dt.strftime("%Y-%m-%dT%H:%M:%S")