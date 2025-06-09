import json
import logging
import asyncio
import aio_pika
from motor.motor_asyncio import AsyncIOMotorClient
import os
from app.events.data_processor import DataProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(self, rabbitmq_url, mongodb_url, db_name, max_retries=5):
        self.rabbitmq_url = rabbitmq_url
        self.mongodb_url = mongodb_url
        self.db_name = db_name
        self.connection = None
        self.channel = None
        self.mongodb = None
        self.data_processor = None  # Inicializado en connect()
        self.max_retries = max_retries
        
    async def connect(self):
        try:
            # Conectar a MongoDB Atlas cluster
            logger.info(f"Conectando a MongoDB Atlas: {self.mongodb_url}")
            mongo_client = AsyncIOMotorClient(self.mongodb_url)
            self.mongodb = mongo_client[self.db_name]
            await self.mongodb.command('ping')
            logger.info("Conexión a MongoDB establecida correctamente")
            
            # Inicializar el procesador de datos
            self.data_processor = DataProcessor(mongo_client, self.db_name)
            logger.info("Procesador de datos inicializado")
            
            # Conectar a RabbitMQ con reintentos
            retry_count = 0
            while retry_count < self.max_retries:
                try:
                    logger.info(f"Intento {retry_count+1} de conexión a RabbitMQ: {self.rabbitmq_url}")
                    self.connection = await aio_pika.connect_robust(
                        self.rabbitmq_url,
                        timeout=30
                    )
                    self.channel = await self.connection.channel()
                    await self.channel.set_qos(prefetch_count=1)
                    logger.info("¡Conexión a RabbitMQ establecida correctamente!")
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count >= self.max_retries:
                        raise
                    wait_time = min(30, 2 ** retry_count)
                    logger.warning(f"Error al conectar a RabbitMQ. Reintentando en {wait_time} segundos. Error: {str(e)}")
                    await asyncio.sleep(wait_time)
            
            # Crear el exchange
            exchange_name = "erp-exchange"
            exchange = await self.channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            logger.info(f"Exchange {exchange_name} declarado correctamente")
            
            # Definir las tablas/entidades a sincronizar (igual que en la configuración Spring)
            tables = ["user", "solicitude", "offer", "loan", "monthly_payment"]
            
            # Crear las colas para cada tabla y vincularlas al exchange
            for table in tables:
                try:
                    # Nombre de cola según el formato "ml-sync-{table}"
                    queue_name = f"ml-sync-{table}"
                    logger.info(f"Declarando cola {queue_name}")
                    
                    # Crear la cola
                    queue = await self.channel.declare_queue(
                        queue_name,
                        durable=True,
                        auto_delete=False
                    )
                    
                    # Vincular la cola al exchange con el routing key apropiado
                    routing_key = f"{table}.*"  # Ejemplo: "user.create", "user.update", etc.
                    await queue.bind(exchange, routing_key)
                    logger.info(f"Cola {queue_name} vinculada a {exchange_name} con routing_key={routing_key}")
                    
                    # Configurar el consumidor
                    await queue.consume(self._get_message_handler(table))
                    logger.info(f"Consumidor configurado para {queue_name}")
                    
                except Exception as e:
                    logger.error(f"Error al configurar {table}: {str(e)}")
                    # Continuar con la siguiente tabla
                    continue
            
            logger.info("Servicio de sincronización iniciado - Esperando mensajes...")
            
        except Exception as e:
            logger.error(f"Error al conectar: {str(e)}")
            raise
            
    def _get_message_handler(self, entity_type):
        async def handle_message(message):
            async with message.process():
                try:
                    # Decodificar y procesar mensaje
                    body = message.body.decode()
                    logger.info(f"Mensaje recibido para {entity_type}: {body[:100]}...")
                    
                    data = json.loads(body)
                    logger.info(f"Procesando mensaje: {data}")
                    
                    # Usar el procesador de datos para manejar la entidad
                    await self.data_processor.process_entity(entity_type, data)
                    
                except Exception as e:
                    logger.error(f"Error procesando mensaje: {str(e)}")
                
        return handle_message
    
    async def close(self):
        """Cerrar conexiones"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

# Usar la IP real para conectar a RabbitMQ
rabbitmq_host = "192.168.1.3"  # Tu IP local que funciona
rabbitmq_port = os.environ.get("RABBITMQ_PORT", "5672")
rabbitmq_user = "admin"
rabbitmq_password = "newpassword"
rabbitmq_vhost = os.environ.get("RABBITMQ_VHOST", "/")

# Construir URL completa de RabbitMQ
rabbitmq_url = f"amqp://{rabbitmq_user}:{rabbitmq_password}@{rabbitmq_host}:{rabbitmq_port}/{rabbitmq_vhost}"

# MongoDB directamente del .env
mongodb_url = os.environ.get("MONGO_URI", "mongodb+srv://mauricioaleman3524:mauri@cluster1.b2lqvyz.mongodb.net/")
db_name = os.environ.get("MONGO_DB", "loanData")

async def main():
    consumer = None
    try:
        logger.info(f"Usando RabbitMQ en: {rabbitmq_host}:{rabbitmq_port}")
        logger.info(f"Usando MongoDB en: {mongodb_url.split('@')[-1]}")
        logger.info(f"Base de datos: {db_name}")
        
        consumer = RabbitMQConsumer(
            rabbitmq_url=rabbitmq_url,
            mongodb_url=mongodb_url,
            db_name=db_name,
            max_retries=5
        )
        
        await consumer.connect()
        
        # Mantener el servicio ejecutándose
        while True:
            await asyncio.sleep(3600)
            
    except KeyboardInterrupt:
        logger.info("Deteniendo servicio por interrupción de usuario")
    except Exception as e:
        logger.error(f"Error fatal en el servicio: {str(e)}")
    finally:
        if consumer and hasattr(consumer, 'close'):
            await consumer.close()
        logger.info("Servicio finalizado")

if __name__ == "__main__":
    asyncio.run(main())