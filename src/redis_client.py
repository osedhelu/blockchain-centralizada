import redis
from src.config import settings
from typing import Optional
import json


class RedisClient:
    def __init__(self):
        self.client = None
    
    def initialize(self):
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            self.client.ping()
            print("Conexión a Redis establecida correctamente")
        except Exception as e:
            print(f"Error conectando a Redis: {e}")
            raise
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        try:
            return self.client.set(key, value, ex=ex)
        except Exception as e:
            print(f"Error estableciendo valor en Redis: {e}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        try:
            return self.client.get(key)
        except Exception as e:
            print(f"Error obteniendo valor de Redis: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Error eliminando clave de Redis: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"Error verificando existencia en Redis: {e}")
            return False
    
    def cache_blockchain_state(self, chain_length: int, latest_hash: str) -> bool:
        try:
            state = {
                'chain_length': chain_length,
                'latest_hash': latest_hash
            }
            return self.set('blockchain:state', json.dumps(state), ex=3600)
        except Exception as e:
            print(f"Error cacheando estado de blockchain: {e}")
            return False
    
    def get_blockchain_state(self) -> Optional[dict]:
        try:
            state_json = self.get('blockchain:state')
            if state_json:
                return json.loads(state_json)
            return None
        except Exception as e:
            print(f"Error obteniendo estado de blockchain: {e}")
            return None
    
    def cache_pending_transactions(self, transactions: list) -> bool:
        try:
            tx_list = [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in transactions]
            return self.set('blockchain:pending_tx', json.dumps(tx_list), ex=300)
        except Exception as e:
            print(f"Error cacheando transacciones pendientes: {e}")
            return False
    
    def get_pending_transactions(self) -> list:
        try:
            tx_json = self.get('blockchain:pending_tx')
            if tx_json:
                return json.loads(tx_json)
            return []
        except Exception as e:
            print(f"Error obteniendo transacciones pendientes: {e}")
            return []


redis_client = RedisClient()

