import asyncio
import time
import signal
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
from sync.data_sync import scheduled_sync, run_initial_sync

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tiempo entre sincronizaciones (en segundos)
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL_MINUTES", "60")) * 60

# Control de ejecución
running = True

def signal_handler(sig, frame):
    """Manejador de señales para detener el servicio limpiamente"""
    global running
    logger.info("Señal de detención recibida. Deteniendo servicio...")
    running = False

async def continuous_sync():
    """Servicio de sincronización continua"""
    try:
        # Realizar sincronización inicial
        logger.info("Realizando sincronización inicial...")
        await scheduled_sync()
        
        # Bucle principal de sincronización
        while running:
            logger.info(f"Esperando {SYNC_INTERVAL} segundos para la próxima sincronización...")
            for _ in range(SYNC_INTERVAL):
                if not running:
                    break
                await asyncio.sleep(1)
            
            if running:
                logger.info("Ejecutando sincronización programada...")
                await scheduled_sync()
    
    except Exception as e:
        logger.error(f"Error en el servicio de sincronización: {str(e)}")
    
    finally:
        logger.info("Servicio de sincronización detenido.")

def start_sync_service():
    """Inicia el servicio de sincronización"""
    # Registrar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Iniciando servicio de sincronización...")
    
    # Ejecutar el servicio en un bucle de eventos
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(continuous_sync())
    finally:
        loop.close()

if __name__ == "__main__":
    start_sync_service()