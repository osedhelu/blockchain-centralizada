from src.models import Blockchain, Transaction, Block
from src.database import db
from src.redis_client import redis_client
from src.rabbitmq_client import rabbitmq_client
from src.config import settings
from src.genesis import genesis_loader
from typing import List, Optional, Dict


class BlockchainService:
    def __init__(self):
        self.blockchain = None
        self._initialize_blockchain()
    
    def _initialize_blockchain(self):
        try:
            # Asegurar que la base de datos esté inicializada
            if db.connection_pool is None:
                db.initialize()
            
            blocks = db.get_all_blocks()
            if blocks:
                self.blockchain = Blockchain(
                    difficulty=settings.BLOCKCHAIN_DIFFICULTY,
                    mining_reward=settings.BLOCKCHAIN_MINING_REWARD
                )
                self.blockchain.chain = blocks
                print(f"Blockchain cargada desde BD: {len(blocks)} bloques")
                
                # Cargar transacciones pendientes desde Redis si están disponibles
                try:
                    if redis_client.client is None:
                        redis_client.initialize()
                    pending_tx_data = redis_client.get_pending_transactions()
                    if pending_tx_data:
                        from src.models import Transaction
                        from datetime import datetime
                        self.blockchain.pending_transactions = []
                        for tx_dict in pending_tx_data:
                            tx = Transaction(
                                sender=tx_dict.get('sender', ''),
                                recipient=tx_dict.get('recipient', ''),
                                amount=int(tx_dict.get('amount', 0)),
                                timestamp=datetime.fromisoformat(tx_dict.get('timestamp', datetime.now().isoformat())) if isinstance(tx_dict.get('timestamp'), str) else tx_dict.get('timestamp', datetime.now())
                            )
                            self.blockchain.pending_transactions.append(tx)
                        print(f"✓ Transacciones pendientes cargadas desde Redis: {len(self.blockchain.pending_transactions)}")
                except Exception as e:
                    print(f"⚠️  No se pudieron cargar transacciones pendientes desde Redis: {e}")
            else:
                # Cargar transacciones del génesis
                genesis_loader.load_genesis()
                genesis_transactions = genesis_loader.get_genesis_transactions()
                
                # Crear blockchain con transacciones del génesis
                self.blockchain = Blockchain(
                    difficulty=settings.BLOCKCHAIN_DIFFICULTY,
                    mining_reward=settings.BLOCKCHAIN_MINING_REWARD,
                    genesis_transactions=genesis_transactions
                )
                
                genesis_block = self.blockchain.chain[0]
                genesis_timestamp = genesis_loader.get_genesis_timestamp()
                if genesis_timestamp:
                    genesis_block.timestamp = genesis_timestamp
                    genesis_block.hash = genesis_block.calculate_hash()
                
                # Guardar el bloque génesis en la base de datos
                if db.connection_pool is not None:
                    db.save_block(genesis_block)
                    print(f"✓ Blockchain nueva creada con {len(genesis_transactions)} transacciones génesis")
                else:
                    print(f"⚠️  Advertencia: Base de datos no inicializada, bloque génesis no guardado")
        except Exception as e:
            print(f"Error inicializando blockchain: {e}")
            import traceback
            traceback.print_exc()
            self.blockchain = Blockchain(
                difficulty=settings.BLOCKCHAIN_DIFFICULTY,
                mining_reward=settings.BLOCKCHAIN_MINING_REWARD
            )
    
    def add_transaction(self, sender: str, recipient: str, amount: float) -> bool:
        try:
            from src.utils import parse_amount
            # amount puede venir como float (ej: 1.5) y se convierte a wei (entero)
            amount_wei = parse_amount(amount)
            transaction = Transaction(
                sender=sender,
                recipient=recipient,
                amount=amount_wei
            )
            self.blockchain.add_transaction(transaction)
            redis_client.cache_pending_transactions(self.blockchain.pending_transactions)
            rabbitmq_client.publish_transaction(transaction)
            return True
        except Exception as e:
            print(f"Error agregando transacción: {e}")
            return False
    
    def mine_pending_transactions(self, mining_reward_address: str = None, include_reward: bool = True) -> Optional[Block]:
        """
        Mina las transacciones pendientes
        - mining_reward_address: Dirección que recibe la recompensa (opcional)
        - include_reward: Si True, agrega recompensa de minería. Si False, mina sin recompensa
        """
        try:
            # Asegurar que tenemos las transacciones pendientes más recientes desde Redis
            try:
                if redis_client.client is None:
                    redis_client.initialize()
                pending_tx_data = redis_client.get_pending_transactions()
                if pending_tx_data:
                    from src.models import Transaction
                    from datetime import datetime
                    # Sincronizar transacciones pendientes desde Redis
                    self.blockchain.pending_transactions = []
                    for tx_dict in pending_tx_data:
                        tx = Transaction(
                            sender=tx_dict.get('sender', ''),
                            recipient=tx_dict.get('recipient', ''),
                            amount=int(tx_dict.get('amount', 0)),
                            timestamp=datetime.fromisoformat(tx_dict.get('timestamp', datetime.now().isoformat())) if isinstance(tx_dict.get('timestamp'), str) else tx_dict.get('timestamp', datetime.now())
                        )
                        self.blockchain.pending_transactions.append(tx)
            except Exception as e:
                print(f"⚠️  Advertencia al sincronizar transacciones pendientes: {e}")
            
            self.blockchain.mine_pending_transactions(mining_reward_address, include_reward=include_reward)
            latest_block = self.blockchain.get_latest_block()
            
            if db.save_block(latest_block):
                # Limpiar transacciones pendientes en Redis después de minar
                redis_client.cache_pending_transactions([])
                redis_client.cache_blockchain_state(
                    len(self.blockchain.chain),
                    latest_block.hash
                )
                rabbitmq_client.publish_block(latest_block)
                return latest_block
            return None
        except Exception as e:
            print(f"Error minando transacciones: {e}")
            return None
    
    def get_balance(self, address: str) -> int:
        """Retorna el balance en wei (entero sin decimales)"""
        # Asegurar que tenemos la cadena más reciente antes de calcular el balance
        self.get_chain()  # Recarga desde BD
        return self.blockchain.get_balance(address)
    
    def get_chain(self) -> List[Block]:
        # Recargar desde BD para asegurar que tenemos la versión más reciente
        try:
            blocks = db.get_all_blocks()
            if blocks:
                self.blockchain.chain = blocks
        except Exception as e:
            print(f"⚠️  Advertencia al recargar cadena desde BD: {e}")
        return self.blockchain.chain
    
    def get_pending_transactions(self) -> List[Transaction]:
        # SIEMPRE sincronizar con Redis antes de devolver (fuente de verdad)
        try:
            if redis_client.client is None:
                redis_client.initialize()
            pending_tx_data = redis_client.get_pending_transactions()
            
            # Limpiar y reconstruir desde Redis (fuente de verdad)
            self.blockchain.pending_transactions = []
            
            if pending_tx_data:
                from src.models import Transaction
                from datetime import datetime
                for tx_dict in pending_tx_data:
                    try:
                        tx = Transaction(
                            sender=tx_dict.get('sender', ''),
                            recipient=tx_dict.get('recipient', ''),
                            amount=int(tx_dict.get('amount', 0)),
                            timestamp=datetime.fromisoformat(tx_dict.get('timestamp', datetime.now().isoformat())) if isinstance(tx_dict.get('timestamp'), str) else tx_dict.get('timestamp', datetime.now())
                        )
                        self.blockchain.pending_transactions.append(tx)
                    except Exception as e:
                        print(f"⚠️  Error creando transacción desde Redis: {e}")
                        continue
        except Exception as e:
            print(f"⚠️  Advertencia al obtener transacciones pendientes desde Redis: {e}")
        return self.blockchain.pending_transactions
    
    def get_block_by_hash(self, hash: str) -> Optional[Block]:
        return db.get_block_by_hash(hash)
    
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict]:
        """Busca una transacción por su hash en toda la cadena"""
        chain = self.get_chain()
        for block in chain:
            for tx in block.transactions:
                if tx.calculate_hash() == tx_hash:
                    return {
                        'transaction': tx.to_dict(),
                        'block_index': block.index,
                        'block_hash': block.hash,
                        'block_timestamp': block.timestamp.isoformat()
                    }
        return None
    
    def is_chain_valid(self) -> bool:
        return self.blockchain.is_chain_valid()
    
    def get_chain_info(self) -> dict:
        # Sincronizar antes de devolver info
        chain = self.get_chain()  # Recarga desde BD
        pending = self.get_pending_transactions()  # Sincroniza desde Redis
        return {
            'length': len(chain),
            'difficulty': self.blockchain.difficulty,
            'mining_reward': self.blockchain.mining_reward,
            'pending_transactions': len(pending),
            'is_valid': self.is_chain_valid()
        }
    
    def get_financial_report(self) -> dict:
        """
        Genera un reporte financiero completo de la blockchain
        """
        from src.utils import format_amount, from_wei
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        chain = self.get_chain()  # Recargar desde BD
        
        # Estadísticas generales
        total_blocks = len(chain)
        total_transactions = sum(len(block.transactions) for block in chain)
        
        # Calcular volumen total transaccionado
        total_volume_wei = 0
        total_rewards_wei = 0
        unique_addresses = set()
        address_balances = defaultdict(int)
        transactions_by_day = defaultdict(int)
        volume_by_day = defaultdict(int)
        
        # Procesar todos los bloques
        for block in chain:
            block_date = block.timestamp.date() if isinstance(block.timestamp, datetime) else block.timestamp
            if isinstance(block_date, str):
                try:
                    block_date = datetime.fromisoformat(block_date).date()
                except:
                    block_date = datetime.now().date()
            
            for tx in block.transactions:
                # Contar direcciones únicas
                if tx.sender and tx.sender != "Sistema":
                    unique_addresses.add(tx.sender.lower())
                if tx.recipient:
                    unique_addresses.add(tx.recipient.lower())
                
                # Calcular volumen (solo transacciones entre direcciones, no recompensas)
                if tx.sender != "Sistema":
                    total_volume_wei += tx.amount
                    volume_by_day[block_date] += tx.amount
                else:
                    total_rewards_wei += tx.amount
                
                # Contar transacciones por día
                transactions_by_day[block_date] += 1
                
                # Calcular balances
                if tx.sender and tx.sender != "Sistema":
                    address_balances[tx.sender.lower()] -= tx.amount
                if tx.recipient:
                    address_balances[tx.recipient.lower()] += tx.amount
        
        # Top direcciones por balance
        top_addresses = sorted(
            [(addr, balance) for addr, balance in address_balances.items() if balance > 0],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Estadísticas de minería
        mining_rewards_count = sum(
            1 for block in chain
            for tx in block.transactions
            if tx.sender == "Sistema"
        )
        
        # Últimas transacciones (últimas 10)
        recent_transactions = []
        for block in reversed(chain[-5:]):  # Últimos 5 bloques
            for tx in block.transactions:
                recent_transactions.append({
                    'hash': tx.calculate_hash(),
                    'sender': tx.sender,
                    'recipient': tx.recipient,
                    'amount': tx.amount,
                    'amount_formatted': format_amount(tx.amount),
                    'block_index': block.index,
                    'timestamp': block.timestamp.isoformat() if isinstance(block.timestamp, datetime) else str(block.timestamp)
                })
                if len(recent_transactions) >= 10:
                    break
            if len(recent_transactions) >= 10:
                break
        
        # Estadísticas por período (últimos 7 días)
        last_7_days = []
        today = datetime.now().date()
        for i in range(7):
            date = today - timedelta(days=i)
            last_7_days.append({
                'date': date.isoformat(),
                'transactions': transactions_by_day.get(date, 0),
                'volume': volume_by_day.get(date, 0),
                'volume_formatted': format_amount(volume_by_day.get(date, 0))
            })
        
        return {
            'summary': {
                'total_blocks': total_blocks,
                'total_transactions': total_transactions,
                'total_volume_wei': total_volume_wei,
                'total_volume_formatted': format_amount(total_volume_wei),
                'total_rewards_wei': total_rewards_wei,
                'total_rewards_formatted': format_amount(total_rewards_wei),
                'unique_addresses': len(unique_addresses),
                'mining_rewards_count': mining_rewards_count,
                'average_transactions_per_block': round(total_transactions / total_blocks, 2) if total_blocks > 0 else 0
            },
            'top_addresses': [
                {
                    'address': addr,
                    'balance': balance,
                    'balance_formatted': format_amount(balance)
                }
                for addr, balance in top_addresses
            ],
            'recent_transactions': recent_transactions,
            'daily_statistics': last_7_days,
            'generated_at': datetime.now().isoformat()
        }


# Instancia global que se inicializará cuando se necesite
_blockchain_service_instance = None

def get_blockchain_service() -> BlockchainService:
    """Obtiene la instancia del servicio de blockchain, inicializándola si es necesario"""
    global _blockchain_service_instance
    if _blockchain_service_instance is None:
        _blockchain_service_instance = BlockchainService()
    return _blockchain_service_instance

# Para compatibilidad con el código existente, crear una instancia después de inicializar servicios
blockchain_service = None  # Se inicializará después de que los servicios estén listos

