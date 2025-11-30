from celery import Task
from celery.schedules import crontab
from src.celery_app import celery_app
from src.blockchain_service import BlockchainService
from src.database import db
from src.redis_client import redis_client
from src.rabbitmq_client import rabbitmq_client
from src.models import Transaction, Block
from src.utils import parse_amount, format_amount
from typing import Optional, Dict
import traceback
import time


class BlockchainTask(Task):
    """Clase base para tareas de blockchain con manejo de errores"""
    _blockchain_service = None
    _services_initialized = False
    
    def initialize_services(self):
        """Inicializa los servicios necesarios para las tareas"""
        if not self._services_initialized:
            try:
                # Inicializar base de datos
                db.initialize()
                # Inicializar Redis
                redis_client.initialize()
                # Inicializar RabbitMQ (opcional para tareas)
                try:
                    rabbitmq_client.initialize()
                except:
                    pass  # No crítico para tareas
                self._services_initialized = True
            except Exception as e:
                print(f"⚠️  Advertencia al inicializar servicios: {e}")
    
    @property
    def blockchain_service(self):
        if self._blockchain_service is None:
            self.initialize_services()
            self._blockchain_service = BlockchainService()
        return self._blockchain_service
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Manejo de errores en tareas"""
        print(f"❌ Tarea {task_id} falló: {exc}")
        print(f"Traceback: {traceback.format_exc()}")


@celery_app.task(base=BlockchainTask, bind=True, name='src.tasks.mine_block_task')
def mine_block_task(self, mining_reward_address: str = None, include_reward: bool = True) -> Dict:
    """
    Tarea asíncrona para minar un bloque
    - mining_reward_address: Dirección que recibe la recompensa (opcional)
    - include_reward: Si True, agrega recompensa de minería. Si False, mina sin recompensa
    """
    try:
        # Asegurar que los servicios estén inicializados
        self.initialize_services()
        
        reward_msg = f"con recompensa para {mining_reward_address}" if include_reward and mining_reward_address else "sin recompensa"
        print(f"⛏️  Iniciando minería {reward_msg}")
        
        # Obtener transacciones pendientes antes de minar
        pending_count = len(self.blockchain_service.get_pending_transactions())
        
        if pending_count == 0:
            return {
                'success': False,
                'message': 'No hay transacciones pendientes para minar',
                'block': None
            }
        
        # Minar el bloque (sin recompensa si mining_reward_address es None)
        block = self.blockchain_service.mine_pending_transactions(
            mining_reward_address=mining_reward_address,
            include_reward=include_reward
        )
        
        if block:
            block_dict = {
                'index': block.index,
                'timestamp': block.timestamp.isoformat(),
                'transactions': [tx.to_dict() for tx in block.transactions],
                'previous_hash': block.previous_hash,
                'hash': block.hash,
                'nonce': block.nonce
            }
            
            print(f"✅ Bloque #{block.index} minado exitosamente {reward_msg}")
            
            return {
                'success': True,
                'message': 'Bloque minado exitosamente',
                'block': block_dict
            }
        else:
            return {
                'success': False,
                'message': 'Error al guardar el bloque en la base de datos',
                'block': None
            }
    except Exception as e:
        error_msg = f"Error en minería: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return {
            'success': False,
            'message': error_msg,
            'block': None,
            'error': str(e)
        }


@celery_app.task(base=BlockchainTask, bind=True, name='src.tasks.auto_mine_task')
def auto_mine_task(self) -> Dict:
    """
    Tarea automática para minar bloques sin recompensa
    Se ejecuta periódicamente para confirmar transacciones pendientes automáticamente
    """
    try:
        # Asegurar que los servicios estén inicializados
        self.initialize_services()
        
        # Obtener transacciones pendientes
        pending_count = len(self.blockchain_service.get_pending_transactions())
        
        if pending_count == 0:
            return {
                'success': False,
                'message': 'No hay transacciones pendientes para minar',
                'block': None,
                'worker': self.request.hostname
            }
        
        print(f"🤖 Worker {self.request.hostname}: Minando automáticamente {pending_count} transacción(es) pendiente(s) (sin recompensa)")
        
        # Minar sin recompensa
        block = self.blockchain_service.mine_pending_transactions(
            mining_reward_address=None,
            include_reward=False
        )
        
        if block:
            block_dict = {
                'index': block.index,
                'timestamp': block.timestamp.isoformat(),
                'transactions_count': len(block.transactions),
                'previous_hash': block.previous_hash,
                'hash': block.hash,
                'nonce': block.nonce
            }
            
            print(f"✅ Worker {self.request.hostname}: Bloque #{block.index} minado automáticamente (sin recompensa)")
            
            return {
                'success': True,
                'message': f'Bloque #{block.index} minado automáticamente sin recompensa',
                'block': block_dict,
                'worker': self.request.hostname
            }
        else:
            return {
                'success': False,
                'message': 'Error al guardar el bloque en la base de datos',
                'block': None,
                'worker': self.request.hostname
            }
    except Exception as e:
        error_msg = f"Error en minería automática: {str(e)}"
        print(f"❌ Worker {self.request.hostname}: {error_msg}")
        print(traceback.format_exc())
        return {
            'success': False,
            'message': error_msg,
            'block': None,
            'error': str(e),
            'worker': self.request.hostname
        }


@celery_app.task(base=BlockchainTask, bind=True, name='src.tasks.process_transaction_task')
def process_transaction_task(self, sender: str, recipient: str, amount: float) -> Dict:
    """
    Tarea asíncrona para procesar una transacción
    """
    try:
        self.initialize_services()
        
        success = self.blockchain_service.add_transaction(sender, recipient, amount)
        
        if success:
            return {
                'success': True,
                'message': 'Transacción agregada exitosamente',
                'transaction': {
                    'sender': sender,
                    'recipient': recipient,
                    'amount': amount
                }
            }
        else:
            return {
                'success': False,
                'message': 'Error al agregar transacción'
            }
    except Exception as e:
        error_msg = f"Error procesando transacción: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'error': str(e)
        }


@celery_app.task(base=BlockchainTask, bind=True, name='src.tasks.validate_chain_task')
def validate_chain_task(self) -> Dict:
    """
    Tarea asíncrona para validar la cadena de bloques
    """
    try:
        self.initialize_services()
        
        is_valid = self.blockchain_service.is_chain_valid()
        chain_length = len(self.blockchain_service.get_chain())
        
        return {
            'success': True,
            'is_valid': is_valid,
            'chain_length': chain_length,
            'message': 'Cadena válida' if is_valid else 'Cadena inválida'
        }
    except Exception as e:
        error_msg = f"Error validando cadena: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'error': str(e)
        }


@celery_app.task(base=BlockchainTask, bind=True, name='src.tasks.update_cache_task')
def update_cache_task(self) -> Dict:
    """
    Tarea asíncrona para actualizar la caché de Redis
    """
    try:
        self.initialize_services()
        
        chain = self.blockchain_service.get_chain()
        if chain:
            latest_block = chain[-1]
            redis_client.cache_blockchain_state(
                len(chain),
                latest_block.hash
            )
            
            pending_tx = self.blockchain_service.get_pending_transactions()
            redis_client.cache_pending_transactions(pending_tx)
            
            return {
                'success': True,
                'message': 'Caché actualizada exitosamente',
                'chain_length': len(chain),
                'pending_transactions': len(pending_tx)
            }
        else:
            return {
                'success': False,
                'message': 'No hay bloques en la cadena'
            }
    except Exception as e:
        error_msg = f"Error actualizando caché: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'error': str(e)
        }


@celery_app.task(base=BlockchainTask, bind=True, name='src.tasks.batch_process_transactions_task')
def batch_process_transactions_task(self, transactions: list) -> Dict:
    """
    Tarea asíncrona para procesar múltiples transacciones en lote
    """
    try:
        self.initialize_services()
        
        results = []
        for tx in transactions:
            try:
                success = self.blockchain_service.add_transaction(
                    tx['sender'],
                    tx['recipient'],
                    float(tx['amount'])
                )
                results.append({
                    'success': success,
                    'transaction': tx
                })
            except Exception as e:
                results.append({
                    'success': False,
                    'transaction': tx,
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r['success'])
        
        return {
            'success': True,
            'message': f'Procesadas {success_count}/{len(transactions)} transacciones',
            'results': results,
            'total': len(results),
            'success_count': success_count
        }
    except Exception as e:
        error_msg = f"Error procesando lote de transacciones: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'error': str(e)
        }
