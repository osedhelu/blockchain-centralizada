import time
import sys
from src.config import settings
from src.database import db
from src.redis_client import redis_client
from src.rabbitmq_client import rabbitmq_client
from src.api import run_api


def initialize_services():
    max_retries = 30
    retry_delay = 2
    
    print("Inicializando servicios...")
    
    for attempt in range(max_retries):
        try:
            print(f"Intento {attempt + 1}/{max_retries}: Conectando a PostgreSQL...")
            db.initialize()
            print("✓ PostgreSQL conectado")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Esperando PostgreSQL... ({e})")
                time.sleep(retry_delay)
            else:
                print(f"Error conectando a PostgreSQL después de {max_retries} intentos: {e}")
                sys.exit(1)
    
    for attempt in range(max_retries):
        try:
            print(f"Intento {attempt + 1}/{max_retries}: Conectando a Redis...")
            redis_client.initialize()
            print("✓ Redis conectado")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Esperando Redis... ({e})")
                time.sleep(retry_delay)
            else:
                print(f"Error conectando a Redis después de {max_retries} intentos: {e}")
                sys.exit(1)
    
    for attempt in range(max_retries):
        try:
            print(f"Intento {attempt + 1}/{max_retries}: Conectando a RabbitMQ...")
            rabbitmq_client.initialize()
            print("✓ RabbitMQ conectado")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Esperando RabbitMQ... ({e})")
                time.sleep(retry_delay)
            else:
                print(f"Error conectando a RabbitMQ después de {max_retries} intentos: {e}")
                sys.exit(1)
    
    print("\n✓ Todos los servicios inicializados correctamente")
    print(f"✓ API iniciando en puerto {settings.BLOCKCHAIN_API_PORT}\n")


if __name__ == "__main__":
    initialize_services()
    run_api()

