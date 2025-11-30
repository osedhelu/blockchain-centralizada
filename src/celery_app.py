from celery import Celery
from src.config import settings

# Configurar Celery usando RabbitMQ como broker y Redis como backend
celery_app = Celery(
    'blockchain_tasks',
    broker=f'amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//',
    backend=f'redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutos máximo por tarea
    task_soft_time_limit=240,  # 4 minutos soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # Los resultados expiran en 1 hora
    task_routes={
        'src.tasks.mine_block_task': {'queue': 'mining'},
        'src.tasks.process_transaction_task': {'queue': 'transactions'},
        'src.tasks.validate_chain_task': {'queue': 'validation'},
        'src.tasks.update_cache_task': {'queue': 'cache'},
    },
    task_default_queue='default',
    task_default_exchange='default',
    task_default_exchange_type='direct',
    task_default_routing_key='default',
)

# Importar tareas para que Celery las registre
# Esto debe estar al final para evitar imports circulares
try:
    import src.tasks  # noqa: F401
except ImportError:
    pass

