from celery import Task
from src.celery_app import celery_app
from src.blockchain_service import BlockchainService
from src.database import db
from src.redis_client import redis_client
from src.rabbitmq_client import rabbitmq_client
from src.models import Transaction, Block
from src.utils import parse_amount, format_amount
from typing import Optional, Dict
import traceback


class BlockchainTask(Task):
    """Clase base para tareas de blockchain con manejo de errores"""
    _blockchain_service = None
    
    @property
    def blockchain_service(self):
        if self._blockchain_service is None:
            self._blockchain_service = BlockchainService()
        return self._blockchain_service
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Manejo de errores en tareas"""
        print(f"❌ Tarea {task_id} falló: {exc}")
        print(f"Traceback: {traceback.format_exc()}")


@celery_app.task(base=BlockchainTask, bind=True, name='src.tasks.mine_block_task')
def mine_block_task(self, mining_reward_address: str) -> Dict:
    """
    Tarea asíncrona para minar un bloque
    """
    try:
        print(f"⛏️  Iniciando minería para dirección: {mining_reward_address}")
        
        # Obtener transacciones pendientes antes de minar
        pending_count = len(self.blockchain_service.get_pending_transactions())
        
        if pending_count == 0:
            return {
                'success': False,
                'message': 'No hay transacciones pendientes para minar',
                'block': None
            }
        
        # Minar el bloque
        block = self.blockchain_service.mine_pending_transactions(mining_reward_address)
        
        if block:
            block_dict = {
                'index': block.index,
                'timestamp': block.timestamp.isoformat(),
                'transactions': [tx.to_dict() for tx in block.transactions],
                'previous_hash': block.previous_hash,
                'hash': block.hash,
                'nonce': block.nonce
            }
            
            print(f"✅ Bloque #{block.index} minado exitosamente")
            
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


@celery_app.task(base=BlockchainTask, bind=True, name='src.tasks.process_transaction_task')
def process_transaction_task(self, sender: str, recipient: str, amount: float) -> Dict:
    """
    Tarea asíncrona para procesar una transacción
    """
    try:
        print(f"📝 Procesando transacción: {sender} → {recipient}, monto: {amount}")
        
        # Convertir monto a wei
        amount_wei = parse_amount(amount)
        
        # Agregar transacción
        success = self.blockchain_service.add_transaction(
            sender,
            recipient,
            float(amount)
        )
        
        if success:
            # Obtener balance actualizado
            sender_balance = self.blockchain_service.get_balance(sender)
            recipient_balance = self.blockchain_service.get_balance(recipient)
            
            print(f"✅ Transacción procesada exitosamente")
            
            return {
                'success': True,
                'message': 'Transacción agregada exitosamente',
                'transaction': {
                    'sender': sender,
                    'recipient': recipient,
                    'amount': amount_wei,
                    'amount_formatted': format_amount(amount_wei)
                },
                'balances': {
                    'sender': sender_balance,
                    'sender_formatted': format_amount(sender_balance),
                    'recipient': recipient_balance,
                    'recipient_formatted': format_amount(recipient_balance)
                }
            }
        else:
            return {
                'success': False,
                'message': 'Error al agregar transacción',
                'transaction': None
            }
    except Exception as e:
        error_msg = f"Error procesando transacción: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return {
            'success': False,
            'message': error_msg,
            'transaction': None,
            'error': str(e)
        }


@celery_app.task(base=BlockchainTask, bind=True, name='src.tasks.validate_chain_task')
def validate_chain_task(self) -> Dict:
    """
    Tarea asíncrona para validar la cadena completa
    """
    try:
        print("🔍 Validando cadena de bloques...")
        
        is_valid = self.blockchain_service.is_chain_valid()
        chain_info = self.blockchain_service.get_chain_info()
        
        result = {
            'success': True,
            'is_valid': is_valid,
            'chain_info': chain_info,
            'message': 'Cadena válida' if is_valid else 'Cadena inválida'
        }
        
        print(f"✅ Validación completada: {'Válida' if is_valid else 'Inválida'}")
        
        return result
    except Exception as e:
        error_msg = f"Error validando cadena: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return {
            'success': False,
            'is_valid': False,
            'message': error_msg,
            'error': str(e)
        }


@celery_app.task(base=BlockchainTask, bind=True, name='src.tasks.update_cache_task')
def update_cache_task(self) -> Dict:
    """
    Tarea asíncrona para actualizar la caché de Redis
    """
    try:
        print("🔄 Actualizando caché...")
        
        chain = self.blockchain_service.get_chain()
        if chain:
            latest_block = chain[-1]
            redis_client.cache_blockchain_state(
                len(chain),
                latest_block.hash
            )
            
            pending_tx = self.blockchain_service.get_pending_transactions()
            redis_client.cache_pending_transactions(pending_tx)
        
        print("✅ Caché actualizada exitosamente")
        
        return {
            'success': True,
            'message': 'Caché actualizada exitosamente'
        }
    except Exception as e:
        error_msg = f"Error actualizando caché: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
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
        print(f"📦 Procesando lote de {len(transactions)} transacciones...")
        
        results = []
        success_count = 0
        error_count = 0
        
        for tx in transactions:
            try:
                success = self.blockchain_service.add_transaction(
                    tx['sender'],
                    tx['recipient'],
                    tx['amount']
                )
                if success:
                    success_count += 1
                    results.append({
                        'success': True,
                        'transaction': tx
                    })
                else:
                    error_count += 1
                    results.append({
                        'success': False,
                        'transaction': tx,
                        'error': 'Error al agregar transacción'
                    })
            except Exception as e:
                error_count += 1
                results.append({
                    'success': False,
                    'transaction': tx,
                    'error': str(e)
                })
        
        print(f"✅ Lote procesado: {success_count} exitosas, {error_count} errores")
        
        return {
            'success': True,
            'message': f'Lote procesado: {success_count} exitosas, {error_count} errores',
            'total': len(transactions),
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        }
    except Exception as e:
        error_msg = f"Error procesando lote: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return {
            'success': False,
            'message': error_msg,
            'error': str(e)
        }

